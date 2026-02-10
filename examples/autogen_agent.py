"""Example: AutoGen agent that hires humans via rentahuman.ai.

Requires:
    pip install rentahuman[autogen] autogen-agentchat autogen-ext[openai]

Creates an AssistantAgent with rentahuman tools that can autonomously
search for and hire humans for real-world tasks.
"""

import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from rentahuman.integrations.autogen import get_rentahuman_tools

# ── Setup ─────────────────────────────────────────────────────

api_key = os.environ.get("RENTAHUMAN_API_KEY")
if not api_key:
    raise SystemExit(
        "Set RENTAHUMAN_API_KEY environment variable. "
        "Get one at https://rentahuman.ai/dashboard?tab=api-keys"
    )

tools = get_rentahuman_tools(api_key=api_key)

model_client = OpenAIChatCompletionClient(model="gpt-4o")

# ── Agent ─────────────────────────────────────────────────────

agent = AssistantAgent(
    "task_coordinator",
    model_client=model_client,
    tools=tools,
    system_message=(
        "You are an AI agent that hires humans for real-world tasks via rentahuman.ai. "
        "Search for available humans, evaluate candidates, and either book directly "
        "or post bounties. Always check reviews before hiring. Be respectful — these are real people."
    ),
)

# ── Run ───────────────────────────────────────────────────────


async def main():
    response = await agent.run(
        task=(
            "I need someone in New York to photograph a storefront at 123 Broadway. "
            "Budget: $50. Find candidates and post a bounty if good options exist."
        )
    )
    await Console(response)


if __name__ == "__main__":
    asyncio.run(main())
