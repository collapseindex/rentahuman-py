"""LangChain integration for rentahuman.ai.

Provides a toolkit of LangChain-compatible tools that let any LangChain agent
search, book, and hire humans for real-world tasks via rentahuman.ai.

Usage:
    pip install rentahuman[langchain]

    from rentahuman.integrations.langchain import RentAHumanToolkit

    toolkit = RentAHumanToolkit(api_key="rah_...")
    tools = toolkit.get_tools()
    # Plug into any LangChain agent
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel, Field

from rentahuman.client import RentAHumanClient
from rentahuman.models import BookingCreate, BountyCreate

try:
    from langchain_core.tools import BaseTool
except ImportError:
    raise ImportError(
        "LangChain integration requires langchain-core. "
        "Install with: pip install rentahuman[langchain]"
    )


# ── Arg Schemas ───────────────────────────────────────────────


class SearchHumansArgs(BaseModel):
    """Arguments for searching humans."""
    skill: str | None = Field(None, description="Skill to search for (e.g. 'Photography', 'Packages', 'Meetings')")
    max_rate: float | None = Field(None, description="Maximum hourly rate in USD")
    min_rate: float | None = Field(None, description="Minimum hourly rate in USD")
    name: str | None = Field(None, description="Filter by name (case-insensitive)")
    limit: int = Field(10, description="Max results to return (1-500)")


class GetHumanArgs(BaseModel):
    """Arguments for getting a human profile."""
    human_id: str = Field(description="The human's ID")


class GetReviewsArgs(BaseModel):
    """Arguments for getting a human's reviews."""
    human_id: str = Field(description="The human's ID")


class CreateBookingArgs(BaseModel):
    """Arguments for creating a booking."""
    human_id: str = Field(description="ID of the human to book")
    task_title: str = Field(description="Brief title of the task")
    start_time: str = Field(description="ISO 8601 datetime for when the task should start")
    estimated_hours: float = Field(description="Estimated duration in hours")
    description: str | None = Field(None, description="Detailed task description")


class GetBookingArgs(BaseModel):
    """Arguments for getting booking details."""
    booking_id: str = Field(description="The booking ID")


class ListBookingsArgs(BaseModel):
    """Arguments for listing bookings."""
    status: str | None = Field(None, description="Filter by status: pending, confirmed, in_progress, completed")
    limit: int = Field(20, description="Max results")


class CreateBountyArgs(BaseModel):
    """Arguments for creating a bounty."""
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed description of what needs to be done")
    price: float = Field(description="Fixed price in USD")
    estimated_hours: float | None = Field(None, description="Estimated hours to complete")
    skills: list[str] = Field(default_factory=list, description="Required skills")
    location: str | None = Field(None, description="Required location (city/region)")


class GetBountyArgs(BaseModel):
    """Arguments for getting bounty details."""
    bounty_id: str = Field(description="The bounty ID")


class GetBountyApplicationsArgs(BaseModel):
    """Arguments for getting bounty applications."""
    bounty_id: str = Field(description="The bounty ID")


class AcceptApplicationArgs(BaseModel):
    """Arguments for accepting a bounty application."""
    bounty_id: str = Field(description="The bounty ID")
    application_id: str = Field(description="The application ID to accept")


class StartConversationArgs(BaseModel):
    """Arguments for starting a conversation."""
    human_id: str = Field(description="ID of the human to message")
    subject: str = Field(description="Conversation subject line")
    message: str = Field(description="Opening message")


class SendMessageArgs(BaseModel):
    """Arguments for sending a message."""
    conversation_id: str = Field(description="The conversation ID")
    message: str = Field(description="Message content")


class GetConversationArgs(BaseModel):
    """Arguments for getting a conversation."""
    conversation_id: str = Field(description="The conversation ID")


# ── Tools ─────────────────────────────────────────────────────


class SearchHumansTool(BaseTool):
    """Search for humans available on rentahuman.ai by skill, rate, or name."""

    name: str = "search_humans"
    description: str = (
        "Search for humans available for hire on rentahuman.ai. "
        "Filter by skill (e.g. 'Photography', 'Packages', 'In-Person Meetings'), "
        "hourly rate range, or name. Returns a list of matching human profiles."
    )
    args_schema: Type[BaseModel] = SearchHumansArgs
    client: Any = Field(exclude=True)

    def _run(self, **kwargs: Any) -> str:
        args = SearchHumansArgs(**kwargs)
        humans = self.client.search_humans(
            skill=args.skill,
            min_rate=args.min_rate,
            max_rate=args.max_rate,
            name=args.name,
            limit=args.limit,
        )
        if not humans:
            return "No humans found matching your criteria."
        lines = [f"Found {len(humans)} human(s):"]
        for h in humans:
            lines.append(f"  - {h.summary()}")
        return "\n".join(lines)


class GetHumanProfileTool(BaseTool):
    """Get detailed profile for a specific human."""

    name: str = "get_human_profile"
    description: str = (
        "Get full profile for a specific human on rentahuman.ai, "
        "including skills, availability, rate, location, and crypto wallets."
    )
    args_schema: Type[BaseModel] = GetHumanArgs
    client: Any = Field(exclude=True)

    def _run(self, human_id: str) -> str:
        h = self.client.get_human(human_id)
        parts = [f"Name: {h.name}", f"ID: {h.id}"]
        if h.location:
            parts.append(f"Location: {h.location}")
        if h.rate:
            parts.append(f"Rate: ${h.rate}/hr")
        if h.skills:
            parts.append(f"Skills: {', '.join(h.skills)}")
        if h.bio:
            parts.append(f"Bio: {h.bio}")
        if h.availability:
            parts.append(f"Availability: {h.availability}")
        if h.rating:
            parts.append(f"Rating: {h.rating:.1f}")
        if h.completed_tasks:
            parts.append(f"Completed tasks: {h.completed_tasks}")
        return "\n".join(parts)


class GetReviewsTool(BaseTool):
    """Get reviews for a human."""

    name: str = "get_reviews"
    description: str = "Get reviews and ratings for a specific human. Useful for evaluating reliability before booking."
    args_schema: Type[BaseModel] = GetReviewsArgs
    client: Any = Field(exclude=True)

    def _run(self, human_id: str) -> str:
        reviews = self.client.get_reviews(human_id)
        if not reviews:
            return "No reviews found for this human."
        lines = [f"{len(reviews)} review(s):"]
        for r in reviews:
            lines.append(f"  - {r.get('rating', '?')}/5: {r.get('comment', 'No comment')}")
        return "\n".join(lines)


class ListSkillsTool(BaseTool):
    """List all available skills on rentahuman.ai."""

    name: str = "list_skills"
    description: str = "Get all available skills that humans offer on rentahuman.ai. Useful for discovering what tasks humans can do."
    client: Any = Field(exclude=True)

    def _run(self) -> str:
        skills = self.client.list_skills()
        if not skills:
            return "No skills found."
        return "Available skills: " + ", ".join(s.name for s in skills)


class CreateBookingTool(BaseTool):
    """Book a human for a task."""

    name: str = "create_booking"
    description: str = (
        "Create a booking to hire a human for a specific task. "
        "Requires the human's ID, a task title, start time (ISO 8601), and estimated hours. "
        "Payment is handled via Stripe Connect escrow."
    )
    args_schema: Type[BaseModel] = CreateBookingArgs
    client: Any = Field(exclude=True)

    def _run(self, **kwargs: Any) -> str:
        args = CreateBookingArgs(**kwargs)
        booking = self.client.create_booking(BookingCreate(
            humanId=args.human_id,
            taskTitle=args.task_title,
            startTime=args.start_time,
            estimatedHours=args.estimated_hours,
            description=args.description,
        ))
        return (
            f"Booking created!\n"
            f"  ID: {booking.id}\n"
            f"  Status: {booking.status}\n"
            f"  Task: {booking.task_title}"
        )


class GetBookingTool(BaseTool):
    """Get booking details."""

    name: str = "get_booking"
    description: str = "Get details and status of a booking by its ID."
    args_schema: Type[BaseModel] = GetBookingArgs
    client: Any = Field(exclude=True)

    def _run(self, booking_id: str) -> str:
        b = self.client.get_booking(booking_id)
        return f"Booking {b.id}: {b.task_title} | Status: {b.status} | Hours: {b.estimated_hours}"


class ListBookingsTool(BaseTool):
    """List your bookings."""

    name: str = "list_bookings"
    description: str = "List your bookings, optionally filtered by status (pending, confirmed, in_progress, completed)."
    args_schema: Type[BaseModel] = ListBookingsArgs
    client: Any = Field(exclude=True)

    def _run(self, **kwargs: Any) -> str:
        args = ListBookingsArgs(**kwargs)
        bookings = self.client.list_bookings(status=args.status, limit=args.limit)
        if not bookings:
            return "No bookings found."
        lines = [f"{len(bookings)} booking(s):"]
        for b in bookings:
            lines.append(f"  - {b.id}: {b.task_title} [{b.status}]")
        return "\n".join(lines)


class CreateBountyTool(BaseTool):
    """Post a task bounty for humans to apply to."""

    name: str = "create_bounty"
    description: str = (
        "Post a task bounty on rentahuman.ai for humans to apply to. "
        "Describe what needs to be done, set a price, and optionally specify "
        "required skills and location. Humans will apply and you can review them."
    )
    args_schema: Type[BaseModel] = CreateBountyArgs
    client: Any = Field(exclude=True)

    def _run(self, **kwargs: Any) -> str:
        args = CreateBountyArgs(**kwargs)
        bounty = self.client.create_bounty(BountyCreate(
            title=args.title,
            description=args.description,
            price=args.price,
            estimatedHours=args.estimated_hours,
            skills=args.skills,
            location=args.location,
        ))
        return (
            f"Bounty posted!\n"
            f"  ID: {bounty.id}\n"
            f"  Title: {bounty.title}\n"
            f"  Price: ${bounty.price}\n"
            f"  Status: {bounty.status}"
        )


class GetBountyTool(BaseTool):
    """Get bounty details."""

    name: str = "get_bounty"
    description: str = "Get details of a specific bounty by ID."
    args_schema: Type[BaseModel] = GetBountyArgs
    client: Any = Field(exclude=True)

    def _run(self, bounty_id: str) -> str:
        b = self.client.get_bounty(bounty_id)
        return (
            f"Bounty {b.id}: {b.title}\n"
            f"  Description: {b.description}\n"
            f"  Price: ${b.price} ({b.price_type})\n"
            f"  Status: {b.status}\n"
            f"  Applications: {b.application_count}"
        )


class GetBountyApplicationsTool(BaseTool):
    """View applications for your bounty."""

    name: str = "get_bounty_applications"
    description: str = "View all applications from humans for a specific bounty. Use this to review candidates."
    args_schema: Type[BaseModel] = GetBountyApplicationsArgs
    client: Any = Field(exclude=True)

    def _run(self, bounty_id: str) -> str:
        apps = self.client.get_bounty_applications(bounty_id)
        if not apps:
            return "No applications yet."
        lines = [f"{len(apps)} application(s):"]
        for a in apps:
            lines.append(
                f"  - {a.human_name} ({a.human_id}): "
                f"${a.rate}/hr | {a.message[:80]}..."
                if len(a.message) > 80
                else f"  - {a.human_name} ({a.human_id}): ${a.rate}/hr | {a.message}"
            )
        return "\n".join(lines)


class AcceptApplicationTool(BaseTool):
    """Accept a bounty application."""

    name: str = "accept_application"
    description: str = "Accept a specific application for a bounty. This hires the human for the task."
    args_schema: Type[BaseModel] = AcceptApplicationArgs
    client: Any = Field(exclude=True)

    def _run(self, bounty_id: str, application_id: str) -> str:
        result = self.client.accept_application(bounty_id, application_id)
        return f"Application accepted! {result.get('message', 'Human has been hired.')}"


class StartConversationTool(BaseTool):
    """Start a direct conversation with a human."""

    name: str = "start_conversation"
    description: str = (
        "Start a direct conversation with a human on rentahuman.ai. "
        "Use this to discuss task details, negotiate terms, or ask questions "
        "before making a booking."
    )
    args_schema: Type[BaseModel] = StartConversationArgs
    client: Any = Field(exclude=True)

    def _run(self, **kwargs: Any) -> str:
        args = StartConversationArgs(**kwargs)
        convo = self.client.start_conversation(
            human_id=args.human_id,
            subject=args.subject,
            message=args.message,
        )
        return f"Conversation started!\n  ID: {convo.id}\n  Subject: {convo.subject}"


class SendMessageTool(BaseTool):
    """Send a message in a conversation."""

    name: str = "send_message"
    description: str = "Send a message in an existing conversation with a human."
    args_schema: Type[BaseModel] = SendMessageArgs
    client: Any = Field(exclude=True)

    def _run(self, conversation_id: str, message: str) -> str:
        msg = self.client.send_message(conversation_id, message)
        return f"Message sent (ID: {msg.id})"


class GetConversationTool(BaseTool):
    """Get conversation with all messages."""

    name: str = "get_conversation"
    description: str = "Get a conversation and all messages in it."
    args_schema: Type[BaseModel] = GetConversationArgs
    client: Any = Field(exclude=True)

    def _run(self, conversation_id: str) -> str:
        convo = self.client.get_conversation(conversation_id)
        lines = [f"Conversation: {convo.subject} (ID: {convo.id})"]
        for m in convo.messages:
            lines.append(f"  [{m.sender}]: {m.content}")
        return "\n".join(lines)


class ListConversationsTool(BaseTool):
    """List your conversations."""

    name: str = "list_conversations"
    description: str = "List all your conversations with humans."
    client: Any = Field(exclude=True)

    def _run(self) -> str:
        convos = self.client.list_conversations()
        if not convos:
            return "No conversations."
        lines = [f"{len(convos)} conversation(s):"]
        for c in convos:
            lines.append(f"  - {c.id}: {c.subject}")
        return "\n".join(lines)


# ── Toolkit ───────────────────────────────────────────────────


class RentAHumanToolkit:
    """LangChain toolkit for rentahuman.ai.

    Bundles all rentahuman tools for easy integration with any LangChain agent.

    Usage:
        from rentahuman.integrations.langchain import RentAHumanToolkit

        toolkit = RentAHumanToolkit(api_key="rah_your_key")
        tools = toolkit.get_tools()

        # Use with any LangChain agent
        from langchain.agents import create_react_agent
        agent = create_react_agent(llm, tools, prompt)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://rentahuman.ai/api",
    ):
        self.client = RentAHumanClient(api_key=api_key, base_url=base_url)

    def get_tools(self) -> list[BaseTool]:
        """Get all rentahuman tools as a list.

        Returns:
            List of LangChain-compatible tools for interacting with rentahuman.ai.
        """
        c = self.client
        return [
            # Discovery
            SearchHumansTool(client=c),
            GetHumanProfileTool(client=c),
            GetReviewsTool(client=c),
            ListSkillsTool(client=c),
            # Bookings
            CreateBookingTool(client=c),
            GetBookingTool(client=c),
            ListBookingsTool(client=c),
            # Bounties
            CreateBountyTool(client=c),
            GetBountyTool(client=c),
            GetBountyApplicationsTool(client=c),
            AcceptApplicationTool(client=c),
            # Conversations
            StartConversationTool(client=c),
            SendMessageTool(client=c),
            GetConversationTool(client=c),
            ListConversationsTool(client=c),
        ]

    def get_search_tools(self) -> list[BaseTool]:
        """Get only search/discovery tools (no API key required)."""
        c = self.client
        return [
            SearchHumansTool(client=c),
            GetHumanProfileTool(client=c),
            GetReviewsTool(client=c),
            ListSkillsTool(client=c),
        ]

    def get_booking_tools(self) -> list[BaseTool]:
        """Get only booking-related tools."""
        c = self.client
        return [
            CreateBookingTool(client=c),
            GetBookingTool(client=c),
            ListBookingsTool(client=c),
        ]

    def get_bounty_tools(self) -> list[BaseTool]:
        """Get only bounty-related tools."""
        c = self.client
        return [
            CreateBountyTool(client=c),
            GetBountyTool(client=c),
            GetBountyApplicationsTool(client=c),
            AcceptApplicationTool(client=c),
        ]
