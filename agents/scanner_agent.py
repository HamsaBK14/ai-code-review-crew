from crewai import Agent, LLM
from tools.github_tool import get_pr_diff
import os
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)

scanner_agent = Agent(
    role="Code Scanner",
    goal="Fetch and summarize the changes made in a given GitHub pull request",
    backstory=(
        "You are an expert at quickly understanding what changed in a codebase by analyzing "
        "pull request diffs. You always respond in clear, readable plain text — never JSON, "
        "never code blocks wrapping your entire answer. Just return the tool's output as-is."
    ),
    tools=[get_pr_diff],
    llm=llm,
    verbose=True
)