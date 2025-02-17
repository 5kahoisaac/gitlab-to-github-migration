# GitLab to GitHub Repository Migration Script

## How the Program Works

### GitLab Setup:
- The `gitlab` client is initialized using the `python-gitlab` SDK with a personal access token.
- The `get_all_gitlab_projects` function recursively fetches all repositories under a specified GitLab group and its subgroups.

### GitHub Setup:
- The `github` client is initialized using the `PyGithub` SDK with a personal access token.
- The `create_github_repo` function creates a new private repository in the specified GitHub organization.
- The `kebab_case` function converts strings to kebab case for the new private repository naming.


### Repository Migration:
The `migrate_repository` function handles the repository migration using the following steps:
1. Clones the GitLab repository using the `git clone --mirror` command.
2. Creates a corresponding repository on GitHub.
3. Pushes the mirrored repository to GitHub using the `git push --mirror` command.
4. Cleans up by deleting the local mirror repository.

### Main Function:
- Iterates over the list of GitLab groups, fetches all repositories in each group and its subgroups, and migrates them to GitHub.

---

## Prerequisites
1. Before using the program, ensure that SSH is properly set up for both GitLab and GitHub by adding your SSH keys to your accounts for seamless repository cloning and pushing.
2. Make sure to install the required SDKs: `pip install python-gitlab PyGithub`.
3. Replace placeholders like `your_gitlab_token`, `your_github_token`, `your_github_name` and `your_github_organization` with actual values.
4. Ensure `git` is installed and available in your system's PATH.

---

## Notes
- The program assumes repositories are private by default. You can modify the `create_github_repo` function to make them public if needed.
- Ensure proper permissions for your GitLab and GitHub tokens to access and manage repositories.
- The program does not handle the large file issue in GitHub where files exceeding 100MB are not allowed. Please address this issue manually if you encounter such errors.