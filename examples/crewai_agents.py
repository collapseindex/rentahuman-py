"""Example: CrewAI agents that hire humans for a verification task.

Requires:
    pip install rentahuman[crewai]

Creates a Crew with a researcher + coordinator that autonomously
find and hire humans for real-world tasks.
"""

import os

from crewai import Agent, Crew, Task

from rentahuman.integrations.crewai import RentAHumanCrewTools

# ── Setup ─────────────────────────────────────────────────────

api_key = os.environ.get("RENTAHUMAN_API_KEY")
if not api_key:
    raise SystemExit(
        "Set RENTAHUMAN_API_KEY environment variable. "
        "Get one at https://rentahuman.ai/dashboard?tab=api-keys"
    )

rah = RentAHumanCrewTools(api_key=api_key)

# ── Agents ────────────────────────────────────────────────────

researcher = Agent(
    role="Human Sourcer",
    goal="Find the best available human for a physical-world task",
    backstory="You're an expert at matching tasks to the right people based on skills, location, rate, and reviews.",
    tools=rah.get_search_tools(),
    verbose=True,
)

coordinator = Agent(
    role="Task Coordinator",
    goal="Post bounties and manage the hiring process",
    backstory="You handle the logistics of hiring humans — posting tasks, reviewing applications, and confirming hires.",
    tools=rah.get_tools(),
    verbose=True,
)

# ── Tasks ─────────────────────────────────────────────────────

research_task = Task(
    description=(
        "Find humans in San Francisco who can do package delivery. "
        "Budget is $50 max. List the top 3 candidates with their rates and ratings."
    ),
    expected_output="A ranked list of 3 candidates with ID, name, rate, and rating.",
    agent=researcher,
)

hiring_task = Task(
    description=(
        "Post a bounty for package pickup at 123 Market St, delivery to 456 Mission St. "
        "Price: $40 fixed. Required skill: Packages. Location: San Francisco."
    ),
    expected_output="Confirmation that the bounty was posted with its ID.",
    agent=coordinator,
)

# ── Crew ──────────────────────────────────────────────────────

if __name__ == "__main__":
    crew = Crew(
        agents=[researcher, coordinator],
        tasks=[research_task, hiring_task],
        verbose=True,
    )
    result = crew.kickoff()
    print(result)
