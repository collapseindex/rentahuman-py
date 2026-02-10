"""CrewAI integration for rentahuman.ai.

Provides a toolkit of CrewAI-compatible tools that let any CrewAI agent
search, book, and hire humans for real-world tasks via rentahuman.ai.

Usage:
    pip install rentahuman[crewai]

    from rentahuman.integrations.crewai import RentAHumanCrewTools

    rah = RentAHumanCrewTools(api_key="rah_...")
    tools = rah.get_tools()
    # Pass to any CrewAI Agent
    agent = Agent(role="...", tools=tools)
"""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel, Field

from rentahuman.client import RentAHumanClient
from rentahuman.models import BookingCreate, BountyCreate

try:
    from crewai.tools import BaseTool
except ImportError:
    raise ImportError(
        "CrewAI integration requires crewai. "
        "Install with: pip install rentahuman[crewai]"
    )


# ── Arg Schemas ───────────────────────────────────────────────


class SearchHumansArgs(BaseModel):
    """Input for searching humans."""
    skill: str | None = Field(None, description="Skill to search for (e.g. 'Photography', 'Packages')")
    max_rate: float | None = Field(None, description="Maximum hourly rate in USD")
    limit: int = Field(10, description="Max results (1-500)")


class GetHumanArgs(BaseModel):
    """Input for getting a human profile."""
    human_id: str = Field(description="The human's ID")


class CreateBookingArgs(BaseModel):
    """Input for creating a booking."""
    human_id: str = Field(description="ID of the human to book")
    task_title: str = Field(description="Brief title of the task")
    start_time: str = Field(description="ISO 8601 datetime for task start")
    estimated_hours: float = Field(description="Estimated duration in hours")
    description: str | None = Field(None, description="Detailed task description")


class CreateBountyArgs(BaseModel):
    """Input for creating a bounty."""
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed description of what needs to be done")
    price: float = Field(description="Fixed price in USD")
    estimated_hours: float | None = Field(None, description="Estimated hours")
    skills: list[str] = Field(default_factory=list, description="Required skills")
    location: str | None = Field(None, description="Required location")


class GetBountyApplicationsArgs(BaseModel):
    """Input for getting bounty applications."""
    bounty_id: str = Field(description="The bounty ID")


class AcceptApplicationArgs(BaseModel):
    """Input for accepting a bounty application."""
    bounty_id: str = Field(description="The bounty ID")
    application_id: str = Field(description="The application ID to accept")


class StartConversationArgs(BaseModel):
    """Input for starting a conversation."""
    human_id: str = Field(description="ID of the human to message")
    subject: str = Field(description="Conversation subject line")
    message: str = Field(description="Opening message")


class SendMessageArgs(BaseModel):
    """Input for sending a message."""
    conversation_id: str = Field(description="The conversation ID")
    message: str = Field(description="Message content")


# ── Tools ─────────────────────────────────────────────────────


class SearchHumansTool(BaseTool):
    name: str = "search_humans"
    description: str = (
        "Search for humans available for hire on rentahuman.ai. "
        "Filter by skill (e.g. 'Photography', 'Packages', 'Meetings'), "
        "hourly rate, or name."
    )
    args_schema: Type[BaseModel] = SearchHumansArgs
    client: Any = None

    def _run(self, **kwargs: Any) -> str:
        args = SearchHumansArgs(**kwargs)
        humans = self.client.search_humans(
            skill=args.skill, max_rate=args.max_rate, limit=args.limit,
        )
        if not humans:
            return "No humans found matching your criteria."
        lines = [f"Found {len(humans)} human(s):"]
        for h in humans:
            lines.append(f"  - {h.summary()}")
        return "\n".join(lines)


class GetHumanProfileTool(BaseTool):
    name: str = "get_human_profile"
    description: str = "Get full profile for a human on rentahuman.ai including skills, rate, location, and availability."
    args_schema: Type[BaseModel] = GetHumanArgs
    client: Any = None

    def _run(self, human_id: str) -> str:
        h = self.client.get_human(human_id)
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


class ListSkillsTool(BaseTool):
    name: str = "list_skills"
    description: str = "List all available skills that humans offer on rentahuman.ai."
    client: Any = None

    def _run(self) -> str:
        skills = self.client.list_skills()
        if not skills:
            return "No skills found."
        return "Available skills: " + ", ".join(s.name for s in skills)


class CreateBookingTool(BaseTool):
    name: str = "create_booking"
    description: str = (
        "Book a human for a task on rentahuman.ai. "
        "Requires human ID, task title, start time (ISO 8601), and estimated hours."
    )
    args_schema: Type[BaseModel] = CreateBookingArgs
    client: Any = None

    def _run(self, **kwargs: Any) -> str:
        args = CreateBookingArgs(**kwargs)
        booking = self.client.create_booking(BookingCreate(
            humanId=args.human_id,
            taskTitle=args.task_title,
            startTime=args.start_time,
            estimatedHours=args.estimated_hours,
            description=args.description,
        ))
        return f"Booking created! ID: {booking.id} | Status: {booking.status} | Task: {booking.task_title}"


class CreateBountyTool(BaseTool):
    name: str = "create_bounty"
    description: str = (
        "Post a task bounty on rentahuman.ai for humans to apply to. "
        "Describe the task, set a price, and optionally specify skills and location."
    )
    args_schema: Type[BaseModel] = CreateBountyArgs
    client: Any = None

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
        return f"Bounty posted! ID: {bounty.id} | Title: {bounty.title} | Price: ${bounty.price}"


class GetBountyApplicationsTool(BaseTool):
    name: str = "get_bounty_applications"
    description: str = "View applications from humans for a specific bounty on rentahuman.ai."
    args_schema: Type[BaseModel] = GetBountyApplicationsArgs
    client: Any = None

    def _run(self, bounty_id: str) -> str:
        apps = self.client.get_bounty_applications(bounty_id)
        if not apps:
            return "No applications yet."
        lines = [f"{len(apps)} application(s):"]
        for a in apps:
            msg = a.message[:80] + "..." if len(a.message) > 80 else a.message
            lines.append(f"  - {a.human_name} ({a.human_id}): ${a.rate}/hr | {msg}")
        return "\n".join(lines)


class AcceptApplicationTool(BaseTool):
    name: str = "accept_application"
    description: str = "Accept a bounty application, hiring the human for the task."
    args_schema: Type[BaseModel] = AcceptApplicationArgs
    client: Any = None

    def _run(self, bounty_id: str, application_id: str) -> str:
        result = self.client.accept_application(bounty_id, application_id)
        return f"Application accepted! {result.get('message', 'Human has been hired.')}"


class StartConversationTool(BaseTool):
    name: str = "start_conversation"
    description: str = "Start a direct conversation with a human on rentahuman.ai to discuss task details."
    args_schema: Type[BaseModel] = StartConversationArgs
    client: Any = None

    def _run(self, **kwargs: Any) -> str:
        args = StartConversationArgs(**kwargs)
        convo = self.client.start_conversation(
            human_id=args.human_id, subject=args.subject, message=args.message,
        )
        return f"Conversation started! ID: {convo.id} | Subject: {convo.subject}"


class SendMessageTool(BaseTool):
    name: str = "send_message"
    description: str = "Send a message in an existing conversation with a human."
    args_schema: Type[BaseModel] = SendMessageArgs
    client: Any = None

    def _run(self, conversation_id: str, message: str) -> str:
        msg = self.client.send_message(conversation_id, message)
        return f"Message sent (ID: {msg.id})"


# ── Toolkit ───────────────────────────────────────────────────


class RentAHumanCrewTools:
    """CrewAI toolkit for rentahuman.ai.

    Usage:
        from rentahuman.integrations.crewai import RentAHumanCrewTools

        rah = RentAHumanCrewTools(api_key="rah_your_key")

        agent = Agent(
            role="Task Coordinator",
            goal="Hire humans for physical tasks",
            tools=rah.get_tools(),
        )
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://rentahuman.ai/api",
    ):
        self.client = RentAHumanClient(api_key=api_key, base_url=base_url)

    def get_tools(self) -> list[BaseTool]:
        """Get all rentahuman tools for CrewAI agents."""
        c = self.client
        return [
            SearchHumansTool(client=c),
            GetHumanProfileTool(client=c),
            ListSkillsTool(client=c),
            CreateBookingTool(client=c),
            CreateBountyTool(client=c),
            GetBountyApplicationsTool(client=c),
            AcceptApplicationTool(client=c),
            StartConversationTool(client=c),
            SendMessageTool(client=c),
        ]

    def get_search_tools(self) -> list[BaseTool]:
        """Get only search/discovery tools (no API key required)."""
        c = self.client
        return [
            SearchHumansTool(client=c),
            GetHumanProfileTool(client=c),
            ListSkillsTool(client=c),
        ]
