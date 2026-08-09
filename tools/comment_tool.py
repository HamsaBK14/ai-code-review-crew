from github import Github, Auth
import os
from dotenv import load_dotenv

load_dotenv()

def post_pr_comment(repo_name: str, pr_number: int, comment_body: str, dry_run: bool = True):
    """
    Posts a comment on a GitHub PR. If dry_run=True, only prints what WOULD be posted.
    Checks for existing bot comments to avoid duplicates.
    """
    if dry_run:
        print("\n" + "="*60)
        print("DRY RUN MODE — comment NOT actually posted.")
        print("This is what WOULD be posted:")
        print("="*60)
        print(comment_body)
        print("="*60 + "\n")
        return "Dry run complete — no comment posted."

    token = os.getenv("GITHUB_TOKEN")
    auth = Auth.Token(token)
    g = Github(auth=auth)

    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Check for existing comments to avoid duplicate posting
    existing_comments = pr.get_issue_comments()
    for comment in existing_comments:
        if "## PR Summary" in comment.body:  # our report's signature header
            return f"A report comment already exists on this PR (comment id {comment.id}). Skipping duplicate post."

    pr.create_issue_comment(comment_body)
    return f"Comment posted successfully on {repo_name} PR #{pr_number}."