"""Shared test fixtures."""

import pytest
import responses

from rentahuman import RentAHumanClient

BASE = "https://rentahuman.ai/api"


@pytest.fixture
def mock_api():
    """Activate responses mock for all tests."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def client():
    """Client with a test API key."""
    return RentAHumanClient(api_key="rah_test_key_123")


@pytest.fixture
def anon_client():
    """Client without an API key (read-only)."""
    return RentAHumanClient()


# ── Mock Data ─────────────────────────────────────────────────

MOCK_HUMANS = [
    {
        "id": "human_test_001",
        "name": "Alice",
        "location": "San Francisco",
        "rate": 45.0,
        "skills": ["Packages", "Meetings", "Errands"],
        "bio": "Reliable SF local. 5 years courier experience.",
        "rating": 4.8,
        "completedTasks": 127,
        "cryptoWallets": [{"chain": "ethereum", "address": "0xabc..."}],
    },
    {
        "id": "human_test_002",
        "name": "Bob",
        "location": "New York",
        "rate": 55.0,
        "skills": ["Photography", "Research", "Food Tasting"],
        "bio": "NYC-based photographer and researcher.",
        "rating": 4.5,
        "completedTasks": 83,
        "cryptoWallets": [{"chain": "solana", "address": "Sol1..."}],
    },
]

MOCK_BOUNTY = {
    "id": "bounty_001",
    "title": "Photograph storefront",
    "description": "Take 5 photos of 123 Broadway.",
    "agentType": "rentahuman-py",
    "estimatedHours": 1.0,
    "priceType": "fixed",
    "price": 50.0,
    "status": "open",
    "applicationCount": 0,
}

MOCK_BOOKING = {
    "id": "booking_001",
    "humanId": "human_test_001",
    "agentId": "rentahuman-py",
    "taskTitle": "Pick up package",
    "status": "pending",
    "startTime": "2026-02-10T14:00:00Z",
    "estimatedHours": 1.5,
}

MOCK_CONVERSATION = {
    "id": "conv_001",
    "humanId": "human_test_001",
    "agentType": "rentahuman-py",
    "subject": "Package pickup",
    "messages": [
        {"id": "msg_001", "conversationId": "conv_001", "sender": "agent", "content": "Hi! Can you pick up a package?"},
        {"id": "msg_002", "conversationId": "conv_001", "sender": "human", "content": "Sure! Where from?"},
    ],
}

MOCK_APPLICATIONS = [
    {
        "id": "app_001",
        "bountyId": "bounty_001",
        "humanId": "human_test_001",
        "humanName": "Alice",
        "message": "I can do this! I'm 2 blocks away.",
        "rate": 45.0,
        "status": "pending",
    },
    {
        "id": "app_002",
        "bountyId": "bounty_001",
        "humanId": "human_test_002",
        "humanName": "Bob",
        "message": "Happy to help with photography.",
        "rate": 55.0,
        "status": "pending",
    },
]
