"""Tests for the async httpx client."""

from __future__ import annotations

import pytest
import httpx

from rentahuman.async_client import AsyncRentAHumanClient
from rentahuman.client import RentAHumanError, RateLimitError

from .conftest import MOCK_HUMANS, MOCK_BOUNTY, MOCK_BOOKING, MOCK_CONVERSATION

BASE = "https://rentahuman.ai/api"


@pytest.fixture
def async_client():
    return AsyncRentAHumanClient(api_key="rah_test_key", max_retries=0)


class TestAsyncSearchHumans:
    @pytest.mark.asyncio
    async def test_search_by_skill(self, async_client, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/humans?limit=20&offset=0&skill=Photography",
            json={"humans": MOCK_HUMANS},
        )
        humans = await async_client.search_humans(skill="Photography")
        assert len(humans) == 2
        assert humans[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_search_empty(self, async_client, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/humans?limit=20&offset=0&skill=Nonexistent",
            json={"humans": []},
        )
        humans = await async_client.search_humans(skill="Nonexistent")
        assert humans == []


class TestAsyncBookings:
    @pytest.mark.asyncio
    async def test_create_booking(self, async_client, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/bookings",
            json={"booking": MOCK_BOOKING},
            method="POST",
        )
        from rentahuman.models import BookingCreate

        booking = await async_client.create_booking(BookingCreate(
            humanId="h_1",
            taskTitle="Test task",
            startTime="2026-03-01T10:00:00Z",
            estimatedHours=2.0,
        ))
        assert booking.id == "booking_001"


class TestAsyncBounties:
    @pytest.mark.asyncio
    async def test_create_bounty(self, async_client, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/bounties",
            json={"bounty": MOCK_BOUNTY},
            method="POST",
        )
        from rentahuman.models import BountyCreate

        bounty = await async_client.create_bounty(BountyCreate(
            title="Test bounty",
            description="Do a thing",
            price=50.0,
        ))
        assert bounty.id == "bounty_001"


class TestAsyncConversations:
    @pytest.mark.asyncio
    async def test_start_conversation(self, async_client, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/conversations",
            json={"conversation": MOCK_CONVERSATION},
            method="POST",
        )
        convo = await async_client.start_conversation(
            human_id="h_1", subject="Hello", message="Hi there",
        )
        assert convo.id == "conv_001"


class TestAsyncErrors:
    @pytest.mark.asyncio
    async def test_rate_limit(self, httpx_mock):
        client = AsyncRentAHumanClient(api_key="rah_test_key", max_retries=0)
        httpx_mock.add_response(
            url=f"{BASE}/humans?limit=20&offset=0",
            status_code=429,
            headers={"Retry-After": "0"},
        )
        with pytest.raises(RateLimitError):
            await client.search_humans()

    @pytest.mark.asyncio
    async def test_auth_error(self, async_client, httpx_mock):
        httpx_mock.add_response(
            url=f"{BASE}/bounties",
            status_code=401,
            json={"error": "Unauthorized"},
            method="POST",
        )
        from rentahuman.models import BountyCreate

        with pytest.raises(RentAHumanError, match="Unauthorized"):
            await async_client.create_bounty(BountyCreate(
                title="x", description="x", price=1.0,
            ))

    @pytest.mark.asyncio
    async def test_path_traversal_rejected(self, async_client):
        with pytest.raises(RentAHumanError, match="Invalid path"):
            await async_client.get_human("../etc/passwd")
