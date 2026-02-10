"""Semantic Kernel integration for rentahuman.ai.

Provides a plugin class with kernel functions that let any Semantic Kernel
agent search, book, and hire humans via rentahuman.ai.

Usage:
    pip install rentahuman[semantic-kernel]

    from rentahuman.integrations.semantic_kernel import RentAHumanPlugin

    plugin = RentAHumanPlugin(api_key="rah_...")
    kernel.add_plugin(plugin, "rentahuman")
"""

from __future__ import annotations

from typing import Annotated

from rentahuman.client import RentAHumanClient
from rentahuman.models import BookingCreate, BountyCreate

try:
    from semantic_kernel.functions import kernel_function
except ImportError:
    raise ImportError(
        "Semantic Kernel integration requires semantic-kernel. "
        "Install with: pip install rentahuman[semantic-kernel]"
    )


class RentAHumanPlugin:
    """Semantic Kernel plugin for rentahuman.ai.

    Usage:
        from rentahuman.integrations.semantic_kernel import RentAHumanPlugin

        plugin = RentAHumanPlugin(api_key="rah_your_key")
        kernel.add_plugin(plugin, "rentahuman")
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://rentahuman.ai/api",
    ):
        self._client = RentAHumanClient(api_key=api_key, base_url=base_url)

    # ── Search ────────────────────────────────────────────────

    @kernel_function(
        name="search_humans",
        description=(
            "Search for humans available for hire on rentahuman.ai. "
            "Filter by skill, max hourly rate, or limit results."
        ),
    )
    def search_humans(
        self,
        skill: Annotated[str | None, "Skill to search for (e.g. 'Photography')"] = None,
        max_rate: Annotated[float | None, "Maximum hourly rate in USD"] = None,
        limit: Annotated[int, "Max results (1-500)"] = 10,
    ) -> str:
        humans = self._client.search_humans(skill=skill, max_rate=max_rate, limit=limit)
        if not humans:
            return "No humans found matching your criteria."
        lines = [f"Found {len(humans)} human(s):"]
        for h in humans:
            lines.append(f"  - {h.summary()}")
        return "\n".join(lines)

    @kernel_function(
        name="get_human_profile",
        description="Get full profile for a human including skills, rate, location, and availability.",
    )
    def get_human_profile(
        self,
        human_id: Annotated[str, "The human's ID"],
    ) -> str:
        h = self._client.get_human(human_id)
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

    @kernel_function(
        name="list_skills",
        description="List all available skills that humans offer on rentahuman.ai.",
    )
    def list_skills(self) -> str:
        skills = self._client.list_skills()
        if not skills:
            return "No skills found."
        return "Available skills: " + ", ".join(s.name for s in skills)

    # ── Bookings ──────────────────────────────────────────────

    @kernel_function(
        name="create_booking",
        description=(
            "Book a human for a task. Requires human ID, task title, "
            "start time (ISO 8601), and estimated hours."
        ),
    )
    def create_booking(
        self,
        human_id: Annotated[str, "ID of the human to book"],
        task_title: Annotated[str, "Brief title of the task"],
        start_time: Annotated[str, "ISO 8601 datetime for task start"],
        estimated_hours: Annotated[float, "Estimated duration in hours"],
        description: Annotated[str | None, "Detailed task description"] = None,
    ) -> str:
        booking = self._client.create_booking(BookingCreate(
            humanId=human_id,
            taskTitle=task_title,
            startTime=start_time,
            estimatedHours=estimated_hours,
            description=description,
        ))
        return f"Booking created! ID: {booking.id} | Status: {booking.status} | Task: {booking.task_title}"

    # ── Bounties ──────────────────────────────────────────────

    @kernel_function(
        name="create_bounty",
        description=(
            "Post a task bounty for humans to apply to. "
            "Describe the task, set a price, and optionally specify skills and location."
        ),
    )
    def create_bounty(
        self,
        title: Annotated[str, "Task title"],
        description: Annotated[str, "Detailed description of what needs to be done"],
        price: Annotated[float, "Fixed price in USD"],
        estimated_hours: Annotated[float | None, "Estimated hours"] = None,
        location: Annotated[str | None, "Required location"] = None,
    ) -> str:
        bounty = self._client.create_bounty(BountyCreate(
            title=title,
            description=description,
            price=price,
            estimatedHours=estimated_hours,
            location=location,
        ))
        return f"Bounty posted! ID: {bounty.id} | Title: {bounty.title} | Price: ${bounty.price}"

    @kernel_function(
        name="get_bounty_applications",
        description="View applications from humans for a specific bounty.",
    )
    def get_bounty_applications(
        self,
        bounty_id: Annotated[str, "The bounty ID"],
    ) -> str:
        apps = self._client.get_bounty_applications(bounty_id)
        if not apps:
            return "No applications yet."
        lines = [f"{len(apps)} application(s):"]
        for a in apps:
            msg = a.message[:80] + "..." if len(a.message) > 80 else a.message
            lines.append(f"  - {a.human_name} ({a.human_id}): ${a.rate}/hr | {msg}")
        return "\n".join(lines)

    @kernel_function(
        name="accept_application",
        description="Accept a bounty application, hiring the human for the task.",
    )
    def accept_application(
        self,
        bounty_id: Annotated[str, "The bounty ID"],
        application_id: Annotated[str, "The application ID to accept"],
    ) -> str:
        result = self._client.accept_application(bounty_id, application_id)
        return f"Application accepted! {result.get('message', 'Human has been hired.')}"

    # ── Conversations ─────────────────────────────────────────

    @kernel_function(
        name="start_conversation",
        description="Start a direct conversation with a human to discuss task details.",
    )
    def start_conversation(
        self,
        human_id: Annotated[str, "ID of the human to message"],
        subject: Annotated[str, "Conversation subject line"],
        message: Annotated[str, "Opening message"],
    ) -> str:
        convo = self._client.start_conversation(
            human_id=human_id, subject=subject, message=message,
        )
        return f"Conversation started! ID: {convo.id} | Subject: {convo.subject}"

    @kernel_function(
        name="send_message",
        description="Send a message in an existing conversation with a human.",
    )
    def send_message(
        self,
        conversation_id: Annotated[str, "The conversation ID"],
        message: Annotated[str, "Message content"],
    ) -> str:
        msg = self._client.send_message(conversation_id, message)
        return f"Message sent (ID: {msg.id})"
