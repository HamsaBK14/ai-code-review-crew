import streamlit as st
import os
from dotenv import load_dotenv
from crewai import Task, Crew

from agents.scanner_agent import scanner_agent
from agents.reviewer_agent import reviewer_agent
from agents.security_agent import security_agent
from agents.fix_agent import fix_agent
from agents.report_agent import report_agent
from tools.comment_tool import post_pr_comment

load_dotenv()

st.set_page_config(page_title="AI Code Review Crew", page_icon="🤖", layout="wide")

st.title("🤖 AI Crew for Automated Code Review & Security Triage")
st.markdown("Multi-agent AI system that reviews GitHub pull requests — code quality, security, and fix suggestions, all in one pass.")

st.divider()

# ==== Input form ====
col1, col2 = st.columns([3, 1])
with col1:
    repo_input = st.text_input("Repository (owner/repo)", placeholder="e.g. psf/requests")
with col2:
    pr_input = st.number_input("PR Number", min_value=1, step=1, value=1)

run_button = st.button("🚀 Run Review", type="primary")

st.divider()

# ==== Run the crew when button is clicked ====
if run_button:
    if not repo_input:
        st.error("Please enter a repository name.")
    else:
        with st.status("Running multi-agent review pipeline...", expanded=True) as status:

            st.write("🔍 **Scanner Agent** — fetching PR data...")
            scan_task = Task(
                description=f"Fetch the pull request #{pr_input} from the repo '{repo_input}'. Return the full list of changed files and their diffs.",
                expected_output="The PR title, description, and all changed files with their diffs.",
                agent=scanner_agent
            )

            st.write("🕵️ **Reviewer Agent** — analyzing code quality...")
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

            st.write("🔐 **Security Auditor Agent** — checking dependencies for CVEs...")
            security_task = Task(
                description=(
                    f"First, use the Requirements File Fetcher tool to get the REAL list of dependencies "
                    f"from the repo '{repo_input}'. Then use the Bulk Dependency Vulnerability Checker tool "
                    f"ONCE with that comma-separated list to check ALL dependencies at once. "
                    f"After getting results, write your final answer with these 4 sections:\n\n"
                    "1. Dependencies Checked: (list all packages found)\n"
                    "2. Vulnerabilities Found: (summarize per package, briefly)\n"
                    "3. Relevance to this PR: (yes/no and why, based on your own judgment)\n"
                    "4. Overall Risk Level: (Low/Medium/High) with justification\n\n"
                    "If no dependency file exists, say so clearly instead of guessing dependencies."
                ),
                expected_output="A structured 4-section security assessment based on the repo's actual dependency file.",
                agent=security_agent,
                context=[scan_task]
            )

            st.write("🛠️ **Fix Suggester Agent** — drafting concrete fixes...")
            fix_task = Task(
                description=(
                    "Using the code review findings and security assessment, propose concrete fixes for the "
                    "top 2-3 most important issues (prioritize High and Medium severity items). For each fix, "
                    "show a brief 'before' snippet and an 'after' snippet, plus a one-line explanation. "
                    "If an issue doesn't have a clear code-level fix, say so instead of forcing a fake fix."
                ),
                expected_output="2-3 concrete fix suggestions with before/after code snippets, or a note that no simple fix applies.",
                agent=fix_agent,
                context=[review_task, security_task]
            )

            st.write("📝 **Report Generator Agent** — synthesizing final report...")
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
                verbose=False,
                max_rpm=2
            )

            result = crew.kickoff()

            status.update(label="✅ Review complete!", state="complete", expanded=False)

        st.divider()
        st.subheader("📋 Final Report")
        st.markdown(str(result))

        # Optional: dry-run posting preview
        st.divider()
        with st.expander("🔎 Preview: what would be posted as a PR comment"):
            dry_run_mode = os.getenv("DRY_RUN", "True") == "True"
            post_result = post_pr_comment(
                repo_name=repo_input,
                pr_number=int(pr_input),
                comment_body=str(result),
                dry_run=dry_run_mode
            )
            st.info(post_result)