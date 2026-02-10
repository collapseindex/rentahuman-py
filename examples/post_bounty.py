"""Example: post a bounty and review applications.

Requires an API key for write operations.

Usage:
    export RENTAHUMAN_API_KEY=rah_your_key
    python examples/post_bounty.py
"""

import os
import sys

from rentahuman import RentAHumanClient
from rentahuman.models import BountyCreate

api_key = os.environ.get("RENTAHUMAN_API_KEY")
if not api_key:
    print("Set RENTAHUMAN_API_KEY environment variable.")
    print("Get one at: https://rentahuman.ai/dashboard?tab=api-keys")
    sys.exit(1)

client = RentAHumanClient(api_key=api_key)

# Post a bounty
print("=== Posting bounty ===")
bounty = client.create_bounty(BountyCreate(
    title="Photograph a storefront in Manhattan",
    description=(
        "Take 5 high-resolution photos of the storefront at 123 Broadway, NYC. "
        "Include: front entrance, signage, window displays, and street view. "
        "Photos should be taken between 10am-2pm for best lighting."
    ),
    price=50.0,
    estimatedHours=1.0,
    skills=["Photography"],
    location="New York",
))
print(f"  Bounty posted: {bounty.id}")
print(f"  Title: {bounty.title}")
print(f"  Price: ${bounty.price}")

# Later: check applications
print(f"\n=== Applications for {bounty.id} ===")
apps = client.get_bounty_applications(bounty.id)
for app in apps:
    print(f"  {app.human_name} - ${app.rate}/hr - {app.message}")

# Accept the best one
if apps:
    best = apps[0]
    print(f"\n=== Accepting: {best.human_name} ===")
    client.accept_application(bounty.id, best.id)
    print("  Done!")
