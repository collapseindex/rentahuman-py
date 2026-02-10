"""Basic example: search for humans on rentahuman.ai.

No API key needed for read-only operations.
"""

from rentahuman import RentAHumanClient

client = RentAHumanClient()

# Search for humans who can take photos
print("=== Searching for photographers ===")
humans = client.search_humans(skill="Photography", max_rate=60, limit=5)
for h in humans:
    print(f"  {h.summary()}")

# Get detailed profile
if humans:
    print(f"\n=== Profile: {humans[0].name} ===")
    profile = client.get_human(humans[0].id)
    print(f"  Location: {profile.location}")
    print(f"  Rate: ${profile.rate}/hr")
    print(f"  Skills: {', '.join(profile.skills)}")
    print(f"  Bio: {profile.bio}")
