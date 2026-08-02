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
from enrich import enrich_tool_result  # noqa: E402
from normalize import normalize_tool_args, resolve_identity_username, unwrap_identity_mention  # noqa: E402
from safety import is_write_tool  # noqa: E402


def test_write_tool_classifier():
    assert is_write_tool("trigger_aggregation") is True
    assert is_write_tool("unlock_identity") is True
    assert is_write_tool("disable_account") is True
    assert is_write_tool("list_applications") is False
    assert is_write_tool("get_identity") is False
    assert is_write_tool("search_identities") is False
    assert is_write_tool("count_open_sod_violations") is False
    assert is_write_tool("toolkit_ping") is False


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


def test_unwrap_identity_mention():
    assert unwrap_identity_mention("Christopher Hayes (MNB00002)") == "MNB00002"
    assert unwrap_identity_mention("Anita Rao (anita.rao)") == "anita.rao"
    assert unwrap_identity_mention("anita.rao") == "anita.rao"
    assert unwrap_identity_mention("MNB00002") == "MNB00002"


def test_normalize_mention_manager_for_transitive_reports():
    out = normalize_tool_args(
        "list_transitive_reports",
        {"manager": "Christopher Hayes (MNB00002)"},
    )
    assert out == {"manager": "MNB00002"}


def test_normalize_mention_id_for_get_identity():
    out = normalize_tool_args(
        "get_identity",
        {"id": "Christopher Hayes (MNB00002)"},
    )
    assert out == {"id": "MNB00002"}


def test_enrich_transitive_reports_adds_labels():
    raw = {
        "ok": True,
        "data": {
            "manager": "MNB00002",
            "count": 2,
            "reports": [{"name": "MNB00026", "depth": 1}, {"name": "MNB00068", "depth": 1}],
        },
    }

    def call(tool, args):
        assert tool == "get_identity"
        key = args["id"]
        names = {"MNB00002": "Christopher Hayes", "MNB00026": "Raj Ross", "MNB00068": "Anita Rao"}
        return {"ok": True, "data": {"userName": key, "displayName": names[key]}}

    out = enrich_tool_result("list_transitive_reports", raw, call)
    assert out["data"]["managerLabel"] == "Christopher Hayes (MNB00002)"
    assert out["data"]["reportLabels"] == ["Raj Ross (MNB00026)", "Anita Rao (MNB00068)"]
    assert out["data"]["reports"][0]["displayName"] == "Raj Ross"


def test_enrich_hierarchy_labels():
    raw = {
        "ok": True,
        "data": {
            "directReports": [
                {"userName": "MNB00012", "displayName": "Meera Torres"},
                {"userName": "MNB00068", "displayName": "Anita Rao"},
            ]
        },
    }
    out = enrich_tool_result("get_manager_hierarchy", raw, None)
    assert out["data"]["directReportLabels"] == [
        "Meera Torres (MNB00012)",
        "Anita Rao (MNB00068)",
    ]


def test_enrich_search_items_labels():
    raw = {
        "ok": True,
        "data": {
            "items": [{"userName": "MNB00068", "displayName": "Anita Rao", "active": True}],
        },
    }
    out = enrich_tool_result("search_identities", raw, None)
    assert out["data"]["items"][0]["label"] == "Anita Rao (MNB00068)"
    assert out["data"]["peopleLabels"] == ["Anita Rao (MNB00068)"]


def test_enrich_bare_manager_field():
    raw = {"ok": True, "data": {"items": [{"policy": "SoD-Wire", "identity": "MNB00015"}]}}

    def call(tool, args):
        return {"ok": True, "data": {"userName": "MNB00015", "displayName": "Michael Ross"}}

    out = enrich_tool_result("list_open_sod_violations", raw, call)
    assert out["data"]["items"][0]["identityLabel"] == "Michael Ross (MNB00015)"


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


def test_agent_loop_emits_live_events():
    """on_event should surface status + tool_start/tool_result for SSE UX."""
    from llm import _brief_tool_result, _extract_thought

    assert "shown" in _brief_tool_result(
        {"ok": True, "data": {"items": [{"a": 1}], "totalResults": 3}}
    )
    assert "error" in _brief_tool_result({"ok": False, "error": "boom"})
    assert "look up" in _extract_thought(
        {"content": "I should look up Anita.", "tool_calls": [{"id": "1"}]}
    ).lower()

    client = OpenRouterClient(api_key="test-key")
    events: list[tuple[str, dict]] = []

    def call_tool(name: str, args: dict[str, Any]) -> Any:
        return {
            "ok": True,
            "data": {"items": [{"userName": "anita.rao"}], "totalResults": 1},
        }

    responses = [
        {
            "content": "Searching the directory…",
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "name": "search_identities",
                        "arguments": json.dumps({"query": "Anita", "count": 10}),
                    },
                }
            ],
        },
        {"content": "Found anita.rao.", "tool_calls": []},
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
        "Find Anita",
        cat.openai_tools(),
        call_tool,
        allowed_names=cat.names(),
        on_event=lambda et, payload: events.append((et, payload)),
    )
    assert outcome["ok"]
    kinds = [e[0] for e in events]
    assert "status" in kinds
    assert "thought" in kinds
    assert "tool_start" in kinds
    assert "tool_result" in kinds
    starts = [p for t, p in events if t == "tool_start"]
    assert starts[0]["tool"] == "search_identities"


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
