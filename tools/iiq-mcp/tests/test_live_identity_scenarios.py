"""Live MCP scenario tests — require IIQ + MCP on localhost.

Run:
  pytest tools/iiq-mcp/tests/test_live_identity_scenarios.py -m integration -q
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


def _mcp_client():
    # Prefer chat client (Bearer-aware) when available
    import sys
    from pathlib import Path

    chat = Path(__file__).resolve().parents[2] / "iiq-chat"
    sys.path.insert(0, str(chat))
    from mcp_client import McpClient

    return McpClient(
        url=os.environ.get("IIQ_MCP_URL", "http://127.0.0.1:8766/mcp"),
        api_key=os.environ.get("MCP_API_KEY", "mnb-lab-mcp-key"),
    )


@pytest.fixture(scope="module")
def mcp():
    client = _mcp_client()
    try:
        client.healthz()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"MCP not reachable: {exc}")
    client.init()
    return client


def _data(msg):
    if isinstance(msg, dict) and "data" in msg:
        return msg["data"]
    return msg


def test_search_spaced_display_name_finds_anita(mcp):
    msg = mcp.call("search_identities", {"query": "Anita Rao", "count": 25})
    data = _data(msg)
    items = data.get("items") or []
    names = {i.get("userName") for i in items}
    assert "anita.rao" in names
    # best match should be first after ranking
    assert items[0]["userName"] == "anita.rao"


def test_get_identity_access_accepts_name_alias(mcp):
    msg = mcp.call("get_identity_access", {"name": "Anita Rao"})
    data = _data(msg)
    assert data.get("userName") == "anita.rao"


def test_get_identity_access_accepts_dotted_id(mcp):
    msg = mcp.call("get_identity_access", {"id": "anita.rao"})
    data = _data(msg)
    assert data.get("userName") == "anita.rao"


def test_get_identity_accounts_profile_hints_title(mcp):
    msg = mcp.call("get_identity_accounts", {"name": "Anita Rao"})
    data = _data(msg)
    hints = data.get("profileHints") or {}
    assert hints.get("resolvedTitle") == "Site Reliability Engineer"
    assert data.get("identity", {}).get("userName") == "anita.rao"


def test_helen_ross_resolves_to_dotted_when_present(mcp):
    msg = mcp.call("search_identities", {"query": "Helen Ross", "count": 25})
    data = _data(msg)
    items = data.get("items") or []
    names = {i.get("userName") for i in items}
    if "helen.ross" not in names:
        pytest.skip("helen.ross not present in this lab")
    assert items[0]["userName"] == "helen.ross"


def test_partial_token_search_finds_people(mcp):
    msg = mcp.call("search_identities", {"query": "anita", "count": 25})
    data = _data(msg)
    names = {i.get("userName") for i in (data.get("items") or [])}
    assert "anita.rao" in names or "anita.ross" in names


def test_search_kathmandu_via_profile_fallback(mcp):
    msg = mcp.call("search_identities", {"query": "Kathmandu", "count": 25})
    data = _data(msg)
    items = data.get("items") or []
    assert items, "expected HR profile fallback for Kathmandu"
    assert data.get("matchedVia") == "account_profile"
    names = {i.get("userName") for i in items}
    assert "anita.rao" in names


def test_search_profiles_kathmandu_nl_phrase(mcp):
    msg = mcp.call(
        "search_profiles",
        {"query": "list all identities from Kathmandu", "count": 25},
    )
    data = _data(msg)
    items = data.get("items") or []
    assert items
    assert any(i.get("userName") == "anita.rao" for i in items)
