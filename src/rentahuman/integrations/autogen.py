"""AutoGen integration for rentahuman.ai.

Provides callable tool functions compatible with AutoGen's FunctionTool pattern.
Each function has full type hints and docstrings so AutoGen can auto-generate
the JSON schema for LLM tool calling.

Usage:
    pip install rentahuman[autogen]

    from rentahuman.integrations.autogen import get_rentahuman_tools

    tools = get_rentahuman_tools(api_key="rah_...")
    # Pass to AssistantAgent
    agent = AssistantAgent("helper", model_client=..., tools=tools)
"""

from __future__ import annotations

from typing import Annotated

from rentahuman.client import RentAHumanClient
from rentahuman.models import BookingCreate, BountyCreate

try:
    from autogen_core.tools import FunctionTool
except ImportError:
    raise ImportError(
        "AutoGen integration requires autogen-core. "
        "Install with: pip install rentahuman[autogen]"
    )


def _make_tools(client: RentAHumanClient) -> list[FunctionTool]:
    """Create AutoGen FunctionTool instances wrapping the rentahuman client."""

    def search_humans(
        skill: Annotated[str | None, "Skill to filter by (e.g. 'Photography', 'Packages')"] = None,
        max_rate: Annotated[float | None, "Maximum hourly rate in USD"] = None,
        limit: Annotated[int, "Max results (1-500)"] = 10,
    ) -> str:
        """Search for humans available for hire on rentahuman.ai by skill, rate, or name."""
        humans = client.search_humans(skill=skill, max_rate=max_rate, limit=limit)
        if not humans:
            return "No humans found matching your criteria."
        lines = [f"Found {len(humans)} human(s):"]
        for h in humans:
            lines.append(f"  - {h.summary()}")
        return "\n".join(lines)

    def get_human_profile(
        human_id: Annotated[str, "The human's ID"],
    ) -> str:
        """Get full profile for a specific human on rentahuman.ai."""
        h = client.get_human(human_id)
        parts = [f"Name: {h.name}", f"ID: {h.id}"]
        if h.location:
            parts.append(f"Location: {h.location}")
        if h.rate:
            parts.append(f"Rate: ${h.rate}/hr")
        if h.skills:
            parts.append(f"Skills: {', '.join(h.skills)}")
        if h.rating:
            parts.append(f"Rating: {h.rating:.1f}")
        return "\n".join(parts)

    def list_skills() -> str:
        """List all available skills that humans offer on rentahuman.ai."""
        skills = client.list_skills()
        if not skills:
            return "No skills found."
        return "Available skills: " + ", ".join(s.name for s in skills)

    def create_booking(
        human_id: Annotated[str, "ID of the human to book"],
        task_title: Annotated[str, "Brief title of the task"],
        start_time: Annotated[str, "ISO 8601 datetime for task start"],
        estimated_hours: Annotated[float, "Estimated duration in hours"],
        description: Annotated[str | None, "Detailed task description"] = None,
    ) -> str:
        """Create a booking to hire a human for a task on rentahuman.ai."""
        booking = client.create_booking(BookingCreate(
            humanId=human_id,
            taskTitle=task_title,
            startTime=start_time,
            estimatedHours=estimated_hours,
            description=description,
        ))
        return f"Booking created! ID: {booking.id} | Status: {booking.status} | Task: {booking.task_title}"

    def create_bounty(
        title: Annotated[str, "Task title"],
        description: Annotated[str, "Detailed description of what needs to be done"],
        price: Annotated[float, "Fixed price in USD"],
        estimated_hours: Annotated[float | None, "Estimated hours"] = None,
        location: Annotated[str | None, "Required location"] = None,
    ) -> str:
        """Post a task bounty on rentahuman.ai for humans to apply to."""
        bounty = client.create_bounty(BountyCreate(
            title=title,
            description=description,
            price=price,
            estimatedHours=estimated_hours,
            location=location,
        ))
        return f"Bounty posted! ID: {bounty.id} | Title: {bounty.title} | Price: ${bounty.price}"

    def get_bounty_applications(
        bounty_id: Annotated[str, "The bounty ID"],
    ) -> str:
        """View applications from humans for a bounty."""
        apps = client.get_bounty_applications(bounty_id)
        if not apps:
            return "No applications yet."
        lines = [f"{len(apps)} application(s):"]
        for a in apps:
            msg = a.message[:80] + "..." if len(a.message) > 80 else a.message
            lines.append(f"  - {a.human_name} ({a.human_id}): ${a.rate}/hr | {msg}")
        return "\n".join(lines)

    def accept_application(
        bounty_id: Annotated[str, "The bounty ID"],
        application_id: Annotated[str, "The application ID to accept"],
    ) -> str:
        """Accept a bounty application, hiring the human for the task."""
        result = client.accept_application(bounty_id, application_id)
        return f"Application accepted! {result.get('message', 'Human has been hired.')}"

    def start_conversation(
        human_id: Annotated[str, "ID of the human to message"],
        subject: Annotated[str, "Conversation subject line"],
        message: Annotated[str, "Opening message"],
    ) -> str:
        """Start a direct conversation with a human on rentahuman.ai."""
        convo = client.start_conversation(
            human_id=human_id, subject=subject, message=message,
        )
        return f"Conversation started! ID: {convo.id} | Subject: {convo.subject}"

    def send_message(
        conversation_id: Annotated[str, "The conversation ID"],
        message: Annotated[str, "Message content"],
    ) -> str:
        """Send a message in an existing conversation with a human."""
        msg = client.send_message(conversation_id, message)
        return f"Message sent (ID: {msg.id})"

    return [
        FunctionTool(search_humans, description="Search for humans on rentahuman.ai by skill, rate, or name"),
        FunctionTool(get_human_profile, description="Get a human's full profile on rentahuman.ai"),
        FunctionTool(list_skills, description="List all available skills on rentahuman.ai"),
        FunctionTool(create_booking, description="Book a human for a task on rentahuman.ai"),
        FunctionTool(create_bounty, description="Post a task bounty on rentahuman.ai"),
        FunctionTool(get_bounty_applications, description="View applications for a bounty on rentahuman.ai"),
        FunctionTool(accept_application, description="Accept a bounty application on rentahuman.ai"),
        FunctionTool(start_conversation, description="Start a conversation with a human on rentahuman.ai"),
        FunctionTool(send_message, description="Send a message in a conversation on rentahuman.ai"),
    ]


def get_rentahuman_tools(
    api_key: str | None = None,
    base_url: str = "https://rentahuman.ai/api",
) -> list[FunctionTool]:
    """Get all rentahuman tools for AutoGen agents.

    Usage:
        from rentahuman.integrations.autogen import get_rentahuman_tools

        tools = get_rentahuman_tools(api_key="rah_your_key")

        agent = AssistantAgent(
            "task_coordinator",
            model_client=model_client,
            tools=tools,
        )
    """
    client = RentAHumanClient(api_key=api_key, base_url=base_url)
    return _make_tools(client)
