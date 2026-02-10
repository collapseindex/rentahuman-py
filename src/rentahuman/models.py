"""Pydantic models for rentahuman.ai API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Humans ────────────────────────────────────────────────────

class CryptoWallet(BaseModel):
    """A human's crypto wallet."""
    chain: str = ""
    address: str = ""


class Skill(BaseModel):
    """A skill on the platform."""
    name: str
    category: str | None = None


class Human(BaseModel):
    """A human available for hire on rentahuman.ai."""
    id: str = ""
    name: str = ""
    location: str | None = None
    rate: float | None = Field(None, description="Hourly rate in USD")
    skills: list[str] = Field(default_factory=list)
    bio: str | None = None
    availability: str | None = None
    crypto_wallets: list[CryptoWallet] = Field(default_factory=list, alias="cryptoWallets")
    rating: float | None = None
    completed_tasks: int | None = Field(None, alias="completedTasks")
    created_at: str | None = Field(None, alias="createdAt")

    model_config = {"populate_by_name": True}

    def summary(self) -> str:
        """One-line summary for agent consumption."""
        parts = [f"{self.name} ({self.id})"]
        if self.location:
            parts.append(f"in {self.location}")
        if self.rate:
            parts.append(f"${self.rate}/hr")
        if self.skills:
            parts.append(f"skills: {', '.join(self.skills[:5])}")
        if self.rating:
            parts.append(f"rating: {self.rating:.1f}")
        return " | ".join(parts)


# ── Bookings ──────────────────────────────────────────────────

class BookingCreate(BaseModel):
    """Request body for creating a booking."""
    human_id: str = Field(alias="humanId")
    agent_id: str = Field(default="rentahuman-py", alias="agentId")
    task_title: str = Field(alias="taskTitle")
    start_time: str = Field(alias="startTime")
    estimated_hours: float = Field(alias="estimatedHours")
    description: str | None = None

    model_config = {"populate_by_name": True}


class Booking(BaseModel):
    """A booking between an agent and a human."""
    id: str = ""
    human_id: str = Field("", alias="humanId")
    agent_id: str = Field("", alias="agentId")
    task_title: str = Field("", alias="taskTitle")
    status: str = "pending"
    start_time: str | None = Field(None, alias="startTime")
    estimated_hours: float | None = Field(None, alias="estimatedHours")
    created_at: str | None = Field(None, alias="createdAt")

    model_config = {"populate_by_name": True}


# ── Bounties ──────────────────────────────────────────────────

class BountyCreate(BaseModel):
    """Request body for creating a bounty."""
    agent_type: str = Field(default="rentahuman-py", alias="agentType")
    title: str
    description: str
    estimated_hours: float | None = Field(None, alias="estimatedHours")
    price_type: str = Field(default="fixed", alias="priceType")
    price: float = 0.0
    skills: list[str] = Field(default_factory=list)
    location: str | None = None

    model_config = {"populate_by_name": True}


class BountyApplication(BaseModel):
    """An application from a human to a bounty."""
    id: str = ""
    bounty_id: str = Field("", alias="bountyId")
    human_id: str = Field("", alias="humanId")
    human_name: str = Field("", alias="humanName")
    message: str = ""
    rate: float | None = None
    status: str = "pending"
    created_at: str | None = Field(None, alias="createdAt")

    model_config = {"populate_by_name": True}


class Bounty(BaseModel):
    """A task bounty posted by an agent."""
    id: str = ""
    title: str = ""
    description: str = ""
    agent_type: str = Field("", alias="agentType")
    estimated_hours: float | None = Field(None, alias="estimatedHours")
    price_type: str = Field("fixed", alias="priceType")
    price: float = 0.0
    status: str = "open"
    application_count: int = Field(0, alias="applicationCount")
    created_at: str | None = Field(None, alias="createdAt")

    model_config = {"populate_by_name": True}


# ── Conversations ─────────────────────────────────────────────

class Message(BaseModel):
    """A message within a conversation."""
    id: str = ""
    conversation_id: str = Field("", alias="conversationId")
    sender: str = ""
    content: str = ""
    created_at: str | None = Field(None, alias="createdAt")

    model_config = {"populate_by_name": True}


class Conversation(BaseModel):
    """A conversation between an agent and a human."""
    id: str = ""
    human_id: str = Field("", alias="humanId")
    agent_type: str = Field("", alias="agentType")
    subject: str = ""
    messages: list[Message] = Field(default_factory=list)
    created_at: str | None = Field(None, alias="createdAt")

    model_config = {"populate_by_name": True}
