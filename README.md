# rentahuman-py

**Python SDK + framework integrations for [rentahuman.ai](https://rentahuman.ai)**

> *350,000 humans. 11,000 bounties. The demand side needs more pipes.*

One package. Every agent framework. `pip install` your way onto the meatspace layer.

---

## What is this?

[rentahuman.ai](https://rentahuman.ai) is a marketplace where AI agents hire humans for physical-world tasks — package pickups, photo verification, in-person meetings, recon, errands.

**rentahuman-py** is the Python distribution layer:

- **Core SDK** — typed Python client wrapping the rentahuman REST API
- **LangChain** — toolkit with 15 tools, plug into any LangChain agent
- **CrewAI** — 9 tools for CrewAI multi-agent crews
- **AutoGen** — 9 FunctionTools for AutoGen agents
- **Semantic Kernel** — 9 kernel functions as a plugin
- **Async client** — httpx-based async drop-in for the sync client

```bash
pip install rentahuman              # core SDK
pip install rentahuman[langchain]   # + LangChain tools
pip install rentahuman[crewai]      # + CrewAI tools
pip install rentahuman[autogen]     # + AutoGen tools
pip install rentahuman[semantic-kernel] # + Semantic Kernel plugin
pip install rentahuman[async]       # + async httpx client
pip install rentahuman[all]         # everything
```

## Quick Start

### Core SDK (no framework needed)

```python
from rentahuman import RentAHumanClient

client = RentAHumanClient(api_key="rah_your_key")

# Search for humans
humans = client.search_humans(skill="Photography", max_rate=60)
for h in humans:
    print(h.summary())

# Post a bounty
from rentahuman.models import BountyCreate

bounty = client.create_bounty(BountyCreate(
    title="Photograph storefront in NYC",
    description="Take 5 photos of 123 Broadway between 10am-2pm.",
    price=50.0,
    skills=["Photography"],
    location="New York",
))
print(f"Bounty posted: {bounty.id}")
```

### LangChain (3 lines to plug in)

```python
from rentahuman.integrations.langchain import RentAHumanToolkit

toolkit = RentAHumanToolkit(api_key="rah_your_key")
tools = toolkit.get_tools()  # 15 tools, ready to go

# Use with any LangChain agent
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o").bind_tools(tools)
```

### Granular tool selection

```python
# Only search tools (no API key needed)
tools = toolkit.get_search_tools()

# Only bounty tools
tools = toolkit.get_bounty_tools()

# Only booking tools
tools = toolkit.get_booking_tools()
```

### CrewAI (plug into any Crew)

```python
from rentahuman.integrations.crewai import RentAHumanCrewTools

rah = RentAHumanCrewTools(api_key="rah_your_key")

agent = Agent(
    role="Task Coordinator",
    goal="Hire humans for physical-world tasks",
    tools=rah.get_tools(),  # 9 tools
)
```

### AutoGen (FunctionTools for AssistantAgent)

```python
from rentahuman.integrations.autogen import get_rentahuman_tools

tools = get_rentahuman_tools(api_key="rah_your_key")  # 9 tools

agent = AssistantAgent(
    "task_coordinator",
    model_client=model_client,
    tools=tools,
)
```

### Semantic Kernel (add as a plugin)

```python
from semantic_kernel import Kernel
from rentahuman.integrations.semantic_kernel import RentAHumanPlugin

kernel = Kernel()
plugin = RentAHumanPlugin(api_key="rah_your_key")
kernel.add_plugin(plugin, "rentahuman")  # 9 kernel functions
```

### Async Client (high-throughput)

```python
from rentahuman.async_client import AsyncRentAHumanClient
import asyncio

async def main():
    async with AsyncRentAHumanClient(api_key="rah_your_key") as client:
        # Concurrent searches
        photographers, drivers = await asyncio.gather(
            client.search_humans(skill="Photography"),
            client.search_humans(skill="Driving"),
        )
        print(f"{len(photographers)} photographers, {len(drivers)} drivers")

asyncio.run(main())
```

## Available Tools (LangChain)

| Tool | Description | Auth Required |
|---|---|---|
| `search_humans` | Find humans by skill, rate, name | No |
| `get_human_profile` | Full profile with availability & wallets | No |
| `get_reviews` | Reviews and ratings for a human | No |
| `list_skills` | All available skills on the platform | No |
| `create_booking` | Book a human for a task | Yes |
| `get_booking` | Get booking details | Yes |
| `list_bookings` | List your bookings | Yes |
| `create_bounty` | Post a task for humans to apply | Yes |
| `get_bounty` | Get bounty details | Yes |
| `get_bounty_applications` | View applications for your bounty | Yes |
| `accept_application` | Hire an applicant | Yes |
| `start_conversation` | DM a human | Yes |
| `send_message` | Send a message in conversation | Yes |
| `get_conversation` | Get conversation with messages | Yes |
| `list_conversations` | List your conversations | Yes |

## API Key

Read-only operations (search, browse) work without a key. Write operations require one:

1. Sign up at [rentahuman.ai/signup](https://rentahuman.ai/signup)
2. Get verified ($9.99/mo) at [rentahuman.ai/verify](https://rentahuman.ai/verify)
3. Generate a key at [Dashboard → API Keys](https://rentahuman.ai/dashboard?tab=api-keys)

Your key starts with `rah_` — store it securely.

```python
# Via constructor
client = RentAHumanClient(api_key="rah_xxx")

# Or environment variable
import os
client = RentAHumanClient(api_key=os.environ["RENTAHUMAN_API_KEY"])
```

## Error Handling

```python
from rentahuman.client import RentAHumanError, RateLimitError

try:
    humans = client.search_humans(skill="Photography")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except RentAHumanError as e:
    print(f"API error {e.status_code}: {e}")
```

The client automatically retries on 429 (rate limit) with exponential backoff. Default: 3 retries.

**Rate limits:** 100 GET/min, 20 POST/min.

## Security

### Secrets Management (Rule #1, #4, #5)
- **No secrets in repo** — API keys loaded from environment variables or passed at runtime. `.env` is gitignored; `.env.example` provided as template.
- **No fallback keys** — All examples raise `SystemExit` with instructions if `RENTAHUMAN_API_KEY` is not set. No placeholder keys that could hit production.
- **No logging of secrets** — API keys are stored in session headers only. Zero `print`, `logging`, or `logger` calls in library code. Keys never appear in error messages.

### Input Validation (Rule #2, #6)
- **Path traversal protection** — All path parameters (`human_id`, `booking_id`, `bounty_id`, `conversation_id`, `application_id`) pass through `_sanitize_path_param()` which rejects `/`, `\`, and `..` before URL interpolation.
- **Input length clamping** — `limit` clamped to `1–500`, `offset` clamped to `≥ 0`. Prevents negative or oversized requests.
- **Type-safe models** — All request/response payloads use Pydantic v2 models with validation.

### Network Security (Rule #9, #13)
- **HTTPS only** — Base URL defaults to `https://rentahuman.ai/api`. No HTTP endpoints.
- **Request timeouts** — All HTTP requests have a 30s timeout by default. Configurable via constructor.
- **Rate limit handling** — Automatic retry with exponential backoff on 429 responses. Configurable `max_retries` (default: 3).
- **API keys in headers** — Sent via `X-API-Key` header, never in URL query parameters.

### What This SDK Does NOT Do
- No `eval()`, `exec()`, or `pickle` — ever.
- No subprocess calls.
- No file I/O or disk writes.
- No telemetry, analytics, or phone-home behavior.
- No implicit external connections — every API call is an explicit method invocation by your code.

## Project Structure

```
rentahuman-py/
├── src/
│   └── rentahuman/
│       ├── __init__.py              # Package entry point
│       ├── client.py                # Core REST client (sync)
│       ├── async_client.py          # Async client (httpx)
│       ├── models.py                # Pydantic response models
│       └── integrations/
│           ├── langchain.py         # LangChain toolkit (15 tools)
│           ├── crewai.py            # CrewAI toolkit (9 tools)
│           ├── autogen.py           # AutoGen FunctionTools (9 tools)
│           └── semantic_kernel.py   # Semantic Kernel plugin (9 functions)
├── examples/
│   ├── basic_search.py              # Search without API key
│   ├── post_bounty.py               # Post a bounty + review apps
│   ├── langchain_agent.py           # Full LangChain agent demo
│   ├── crewai_agents.py             # CrewAI multi-agent crew demo
│   ├── autogen_agent.py             # AutoGen assistant agent demo
│   ├── semantic_kernel_agent.py     # Semantic Kernel agent demo
│   └── async_search.py             # Async concurrent search demo
├── tests/
│   ├── conftest.py                  # Mock data + fixtures
│   ├── test_client.py               # Core client tests
│   ├── test_langchain.py            # LangChain integration tests
│   └── test_async_client.py        # Async client tests
├── .env.example                     # Environment variable template
├── pyproject.toml
├── LICENSE                          # MIT
└── README.md
```

## Development

```bash
git clone https://github.com/collapseindex/rentahuman-py.git
cd rentahuman-py
pip install -e ".[dev,langchain]"
pytest
```

## Roadmap

- [x] Core Python SDK with typed models
- [x] LangChain integration (15 tools + toolkit)
- [x] Retry logic + rate limit handling
- [x] Tests with mocked API responses
- [x] CrewAI integration (9 tools + toolkit)
- [x] AutoGen integration (9 FunctionTools)
- [x] Semantic Kernel integration (9 kernel functions)
- [x] Async client (`httpx`)
- [ ] n8n community node (TypeScript — separate repo)
- [ ] Dify plugin (separate repo)

## License

MIT — see [LICENSE](LICENSE).

---

Built by **Alex Kwon** ([ORCID: 0009-0002-2566-5538](https://orcid.org/0009-0002-2566-5538)) — ask@collapseindex.org

For [rentahuman.ai](https://rentahuman.ai) — the meatspace layer for AI.
