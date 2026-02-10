"""rentahuman — Python SDK + framework integrations for rentahuman.ai"""

__version__ = "0.2.0"

from rentahuman.client import RentAHumanClient

try:
    from rentahuman.async_client import AsyncRentAHumanClient
except ImportError:
    # httpx not installed — async client unavailable
    AsyncRentAHumanClient = None  # type: ignore[assignment,misc]

__all__ = ["RentAHumanClient", "AsyncRentAHumanClient"]
