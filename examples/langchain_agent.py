"""Example: LangChain agent that hires a human for a real-world task.

Requires:
    pip install rentahuman[langchain] langchain-openai

This creates a ReAct agent that can autonomously search for humans,
evaluate options, and hire someone — all through natural conversation.
"""

import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from rentahuman.integrations.langchain import RentAHumanToolkit

# ── Setup ─────────────────────────────────────────────────────

api_key = os.environ.get("RENTAHUMAN_API_KEY")
if not api_key:
    raise SystemExit("Set RENTAHUMAN_API_KEY environment variable. Get one at https://rentahuman.ai/dashboard?tab=api-keys")

toolkit = RentAHumanToolkit(api_key=api_key)
tools = toolkit.get_tools()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# ── Agent ─────────────────────────────────────────────────────

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

system_prompt = """You are an AI agent that hires humans for real-world tasks via rentahuman.ai.

When given a task:
1. Determine what skills are needed
2. Search for available humans with those skills
3. Evaluate candidates by rate, rating, and reviews
4. Either post a bounty (for non-urgent tasks) or start a conversation (for urgent tasks)
5. Report back with the outcome

Always check reviews before hiring. Prefer humans with higher ratings.
Be respectful in all communications — these are real people."""

messages = [
    ("system", system_prompt),
    ("human", "{input}"),
]

prompt = ChatPromptTemplate.from_messages(messages)

# ── Run ───────────────────────────────────────────────────────

if __name__ == "__main__":
    chain = prompt | llm_with_tools

    result = chain.invoke({
        "input": (
            "I need someone in San Francisco to pick up a package from "
            "456 Market Street and deliver it to 789 Mission Street. "
            "Budget: $60 max. Need it done by tomorrow."
        )
    })

    print(result.content)
    if result.tool_calls:
        for tc in result.tool_calls:
            print(f"\nTool call: {tc['name']}")
            print(f"  Args: {tc['args']}")
