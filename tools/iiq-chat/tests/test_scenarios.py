"""Teller unit tests — normalize, summaries, agent loop, catalog (no static LLM catalog)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

CHAT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAT_ROOT))

from catalog import CATALOG, ToolCatalog, FAVORITE_PRESETS  # noqa: E402
from llm import LlmError, OpenRouterClient, _bad_summary, _local_summary, _skippable_model_error  # noqa: E402
from normalize import normalize_tool_args, resolve_identity_username  # noqa: E402


def _fake_search_factory(payload_by_query: dict):
    def _search(q: str):
        for key, payload in payload_by_query.items():
            if key.lower() in q.lower() or q.lower() in key.lower():
                return payload
        dotted = q.strip().lower().replace(" ", ".")
        return payload_by_query.get(dotted) or {"ok": True, "data": {"items": []}}

    return _search


ANITA_SEARCH = {
    "ok": True,
    "data": {
        "items": [
            {"id": "a1", "userName": "anita.ross", "displayName": "anita.ross"},
            {"id": "a2", "userName": "anita.rao", "displayName": "anita.rao"},
            {"id": "a3", "userName": "anthony.rao", "displayName": "anthony.rao"},
        ]
    },
}

HELEN_SEARCH = {
    "ok": True,
    "data": {
        "items": [
            {"id": "h1", "userName": "Helen Ross", "displayName": "Helen Ross"},
            {"id": "h2", "userName": "helen.ross", "displayName": "helen.ross"},
        ]
    },
}

FAKE_MCP_TOOLS = [
    {
        "name": "search_identities",
        "description": "Search identities by query",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "count": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "search_profiles",
        "description": "Search by HR profile attrs (city, title, dept)",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_identity",
        "description": "Get identity detail",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    {
        "name": "toolkit_ping",
        "description": "Ping toolkit",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def test_no_static_llm_tool_catalog():
    from llm import SYSTEM_PROMPT

    assert "get_identity_accounts" not in SYSTEM_PROMPT
    assert "search_profiles" not in SYSTEM_PROMPT or "Use the provided tools" in SYSTEM_PROMPT
    # No hard-coded routing rules
    assert "For **job title" not in SYSTEM_PROMPT
    assert "For people by workplace" not in SYSTEM_PROMPT


def test_catalog_from_mcp_list():
    cat = ToolCatalog(ttl=300)
    tools = cat.refresh(lambda: FAKE_MCP_TOOLS)
    assert len(tools) == 4
    assert cat.has("search_identities")
    oa = cat.openai_tools()
    names = {t["function"]["name"] for t in oa}
    assert names == {"search_identities", "search_profiles", "get_identity", "toolkit_ping"}
    actions_pub = cat.actions_public()
    assert any(a["tool"] == "toolkit_ping" and a.get("favorite") for a in actions_pub)
    assert any(a["id"] == "search_identities" and a.get("needsArgs") for a in actions_pub)


def test_catalog_equals_mcp_source_of_truth():
    """Rail/openai tools are derived only from the list_fn payload — no side catalog."""
    cat = ToolCatalog(ttl=1)
    cat.refresh(lambda: FAKE_MCP_TOOLS)
    assert cat.names() == {t["name"] for t in FAKE_MCP_TOOLS}
    assert set(a["tool"] for a in cat.actions_public() if not str(a["id"]).startswith("fav:")) == {
        t["name"] for t in FAKE_MCP_TOOLS
    }


def test_normalize_name_alias_to_id_for_access():
    search = _fake_search_factory({"Anita Rao": ANITA_SEARCH, "anita.rao": ANITA_SEARCH})
    out = normalize_tool_args(
        "get_identity_access",
        {"name": "Anita Rao"},
        search_fn=search,
    )
    assert out == {"id": "anita.rao"}


def test_normalize_helen_prefers_dotted():
    search = _fake_search_factory({"Helen Ross": HELEN_SEARCH, "helen.ross": HELEN_SEARCH})
    out = normalize_tool_args(
        "get_identity_access",
        {"name": "Helen Ross"},
        search_fn=search,
    )
    assert out["id"] == "helen.ross"


def test_normalize_search_identities_moves_name_to_query():
    out = normalize_tool_args("search_identities", {"name": "Anita Rao"})
    assert out["query"] == "Anita Rao"
    assert "name" not in out


def test_normalize_unlock_uses_identity_name():
    search = _fake_search_factory({"Anita Rao": ANITA_SEARCH, "anita.rao": ANITA_SEARCH})
    out = normalize_tool_args(
        "unlock_iiq_identity",
        {"name": "Anita Rao"},
        search_fn=search,
    )
    assert out == {"identity_name": "anita.rao"}


def test_resolve_identity_username_anita():
    search = _fake_search_factory({"Anita Rao": ANITA_SEARCH, "anita.rao": ANITA_SEARCH})
    assert resolve_identity_username(search, "Anita Rao") == "anita.rao"


def test_local_summary_uses_profile_hints():
    result = {
        "ok": True,
        "data": {
            "items": [],
            "identity": {"userName": "anita.rao"},
            "profileHints": {"resolvedTitle": "Site Reliability Engineer"},
        },
    }
    text = _local_summary("get_identity_accounts", result, "what is the job title of Anita Rao")
    assert "Site Reliability Engineer" in text
    assert "anita.rao" in text


def test_local_summary_empty_search():
    result = {"ok": True, "data": {"items": [], "totalResults": 0}}
    text = _local_summary("search_identities", result)
    assert "No identities matched" in text


def test_local_summary_profile_search_hits():
    result = {
        "ok": True,
        "data": {
            "matchedVia": "account_profile",
            "totalResults": 1,
            "items": [
                {
                    "userName": "anita.rao",
                    "displayName": "Anita Rao",
                    "profileHints": {
                        "resolvedTitle": "Site Reliability Engineer",
                        "location": "Kathmandu",
                    },
                }
            ],
        },
    }
    text = _local_summary("search_identities", result)
    assert "anita.rao" in text.lower() or "Anita Rao" in text
    assert "Kathmandu" in text or "Site Reliability" in text
    assert "HR profile" in text


def test_skippable_openrouter_model_404():
    assert _skippable_model_error(
        LlmError(
            'OpenRouter HTTP 404: {"error":{"message":"No endpoints found for qwen/qwen3-4b:free."}}'
        )
    )
    assert not _skippable_model_error(LlmError("OpenRouter HTTP 401: User not found"))


def test_bad_summary_rejects_safety_classifier():
    assert _bad_summary("User Safety: safe") is True
    assert _bad_summary("safe") is True
    assert _bad_summary("Anita Rao is a Site Reliability Engineer in Technology Platforms.") is False


def test_agent_loop_who_is_anita_rao():
    """Mock LLM tool_calls: search → get_identity (Anita Rao NL path)."""
    client = OpenRouterClient(api_key="test-key")
    calls: list[tuple[str, dict]] = []

    search_result = {
        "ok": True,
        "data": {
            "items": [{"userName": "anita.rao", "displayName": "Anita Rao", "id": "a2"}],
            "totalResults": 1,
        },
    }
    identity_result = {
        "ok": True,
        "data": {
            "userName": "anita.rao",
            "displayName": "Anita Rao",
            "emails": [{"value": "anita.rao@meridiannb.com"}],
        },
    }

    def call_tool(name: str, args: dict[str, Any]) -> Any:
        calls.append((name, args))
        if name == "search_identities":
            return search_result
        if name == "get_identity":
            return identity_result
        return {"ok": False, "error": f"unexpected {name}"}

    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "id": "1",
                    "type": "function",
                    "function": {
                        "name": "search_identities",
                        "arguments": json.dumps({"query": "Anita Rao", "count": 10}),
                    },
                }
            ],
        },
        {
            "content": "",
            "tool_calls": [
                {
                    "id": "2",
                    "type": "function",
                    "function": {
                        "name": "get_identity",
                        "arguments": json.dumps({"id": "anita.rao"}),
                    },
                }
            ],
        },
        {
            "content": "Anita Rao (anita.rao) is an identity in the Meridian lab.",
            "tool_calls": [],
        },
    ]
    idx = {"i": 0}

    def fake_complete(model, messages, tools=None):
        i = idx["i"]
        idx["i"] += 1
        return responses[min(i, len(responses) - 1)]

    client._complete_message = fake_complete  # type: ignore[method-assign]

    cat = ToolCatalog()
    cat.refresh(lambda: FAKE_MCP_TOOLS)
    outcome = client.run_agent(
        "Who is Anita Rao?",
        cat.openai_tools(),
        call_tool,
        allowed_names=cat.names(),
    )
    assert outcome["ok"]
    assert "Anita Rao" in outcome["reply"]
    assert [c[0] for c in calls] == ["search_identities", "get_identity"]
    assert len(outcome["steps"]) == 2


def test_agent_loop_anyone_named_anita():
    client = OpenRouterClient(api_key="test-key")
    calls: list[str] = []

    def call_tool(name: str, args: dict[str, Any]) -> Any:
        calls.append(name)
        return ANITA_SEARCH

    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "name": "search_identities",
                        "arguments": '{"query":"Anita","count":15}',
                    },
                }
            ],
        },
        {
            "content": "Yes — anita.rao, anita.ross (and anthony.rao matched).",
            "tool_calls": [],
        },
    ]
    idx = {"i": 0}

    def fake_complete(model, messages, tools=None):
        i = idx["i"]
        idx["i"] += 1
        return responses[min(i, len(responses) - 1)]

    client._complete_message = fake_complete  # type: ignore[method-assign]
    cat = ToolCatalog()
    cat.refresh(lambda: FAKE_MCP_TOOLS)
    outcome = client.run_agent("Do I have anyone named Anita?", cat.openai_tools(), call_tool)
    assert outcome["ok"]
    assert calls == ["search_identities"]
    assert "anita" in outcome["reply"].lower()


def test_agent_loop_employees_in_paris():
    client = OpenRouterClient(api_key="test-key")
    calls: list[tuple[str, dict]] = []

    def call_tool(name: str, args: dict[str, Any]) -> Any:
        calls.append((name, args))
        return {
            "ok": True,
            "data": {
                "matchedVia": "account_profile",
                "totalResults": 2,
                "items": [
                    {"userName": "claire.paris", "profileHints": {"location": "Paris"}},
                    {"userName": "marc.dubois", "profileHints": {"location": "Paris"}},
                ],
            },
        }

    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "name": "search_profiles",
                        "arguments": '{"query":"Paris"}',
                    },
                }
            ],
        },
        {
            "content": "Found 2 employees in Paris: claire.paris, marc.dubois.",
            "tool_calls": [],
        },
    ]
    idx = {"i": 0}

    def fake_complete(model, messages, tools=None):
        i = idx["i"]
        idx["i"] += 1
        return responses[min(i, len(responses) - 1)]

    client._complete_message = fake_complete  # type: ignore[method-assign]
    cat = ToolCatalog()
    cat.refresh(lambda: FAKE_MCP_TOOLS)
    outcome = client.run_agent(
        "Find me all employees in Paris",
        cat.openai_tools(),
        call_tool,
    )
    assert outcome["ok"]
    assert calls[0][0] == "search_profiles"
    assert "Paris" in str(calls[0][1].get("query", ""))
    assert "Paris" in outcome["reply"] or "claire" in outcome["reply"].lower()


def test_favorite_presets_are_mcp_names_only():
    for fav in FAVORITE_PRESETS:
        assert "tool" in fav
        assert isinstance(fav["tool"], str)
        assert fav["tool"]  # non-empty MCP tool name
