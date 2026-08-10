# 🤖 AI Crew for Automated Code Review & Security Triage

A multi-agent AI system that autonomously reviews GitHub pull requests — analyzing code quality, auditing real dependencies against a live vulnerability database, suggesting concrete fixes, and generating a unified, actionable report. Built with [CrewAI](https://github.com/joaomdmoura/crewAI) and powered by free, open-source LLMs via [Groq](https://groq.com).

---

## Table of Contents

- [What It Does](#what-it-does)
- [Why This Project](#why-this-project)
- [Architecture](#architecture)
- [The 5 Agents](#the-5-agents)
- [Tech Stack](#tech-stack)
- [Setup](#setup)
- [Usage](#usage)
- [Example Output](#example-output)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [Future Work](#future-work)
- [Safety Notes](#safety-notes)

---

## What It Does

Point this system at any public GitHub pull request, and five specialized AI agents collaborate — reasoning, calling tools, and handing off findings to each other — to produce a complete, human-readable review:

1. **Scans** the PR to understand exactly what changed
2. **Reviews** the code for bugs, bad practices, and quality issues
3. **Audits security** by fetching the repository's real dependencies and checking each one against a live CVE database
4. **Suggests concrete fixes** with before/after code snippets for the most important issues
5. **Generates a final report** that synthesizes everything into one prioritized, readable document — which can optionally be posted directly as a comment on the PR

This isn't a single AI model answering a prompt — it's a team of agents, each with a distinct role, reasoning independently and building on each other's work.

---

## Why This Project

Most "AI code review" tools are a single LLM call wrapped in a nice UI. This project instead explores **agentic AI** — autonomous agents that plan, use tools, and collaborate — combined with **software supply chain security**, applied to a genuinely useful real-world workflow.

It's built to demonstrate:
- Multi-agent orchestration and structured task hand-offs (not just sequential prompting)
- Real tool integration (GitHub API, OSV.dev vulnerability database, TOML parsing)
- Practical, deployable output (an actual PR comment, not just a chat response)
- Honest engineering trade-offs (documented limitations below, not overclaiming)

---

## Architecture

```
                        GitHub PR Link (repo + PR number)
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │    Scanner Agent      │
                        │  (fetches PR diff via │
                        │     GitHub API)       │
                        └───────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                                ▼
        ┌───────────────────────┐      ┌────────────────────────────┐
        │   Reviewer Agent      │      │   Security Auditor Agent    │
        │ (analyzes code for    │      │ (fetches real dependencies, │
        │  bugs & bad practices)│      │  checks OSV.dev for CVEs)   │
        └───────────┬───────────┘      └──────────────┬───────────────┘
                    │                                  │
                    └───────────────┬──────────────────┘
                                    ▼
                        ┌───────────────────────┐
                        │   Fix Suggester Agent │
                        │ (proposes concrete    │
                        │  before/after fixes)  │
                        └───────────┬───────────┘
                                    ▼
                        ┌───────────────────────┐
                        │  Report Generator     │
                        │  Agent (synthesizes   │
                        │  everything into one  │
                        │  final report)        │
                        └───────────┬───────────┘
                                    ▼
                    Final Report (printed, or optionally
                       posted as a real PR comment)
```

**Key design principle:** each agent only receives what it needs via CrewAI's `context=[]` mechanism — the Reviewer and Security Auditor both read the Scanner's output independently, and the Report Generator reads from *both* of them. This structured hand-off (not just concatenating prompts) is what makes this a genuine multi-agent system rather than a single long prompt.

---

## The 5 Agents

| Agent | Role | Tools Used | Output |
|---|---|---|---|
| **Scanner** | Fetches the PR's changed files and diffs | GitHub PR Fetcher (GitHub API) | Structured diff data |
| **Reviewer** | Analyzes code quality, bugs, style issues | — (pure LLM reasoning over the diff) | Severity-rated findings list |
| **Security Auditor** | Audits real dependencies for known CVEs | Requirements File Fetcher, Bulk Dependency Vulnerability Checker (OSV.dev) | 4-section risk assessment |
| **Fix Suggester** | Proposes concrete code fixes | — (reasons over Reviewer + Security findings) | Before/after code snippets |
| **Report Generator** | Synthesizes all findings into one report | — (reasons over all prior agent outputs) | Final structured report |

---

## Tech Stack

- **Orchestration:** [CrewAI](https://github.com/joaomdmoura/crewAI) `0.126.0`
- **LLM:** [Groq](https://groq.com) (free tier) — `llama-3.3-70b-versatile` and `llama-3.1-8b-instant`
- **LLM Routing:** LiteLLM (via CrewAI)
- **GitHub Integration:** [PyGithub](https://pygithub.readthedocs.io/)
- **Vulnerability Data:** [OSV.dev](https://osv.dev) API (Open Source Vulnerabilities database)
- **Dependency Parsing:** Python's built-in `tomllib` (structural `pyproject.toml` parsing, supports PEP 621 and Poetry formats) + custom `requirements.txt` parser
- **Language:** Python 3.12
- **Environment Management:** `venv` + `python-dotenv`

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/HamsaBK14/ai-code-review-crew.git
cd ai-code-review-crew
```

### 2. Create a virtual environment
```bash
python3.12 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Get free API keys

**Groq API key** (free, no credit card required):
1. Sign up at [console.groq.com](https://console.groq.com)
2. Go to **API Keys** → **Create API Key**
3. Copy the key (starts with `gsk_...`)

**GitHub Personal Access Token:**
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. **Generate new token (classic)**
3. Check the `repo` scope
4. Copy the token (starts with `ghp_...`)

### 5. Configure environment variables

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_key_here
GITHUB_TOKEN=your_github_token_here
DRY_RUN=True
```

> **No spaces around the `=` sign** — this will break `.env` loading.

---

## Usage

### 1. Set the target PR

Open `main.py` and edit the configuration block near the top:
```python
TARGET_REPO = "owner/repo-name"
TARGET_PR_NUMBER = 1234
```

### 2. Run the pipeline
```bash
python main.py
```

You'll see live, verbose output as each agent reasons, calls tools, and produces its findings — followed by the final synthesized report.

### 3. (Optional) Post the report as a real PR comment

By default, `DRY_RUN=True` means the system only *prints* what it would post — nothing is sent to GitHub. This is intentional and safe.

To actually post a comment, only do this on a **repository you own**:
1. Set `DRY_RUN=False` in `.env`
2. Point `TARGET_REPO` / `TARGET_PR_NUMBER` at your own repo/PR
3. Run `python main.py` again

The system also checks for existing report comments before posting, to avoid duplicates.

---

## Example Output

```markdown
## PR Summary
This PR updates HTTP status code definitions and modifies documentation
hyperlinks to improve accuracy and usability.

## Critical Issues
- High: New enumeration value added without validation in
  src/requests/status_codes.py

## Other Findings
- Low: Minor formatting inconsistencies in documentation links
- Medium: New status code lacks accompanying test coverage

## Suggested Fixes
1. Validate new enum values before insertion
   Before: `508: ("loop_detected",)`
   After:  `if validate_status_code(508): status_codes[508] = ("loop_detected",)`

## Security Assessment Summary
Checked 4 real dependencies (certifi, charset_normalizer, idna, urllib3)
against OSV.dev. urllib3 has 38 known vulnerabilities; not introduced by
this PR but worth tracking.

## Recommendation
Request Changes — address the validation issue and consider dependency
updates in a follow-up.
```

---

## Project Structure

```
ai-code-review-crew/
├── agents/
│   ├── scanner_agent.py        # Agent 1: fetches PR data
│   ├── reviewer_agent.py       # Agent 2: code quality review
│   ├── security_agent.py       # Agent 3: dependency vulnerability audit
│   ├── fix_agent.py            # Agent 4: proposes concrete fixes
│   └── report_agent.py         # Agent 5: synthesizes final report
├── tools/
│   ├── github_tool.py          # Fetches PR diffs via GitHub API
│   ├── security_tool.py        # Queries OSV.dev for CVEs
│   ├── dependency_fetch_tool.py# Parses requirements.txt / pyproject.toml
│   └── comment_tool.py         # Posts (or dry-runs) PR comments
├── main.py                     # Orchestrates the full crew pipeline
├── requirements.txt            # Python dependencies
├── .env                        # API keys (not committed — see .gitignore)
├── .gitignore
└── README.md
```

---

## Known Limitations

Documented honestly, not hidden:

- **Free-tier LLM accuracy:** uses Groq's free `llama-3.3-70b` / `llama-3.1-8b` models, which are meaningfully less accurate than GPT-4-class models — occasional hallucinated or overstated findings, especially in the Fix Suggester.
- **Truncated diffs:** individual file diffs are capped (~900 characters) to stay within free-tier token limits, so very large PRs are only partially analyzed.
- **Dependency parsing coverage:** `pyproject.toml` parsing supports standard PEP 621 and Poetry dependency formats via Python's `tomllib`, but not every possible packaging format (e.g. Pipenv, Conda).
- **Sequential execution:** agents run one after another due to free-tier rate limits (`max_rpm=2`), making a full run take 2-5 minutes. A production version would parallelize independent agents (Reviewer and Security Auditor don't depend on each other).
- **No static analysis grounding:** the Reviewer agent relies purely on LLM reasoning over the diff, not a real static analysis tool like pylint — this is a known source of occasional false positives.

---

## Future Work

- Integrate a real static analysis tool (pylint/bandit) as a callable tool to ground Reviewer findings
- Parallelize independent agent calls to reduce total runtime
- Add support for more dependency file formats (Pipenv, Conda, npm's package.json for JS repos)
- Build a Streamlit UI for live, interactive demos
- Add caching to avoid re-scanning previously analyzed PRs

---

## Safety Notes

- `DRY_RUN=True` by default — no PR comments are posted without explicit opt-in.
- API keys are loaded exclusively from `.env`, which is excluded via `.gitignore` and never committed.
- The comment-posting tool checks for existing report comments before posting, to avoid duplicate spam.
- This tool should only be used to post comments on repositories you own or have explicit permission to comment on — never on third-party public repositories without consent.

---

## License

This project is for educational and portfolio purposes.