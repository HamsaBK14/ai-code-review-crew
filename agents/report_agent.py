from crewai import Agent, LLM
import os
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="groq/llama-3.3-70b-versatile",  # switched from 8b-instant
    api_key=os.getenv("GROQ_API_KEY")
)

report_agent = Agent(
    role="Report Generator",
    goal="Synthesize code review and security findings into one clear, prioritized report",
    backstory=(
        "You are a technical lead who writes clear, concise summary reports for engineering teams. "
        "You take findings from multiple reviewers and combine them into a single report that a "
        "developer can act on quickly. You prioritize the most critical issues first."
    ),
    llm=llm,
    verbose=True,
    max_iter=3
)