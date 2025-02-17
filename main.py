import gitlab
from github import Github, Auth
import os
import subprocess
import re

# Replace these with your GitLab and GitHub tokens
GITLAB_TOKEN = "your_gitlab_token"  # GitLab personal access token
GITHUB_TOKEN = "your_github_token"  # GitHub personal access token

# GitHub user and organization name
GITHUB_USER = "your_github_name"
GITHUB_ORG = "your_github_organization"

# Initialize GitLab and GitHub clients
gitlab_client = gitlab.Gitlab("https://gitlab.com", private_token=GITLAB_TOKEN)

auth = Auth.Login(GITHUB_USER, GITHUB_TOKEN)
github_client = Github(auth=auth)
github_org = github_client.get_organization(GITHUB_ORG)


def kebab_case(s):
    """
    Convert a string to kebab case.
    """
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def construct_repo_name(group_hierarchy, project_name):
    """
    Construct the repository name by joining the group hierarchy and project name in kebab case.
    """
    parts = [kebab_case(group.name) for group in group_hierarchy]
    parts.append(kebab_case(project_name))
    return "-".join(parts)


def get_all_gitlab_projects(group_id, group_hierarchy=None):
    """
    Recursively fetch all repositories (projects) under a GitLab group and its subgroups.
    Pass the hierarchy of groups to build the full path of each project.
    """
    if group_hierarchy is None:
        group_hierarchy = []

    projects = []
    try:
        group = gitlab_client.groups.get(group_id)
        group_hierarchy.append(group)

        # Add all projects directly under this group
        for project in group.projects.list(all=True):
            projects.append((project, list(group_hierarchy)))

        # Fetch subgroups and recursively get their projects
        subgroups = group.subgroups.list(all=True)
        for subgroup in subgroups:
            projects.extend(get_all_gitlab_projects(subgroup.id, group_hierarchy))

        # Remove the group from the hierarchy after processing
        group_hierarchy.pop()

    except gitlab.exceptions.GitlabGetError as e:
        print(f"Error fetching group {group_id}: {e}")
    return projects


def create_github_repo(repo_name, description):
    """
    Create a new repository in the GitHub organization.
    """
    try:
        github_org.create_repo(name=repo_name, description=description, private=True)
    except Exception as e:
        # GitLab support more symbol than GitHub, just pass empty string in case facing error and run again
        if (description != ""):
          create_github_repo(repo_name, "")
        else:
          print(f"Error creating GitHub repository {repo_name}: {e}")


def migrate_repository(gitlab_project, github_repo_name):
    """
    Migrate a single repository from GitLab to GitHub.
    """
    gitlab_repo_url = gitlab_project.ssh_url_to_repo
    description = gitlab_project.description
    github_repo_url = f"git@github.com:{GITHUB_ORG}/{github_repo_name}.git"

    try:
        # Create the repository on GitHub
        print(f"Creating GitHub repository: {github_repo_name}")
        create_github_repo(github_repo_name, description)

        # Use `git` commands to handle migration (requires Git installed locally)
        print(f"Cloning GitLab repository: {gitlab_repo_url}")
        subprocess.run(
            ["git", "clone", "--mirror", gitlab_repo_url, github_repo_name], check=True
        )

        # Push the cloned repository to GitHub
        os.chdir(github_repo_name)
        subprocess.run(["git", "remote", "add", "github", github_repo_url], check=True)
        print(f"Pushing to GitHub repository: {github_repo_url}")
        subprocess.run(["git", "push", "--mirror", "github"], check=True)

        # Clean up (delete the local mirror repository)
        os.chdir("..")
        subprocess.run(["rm", "-rf", github_repo_name], check=True)

    except Exception as e:
        print(f"Error migrating repository {github_repo_name}: {e}")


def main():
    """
    Main function to handle the migration of repositories from multiple GitLab groups.
    """
    try:
        groups = gitlab_client.groups.list(get_all=True, top_level_only=True)

        for group in groups:
            group_name = group.name
            group_id = group.id
            print(f"Fetching repositories under GitLab group '{group_name}': {group_id}")

            gitlab_projects = get_all_gitlab_projects(group_id)
            print(f"Found {len(gitlab_projects)} repositories in group '{group_name}'")

            for project, group_hierarchy in gitlab_projects:
                # Construct the GitHub repository name with max length 100 charters
                github_repo_name = construct_repo_name(group_hierarchy, project.name)[:100]

                print(f"Migrating repository: {project.name} as {github_repo_name}")
                migrate_repository(project, github_repo_name)
                print(f"Successfully migrated {project.name} as {github_repo_name}")

    except Exception as e:
        print(f"Error during migration: {e}")


if __name__ == "__main__":
    main()
