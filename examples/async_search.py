"""Async client example — concurrent searches.

Usage:
    pip install rentahuman[async]
    python examples/async_search.py
"""

import asyncio

from rentahuman.async_client import AsyncRentAHumanClient


async def main():
    async with AsyncRentAHumanClient() as client:
        # Run multiple searches concurrently
        photographers, drivers, couriers = await asyncio.gather(
            client.search_humans(skill="Photography", max_rate=60),
            client.search_humans(skill="Driving", max_rate=40),
            client.search_humans(skill="Packages", max_rate=30),
        )

        print(f"Photographers: {len(photographers)}")
        for h in photographers:
            print(f"  - {h.summary()}")

        print(f"\nDrivers: {len(drivers)}")
        for h in drivers:
            print(f"  - {h.summary()}")

        print(f"\nCouriers: {len(couriers)}")
        for h in couriers:
            print(f"  - {h.summary()}")


if __name__ == "__main__":
    asyncio.run(main())
