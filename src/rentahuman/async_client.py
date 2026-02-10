"""Async client for rentahuman.ai API.

Drop-in async replacement for RentAHumanClient. Uses httpx.

Usage:
    pip install rentahuman[async]

    from rentahuman.async_client import AsyncRentAHumanClient

    async with AsyncRentAHumanClient(api_key="rah_...") as client:
        humans = await client.search_humans(skill="Photography")
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from rentahuman.client import BASE_URL, DEFAULT_TIMEOUT, RentAHumanError, RateLimitError
from rentahuman.models import (
    Booking,
    BookingCreate,
    Bounty,
    BountyApplication,
    BountyCreate,
    Conversation,
    Human,
    Message,
    Skill,
)


class AsyncRentAHumanClient:
    """Async client for the rentahuman.ai REST API.

    Args:
        api_key: Your rentahuman API key (starts with rah_).
                 Required for write ops. Read-only ops work without one.
        base_url: API base URL. Override for testing.
        timeout: Request timeout in seconds.
        max_retries: Max retries on rate limit (429). 0 = no retry.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key

        self._client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(timeout),
        )

    async def __aenter__(self) -> AsyncRentAHumanClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    # ── internal ──────────────────────────────────────────────

    @staticmethod
    def _sanitize_path_param(value: str) -> str:
        """Validate path parameters to prevent path traversal."""
        if not value or "/" in value or "\\" in value or ".." in value:
            raise RentAHumanError(f"Invalid path parameter: {value!r}")
        return value

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        """Make an API request with retry on 429."""
        url = f"{self.base_url}{path}"

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = await self._client.request(method, url, **kwargs)

                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", "1.0"))
                    if attempt < self.max_retries:
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(retry_after)

                if resp.status_code >= 400:
                    body = resp.json() if resp.content else {}
                    error_msg = body.get("error", resp.reason_phrase or f"HTTP {resp.status_code}")
                    raise RentAHumanError(error_msg, status_code=resp.status_code)

                return resp.json()

            except httpx.HTTPError as e:
                last_exc = e
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise RentAHumanError(f"Request failed: {e}") from e

        raise RentAHumanError(f"Request failed after {self.max_retries} retries") from last_exc

    async def _get(self, path: str, params: dict | None = None) -> dict:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, json: dict | None = None) -> dict:
        return await self._request("POST", path, json=json)

    async def _patch(self, path: str, json: dict | None = None) -> dict:
        return await self._request("PATCH", path, json=json)

    # ── Humans ────────────────────────────────────────────────

    async def search_humans(
        self,
        skill: str | None = None,
        min_rate: float | None = None,
        max_rate: float | None = None,
        name: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Human]:
        """Search for available humans."""
        params: dict[str, Any] = {"limit": max(1, min(limit, 500)), "offset": max(0, offset)}
        if skill:
            params["skill"] = skill
        if min_rate is not None:
            params["minRate"] = min_rate
        if max_rate is not None:
            params["maxRate"] = max_rate
        if name:
            params["name"] = name

        data = await self._get("/humans", params=params)
        return [Human.model_validate(h) for h in data.get("humans", [])]

    async def get_human(self, human_id: str) -> Human:
        """Get detailed profile for a specific human."""
        human_id = self._sanitize_path_param(human_id)
        data = await self._get(f"/humans/{human_id}")
        return Human.model_validate(data.get("human", data))

    async def list_skills(self) -> list[Skill]:
        """Get all available skills on the platform."""
        data = await self._get("/skills")
        raw = data.get("skills", data)
        if raw and isinstance(raw[0], str):
            return [Skill(name=s) for s in raw]
        return [Skill.model_validate(s) for s in raw]

    async def get_reviews(self, human_id: str) -> list[dict]:
        """Get reviews and ratings for a human."""
        human_id = self._sanitize_path_param(human_id)
        data = await self._get(f"/humans/{human_id}/reviews")
        return data.get("reviews", [])

    # ── Bookings ──────────────────────────────────────────────

    async def create_booking(self, booking: BookingCreate) -> Booking:
        """Create a new booking with a human."""
        data = await self._post(
            "/bookings", json=booking.model_dump(by_alias=True, exclude_none=True),
        )
        return Booking.model_validate(data.get("booking", data))

    async def get_booking(self, booking_id: str) -> Booking:
        """Get booking details by ID."""
        booking_id = self._sanitize_path_param(booking_id)
        data = await self._get(f"/bookings/{booking_id}")
        return Booking.model_validate(data.get("booking", data))

    async def list_bookings(
        self,
        human_id: str | None = None,
        agent_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[Booking]:
        """List bookings with optional filters."""
        params: dict[str, Any] = {"limit": limit}
        if human_id:
            params["humanId"] = human_id
        if agent_id:
            params["agentId"] = agent_id
        if status:
            params["status"] = status

        data = await self._get("/bookings", params=params)
        return [Booking.model_validate(b) for b in data.get("bookings", [])]

    # ── Bounties ──────────────────────────────────────────────

    async def create_bounty(self, bounty: BountyCreate) -> Bounty:
        """Post a task bounty for humans to apply to."""
        data = await self._post(
            "/bounties", json=bounty.model_dump(by_alias=True, exclude_none=True),
        )
        return Bounty.model_validate(data.get("bounty", data))

    async def get_bounty(self, bounty_id: str) -> Bounty:
        """Get bounty details by ID."""
        bounty_id = self._sanitize_path_param(bounty_id)
        data = await self._get(f"/bounties/{bounty_id}")
        return Bounty.model_validate(data.get("bounty", data))

    async def list_bounties(self, limit: int = 20) -> list[Bounty]:
        """List available bounties."""
        data = await self._get("/bounties", params={"limit": limit})
        return [Bounty.model_validate(b) for b in data.get("bounties", [])]

    async def get_bounty_applications(self, bounty_id: str) -> list[BountyApplication]:
        """Get applications for a bounty."""
        bounty_id = self._sanitize_path_param(bounty_id)
        data = await self._get(f"/bounties/{bounty_id}/applications")
        return [BountyApplication.model_validate(a) for a in data.get("applications", [])]

    async def accept_application(self, bounty_id: str, application_id: str) -> dict:
        """Accept an application for a bounty."""
        bounty_id = self._sanitize_path_param(bounty_id)
        application_id = self._sanitize_path_param(application_id)
        return await self._post(f"/bounties/{bounty_id}/applications/{application_id}/accept")

    async def update_bounty(self, bounty_id: str, updates: dict) -> Bounty:
        """Update or cancel a bounty."""
        bounty_id = self._sanitize_path_param(bounty_id)
        data = await self._patch(f"/bounties/{bounty_id}", json=updates)
        return Bounty.model_validate(data.get("bounty", data))

    # ── Conversations ─────────────────────────────────────────

    async def start_conversation(
        self,
        human_id: str,
        subject: str,
        message: str,
        agent_type: str = "rentahuman-py",
    ) -> Conversation:
        """Start a conversation with a human."""
        payload = {
            "humanId": human_id,
            "agentType": agent_type,
            "subject": subject,
            "message": message,
        }
        data = await self._post("/conversations", json=payload)
        return Conversation.model_validate(data.get("conversation", data))

    async def send_message(self, conversation_id: str, message: str) -> Message:
        """Send a message in an existing conversation."""
        conversation_id = self._sanitize_path_param(conversation_id)
        data = await self._post(
            f"/conversations/{conversation_id}/messages",
            json={"message": message},
        )
        return Message.model_validate(data.get("message", data))

    async def get_conversation(self, conversation_id: str) -> Conversation:
        """Get a conversation with all messages."""
        conversation_id = self._sanitize_path_param(conversation_id)
        data = await self._get(f"/conversations/{conversation_id}")
        return Conversation.model_validate(data.get("conversation", data))

    async def list_conversations(self, limit: int = 20) -> list[Conversation]:
        """List all conversations."""
        data = await self._get("/conversations", params={"limit": limit})
        return [Conversation.model_validate(c) for c in data.get("conversations", [])]
