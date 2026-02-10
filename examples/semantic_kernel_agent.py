"""Semantic Kernel agent using rentahuman.ai tools.

Usage:
    pip install rentahuman[semantic-kernel]
    export RENTAHUMAN_API_KEY=rah_your_key
    export OPENAI_API_KEY=sk-...
    python examples/semantic_kernel_agent.py
"""

import asyncio
import os
import sys

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory

from rentahuman.integrations.semantic_kernel import RentAHumanPlugin

api_key = os.environ.get("RENTAHUMAN_API_KEY")
if not api_key:
    print("Set RENTAHUMAN_API_KEY environment variable.")
    print("Get one at: https://rentahuman.ai/dashboard?tab=api-keys")
    sys.exit(1)


async def main():
    # Set up kernel
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="chat"))

    # Add rentahuman plugin
    plugin = RentAHumanPlugin(api_key=api_key)
    kernel.add_plugin(plugin, "rentahuman")

    # Configure auto function calling
    settings = OpenAIChatPromptExecutionSettings(
        service_id="chat",
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )

    # Chat
    history = ChatHistory()
    history.add_system_message(
        "You are a task coordinator. Use the rentahuman plugin to find "
        "and hire humans for physical-world tasks. Always search for "
        "available humans before creating bookings or bounties."
    )

    history.add_user_message(
        "Find me a photographer in San Francisco under $60/hr"
    )

    result = await kernel.invoke_prompt(
        prompt="{{$chat_history}}",
        settings=settings,
        chat_history=history,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
