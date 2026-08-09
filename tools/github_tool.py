from github import Github, Auth
from crewai.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

@tool("GitHub PR Fetcher")
def get_pr_diff(repo_name: str, pr_number: int) -> str:
    """
    Fetches the diff (changed files + code changes) from a GitHub PR.
    repo_name format: 'owner/repo' e.g. 'facebook/react'
    pr_number: the pull request number (integer)
    Returns a text summary of the PR title, description, and changed files with their diffs.
    """
    token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(token)
    g = Github(auth=auth)

    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    output = f"PR Title: {pr.title}\n"
    output += f"PR Description: {pr.body}\n\n"
    output += "Changed Files:\n"

    for file in pr.get_files():
        output += f"\n--- {file.filename} ({file.status}) ---\n"
        output += f"+{file.additions} -{file.deletions}\n"
        if file.patch:
            output += f"Diff:\n{file.patch[:900]}\n" # reduced from 1500 to 900

    return output