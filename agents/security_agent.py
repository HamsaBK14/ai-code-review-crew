from crewai import Agent, LLM
from tools.security_tool import check_vulnerabilities, check_multiple_vulnerabilities
from tools.dependency_fetch_tool import fetch_requirements_file
import os
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

security_agent = Agent(
    role="Security Auditor",
    goal="Identify security vulnerabilities across ALL dependencies in the repository, not just one",
    backstory=(
        "You are a cybersecurity expert specializing in software supply chain security. "
        "You always start by fetching the repository's actual requirements.txt file to get "
        "the real, complete list of dependencies — you never guess or assume dependencies. "
        "Then you check ALL of them for known CVEs in one bulk check. You prioritize findings "
        "by severity and always explain the real-world risk of each issue."
    ),
    tools=[fetch_requirements_file, check_multiple_vulnerabilities],
    llm=llm,
    verbose=True,
    max_iter=4
)