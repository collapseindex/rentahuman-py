"""Tests for LangChain integration."""

import responses

from .conftest import BASE, MOCK_APPLICATIONS, MOCK_BOUNTY, MOCK_HUMANS

from rentahuman.integrations.langchain import (
    RentAHumanToolkit,
    SearchHumansTool,
    CreateBountyTool,
    GetBountyApplicationsTool,
)


# ── Toolkit ───────────────────────────────────────────────────


class TestToolkit:

    def test_get_all_tools(self):
        toolkit = RentAHumanToolkit(api_key="rah_test")
        tools = toolkit.get_tools()
        assert len(tools) == 15

        names = [t.name for t in tools]
        assert "search_humans" in names
        assert "create_booking" in names
        assert "create_bounty" in names
        assert "start_conversation" in names

    def test_get_search_tools(self):
        toolkit = RentAHumanToolkit()
        tools = toolkit.get_search_tools()
        assert len(tools) == 4
        names = [t.name for t in tools]
        assert "search_humans" in names
        assert "get_human_profile" in names

    def test_get_bounty_tools(self):
        toolkit = RentAHumanToolkit(api_key="rah_test")
        tools = toolkit.get_bounty_tools()
        assert len(tools) == 4


# ── Tool Execution ────────────────────────────────────────────


class TestToolExecution:

    @responses.activate
    def test_search_humans_tool(self):
        responses.add(
            responses.GET,
            f"{BASE}/humans",
            json={"success": True, "humans": MOCK_HUMANS, "count": 2},
            status=200,
        )
        toolkit = RentAHumanToolkit()
        tool = toolkit.get_search_tools()[0]  # SearchHumansTool
        assert tool.name == "search_humans"

        result = tool.invoke({"skill": "Photography", "limit": 5})
        assert "Found 2 human(s)" in result
        assert "Alice" in result
        assert "Bob" in result

    @responses.activate
    def test_search_no_results(self):
        responses.add(
            responses.GET,
            f"{BASE}/humans",
            json={"success": True, "humans": [], "count": 0},
            status=200,
        )
        toolkit = RentAHumanToolkit()
        tool = toolkit.get_search_tools()[0]
        result = tool.invoke({"skill": "Underwater Basket Weaving"})
        assert "No humans found" in result

    @responses.activate
    def test_create_bounty_tool(self):
        responses.add(
            responses.POST,
            f"{BASE}/bounties",
            json={"success": True, "bounty": MOCK_BOUNTY},
            status=200,
        )
        toolkit = RentAHumanToolkit(api_key="rah_test")
        tools = toolkit.get_bounty_tools()
        create_tool = [t for t in tools if t.name == "create_bounty"][0]

        result = create_tool.invoke({
            "title": "Photograph storefront",
            "description": "Take 5 photos of 123 Broadway.",
            "price": 50.0,
        })
        assert "Bounty posted!" in result
        assert "bounty_001" in result

    @responses.activate
    def test_get_applications_tool(self):
        responses.add(
            responses.GET,
            f"{BASE}/bounties/bounty_001/applications",
            json={"success": True, "applications": MOCK_APPLICATIONS},
            status=200,
        )
        toolkit = RentAHumanToolkit(api_key="rah_test")
        tools = toolkit.get_bounty_tools()
        apps_tool = [t for t in tools if t.name == "get_bounty_applications"][0]

        result = apps_tool.invoke({"bounty_id": "bounty_001"})
        assert "2 application(s)" in result
        assert "Alice" in result
        assert "Bob" in result


# ── Tool Descriptions ─────────────────────────────────────────


class TestToolDescriptions:
    """Ensure all tools have proper descriptions for LLM consumption."""

    def test_all_tools_have_descriptions(self):
        toolkit = RentAHumanToolkit()
        for tool in toolkit.get_tools():
            assert tool.description, f"{tool.name} missing description"
            assert len(tool.description) > 20, f"{tool.name} description too short"

    def test_all_tools_have_names(self):
        toolkit = RentAHumanToolkit()
        names = [t.name for t in toolkit.get_tools()]
        assert len(names) == len(set(names)), "Duplicate tool names!"
