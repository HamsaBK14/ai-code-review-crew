from crewai import Task, Crew
from agents.scanner_agent import scanner_agent
from agents.reviewer_agent import reviewer_agent
from agents.security_agent import security_agent
from agents.report_agent import report_agent
from agents.fix_agent import fix_agent
from tools.comment_tool import post_pr_comment
import os

# ==== CONFIGURATION — change these to scan a different PR ====
TARGET_REPO = "psf/requests"
TARGET_PR_NUMBER = 6606
# ================================================================

scan_task = Task(
    description=f"Fetch the pull request #{TARGET_PR_NUMBER} from the repo '{TARGET_REPO}'. Return the full list of changed files and their diffs.",
    expected_output="The PR title, description, and all changed files with their diffs.",
    agent=scanner_agent
)

review_task = Task(
    description=(
        "Using the PR diff data gathered by the Scanner, review the code changes for bugs, "
        "bad practices, poor style, or logic errors. For each issue found, mention the filename, "
        "what the issue is, and why it matters. If a file looks fine, say so briefly."
    ),
    expected_output="A structured list of code review findings, organized by file, with severity (Low/Medium/High) for each issue.",
    agent=reviewer_agent,
    context=[scan_task]
)

security_task = Task(
    description=(
        f"First, use the Requirements File Fetcher tool to get the REAL list of dependencies "
        f"from the repo '{TARGET_REPO}'. Then use the Bulk Dependency Vulnerability Checker tool "
        f"ONCE with that comma-separated list to check ALL dependencies at once. "
        f"After getting results, write your final answer with these 4 sections:\n\n"
        "1. Dependencies Checked: (list all packages found)\n"
        "2. Vulnerabilities Found: (summarize per package, briefly)\n"
        "3. Relevance to this PR: (yes/no and why, based on your own judgment)\n"
        "4. Overall Risk Level: (Low/Medium/High) with justification\n\n"
        "If no requirements.txt exists, say so clearly instead of guessing dependencies."
    ),
    expected_output="A structured 4-section security assessment based on the repo's actual dependency file.",
    agent=security_agent,
    context=[scan_task]
)

fix_task = Task(
    description=(
        "Using the code review findings and security assessment, propose concrete fixes for the "
        "top 2-3 most important issues (prioritize High and Medium severity items). For each fix, "
        "show a brief 'before' snippet and an 'after' snippet, plus a one-line explanation. "
        "If an issue doesn't have a clear code-level fix (e.g. it needs a team discussion), say so "
        "instead of forcing a fake fix."
    ),
    expected_output="2-3 concrete fix suggestions with before/after code snippets, or a note that no simple fix applies.",
    agent=fix_agent,
    context=[review_task, security_task]
)

report_task = Task(
    description=(
        "Combine the code review findings, security assessment, and suggested fixes into one final report. "
        "Structure it as:\n\n"
        "## PR Summary\n(1-2 sentences on what this PR does)\n\n"
        "## Critical Issues (High severity items from either review)\n\n"
        "## Other Findings (Medium/Low severity items)\n\n"
        "## Suggested Fixes\n(include the before/after snippets provided)\n\n"
        "## Security Assessment Summary\n\n"
        "## Recommendation (Approve / Request Changes / Needs Discussion, with reasoning)"
    ),
    expected_output="A complete, well-formatted final report combining all findings and fixes, following the structure given.",
    agent=report_agent,
    context=[review_task, security_task, fix_task]
)

crew = Crew(
    agents=[scanner_agent, reviewer_agent, security_agent, fix_agent, report_agent],
    tasks=[scan_task, review_task, security_task, fix_task, report_task],
    verbose=True,
    max_rpm=2
)

result = crew.kickoff()
print("\n\n=== FINAL RESULT ===")
print(result)

# Post the report (dry run by default — safe testing)
dry_run_mode = os.getenv("DRY_RUN", "True") == "True"

post_result = post_pr_comment(
    repo_name=TARGET_REPO,
    pr_number=TARGET_PR_NUMBER,
    comment_body=str(result),
    dry_run=dry_run_mode
)
print(post_result)