"""Tests for the core RentAHumanClient."""

import pytest
import responses

from rentahuman import RentAHumanClient
from rentahuman.client import RateLimitError, RentAHumanError
from rentahuman.models import BookingCreate, BountyCreate

from .conftest import BASE, MOCK_BOOKING, MOCK_BOUNTY, MOCK_CONVERSATION, MOCK_HUMANS


# ── Search ────────────────────────────────────────────────────


class TestSearchHumans:

    @responses.activate
    def test_search_by_skill(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/humans",
            json={"success": True, "humans": MOCK_HUMANS, "count": 2},
            status=200,
        )
        humans = client.search_humans(skill="Packages")
        assert len(humans) == 2
        assert humans[0].name == "Alice"
        assert humans[0].id == "human_test_001"
        assert "Packages" in humans[0].skills

    @responses.activate
    def test_search_with_rate_filter(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/humans",
            json={"success": True, "humans": [MOCK_HUMANS[0]], "count": 1},
            status=200,
        )
        humans = client.search_humans(max_rate=50)
        assert len(humans) == 1
        assert humans[0].rate <= 50

    @responses.activate
    def test_search_empty(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/humans",
            json={"success": True, "humans": [], "count": 0},
            status=200,
        )
        humans = client.search_humans(skill="Nonexistent")
        assert humans == []


class TestGetHuman:

    @responses.activate
    def test_get_profile(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/humans/human_test_001",
            json={"success": True, "human": MOCK_HUMANS[0]},
            status=200,
        )
        h = client.get_human("human_test_001")
        assert h.name == "Alice"
        assert h.location == "San Francisco"
        assert h.rate == 45.0
        assert h.completed_tasks == 127

    @responses.activate
    def test_get_not_found(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/humans/nonexistent",
            json={"success": False, "error": "Human not found"},
            status=404,
        )
        with pytest.raises(RentAHumanError) as exc:
            client.get_human("nonexistent")
        assert exc.value.status_code == 404


# ── Bookings ──────────────────────────────────────────────────


class TestBookings:

    @responses.activate
    def test_create_booking(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/bookings",
            json={"success": True, "booking": MOCK_BOOKING},
            status=200,
        )
        booking = client.create_booking(BookingCreate(
            humanId="human_test_001",
            taskTitle="Pick up package",
            startTime="2026-02-10T14:00:00Z",
            estimatedHours=1.5,
        ))
        assert booking.id == "booking_001"
        assert booking.status == "pending"
        assert booking.task_title == "Pick up package"

    @responses.activate
    def test_get_booking(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/bookings/booking_001",
            json={"success": True, "booking": MOCK_BOOKING},
            status=200,
        )
        b = client.get_booking("booking_001")
        assert b.id == "booking_001"

    @responses.activate
    def test_list_bookings(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/bookings",
            json={"success": True, "bookings": [MOCK_BOOKING], "count": 1},
            status=200,
        )
        bookings = client.list_bookings()
        assert len(bookings) == 1


# ── Bounties ──────────────────────────────────────────────────


class TestBounties:

    @responses.activate
    def test_create_bounty(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/bounties",
            json={"success": True, "bounty": MOCK_BOUNTY},
            status=200,
        )
        bounty = client.create_bounty(BountyCreate(
            title="Photograph storefront",
            description="Take 5 photos of 123 Broadway.",
            price=50.0,
            estimatedHours=1.0,
        ))
        assert bounty.id == "bounty_001"
        assert bounty.price == 50.0

    @responses.activate
    def test_list_bounties(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/bounties",
            json={"success": True, "bounties": [MOCK_BOUNTY], "count": 1},
            status=200,
        )
        bounties = client.list_bounties()
        assert len(bounties) == 1
        assert bounties[0].title == "Photograph storefront"


# ── Conversations ─────────────────────────────────────────────


class TestConversations:

    @responses.activate
    def test_start_conversation(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/conversations",
            json={"success": True, "conversation": MOCK_CONVERSATION},
            status=200,
        )
        convo = client.start_conversation(
            human_id="human_test_001",
            subject="Package pickup",
            message="Hi! Can you pick up a package?",
        )
        assert convo.id == "conv_001"
        assert convo.subject == "Package pickup"

    @responses.activate
    def test_get_conversation(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/conversations/conv_001",
            json={"success": True, "conversation": MOCK_CONVERSATION},
            status=200,
        )
        convo = client.get_conversation("conv_001")
        assert len(convo.messages) == 2
        assert convo.messages[0].sender == "agent"
        assert convo.messages[1].sender == "human"


# ── Error Handling ────────────────────────────────────────────


class TestErrors:

    @responses.activate
    def test_rate_limit_retries(self, client):
        # First call: 429, second call: success
        responses.add(
            responses.GET,
            f"{BASE}/humans",
            json={"error": "Rate limited"},
            status=429,
            headers={"Retry-After": "0.01"},
        )
        responses.add(
            responses.GET,
            f"{BASE}/humans",
            json={"success": True, "humans": MOCK_HUMANS, "count": 2},
            status=200,
        )
        humans = client.search_humans()
        assert len(humans) == 2

    @responses.activate
    def test_auth_error(self):
        client = RentAHumanClient()  # no api key
        responses.add(
            responses.POST,
            f"{BASE}/bookings",
            json={"success": False, "error": "Authentication required"},
            status=401,
        )
        with pytest.raises(RentAHumanError) as exc:
            client.create_booking(BookingCreate(
                humanId="h1",
                taskTitle="test",
                startTime="2026-01-01T00:00:00Z",
                estimatedHours=1,
            ))
        assert exc.value.status_code == 401


# ── Model Tests ───────────────────────────────────────────────


class TestModels:

    def test_human_summary(self):
        from rentahuman.models import Human
        h = Human.model_validate(MOCK_HUMANS[0])
        s = h.summary()
        assert "Alice" in s
        assert "human_test_001" in s
        assert "$45.0/hr" in s
        assert "Packages" in s
