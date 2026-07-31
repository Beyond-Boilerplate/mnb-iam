"""Catalog completeness and phase gating tests."""

from __future__ import annotations

import asyncio

from iiq_mcp.config import Settings
from iiq_mcp.server import build_server
from iiq_mcp.tools import stubs_catalog
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool
from iiq_mcp.tools.stubs_catalog import (
    all_catalog_names,
    excluded_tool_names,
    load_catalog,
)


def _build():
    settings = Settings(
        IIQ_BASE_URL="http://localhost:8080/identityiq",
        IIQ_USER="test",
        IIQ_PASSWORD="test",
        IIQ_MCP_ENABLED_PHASES="1",
        MCP_API_KEY="",
    )
    return build_server(settings)


def test_catalog_names_unique() -> None:
    names = [t["name"] for t in load_catalog()]
    assert len(names) == len(set(names))


def test_yaml_exclusions_not_in_implemented() -> None:
    mcp, client, _ = _build()
    try:
        yaml_names = {t["name"] for t in load_catalog()}
        overlap = yaml_names & stubs_catalog.IMPLEMENTED_TOOL_NAMES
        assert overlap == set()
        assert excluded_tool_names() == yaml_names
    finally:
        asyncio.run(client.aclose())


def test_expected_tools_present() -> None:
    mcp, client, _ = _build()
    try:
        names = all_catalog_names()
        for required in (
            "search_identities",
            "get_identity",
            "list_certifications",
            "list_policy_violations",
            "list_work_items",
            "get_task_result",
            "run_task_now",
            "search_audit_events",
            "complete_work_item",
            "submit_batch_request",
            "search_roles",
            "create_access_request",
            "reset_password",
            "create_application",
            "onboard_application",
            "run_jml_event",
            "create_certification_campaign",
            "create_sod_policy",
            "reset_target_password",
            "get_executive_digest",
            "list_uiapi_gaps",
            "toolkit_ping",
            "update_rule_source",
            "grant_capability",
        ):
            assert required in names
    finally:
        asyncio.run(client.aclose())


def test_implemented_count() -> None:
    mcp, client, _ = _build()
    try:
        assert len(stubs_catalog.IMPLEMENTED_TOOL_NAMES) >= 100
        assert len(load_catalog()) == 3
        assert stubs_catalog.PHASE1_IMPLEMENTED_NAMES is stubs_catalog.IMPLEMENTED_TOOL_NAMES
        assert "onboard_application" in stubs_catalog.IMPLEMENTED_TOOL_NAMES
        assert "run_jml_event" in stubs_catalog.IMPLEMENTED_TOOL_NAMES
        assert "create_certification_campaign" in stubs_catalog.IMPLEMENTED_TOOL_NAMES
        assert "assign_identity_scope" in stubs_catalog.IMPLEMENTED_TOOL_NAMES
    finally:
        asyncio.run(client.aclose())


def test_server_registers_all_catalog_tools() -> None:
    mcp, client, _ = _build()
    try:
        tools = asyncio.run(mcp.list_tools())
        registered = {t.name for t in tools}
        missing = all_catalog_names() - registered
        assert not missing, f"Missing tools: {sorted(missing)}"
        assert "search_roles" in registered
        assert "search_audit_events" in registered
        assert "complete_work_item" in registered
        assert "onboard_application" in registered
        for coverage in (
            "run_jml_event",
            "create_certification_campaign",
            "create_sod_policy",
            "reset_target_password",
            "preview_access_request",
            "mine_business_roles",
            "trigger_group_aggregation",
            "classify_entitlements",
            "correlate_account",
            "forward_work_item",
            "get_executive_digest",
            "execute_batch_request",
        ):
            assert coverage in registered, coverage
    finally:
        asyncio.run(client.aclose())


def test_phase_gate_blocks_higher_phase() -> None:
    settings = Settings(IIQ_MCP_ENABLED_PHASES="1")
    meta = ToolMeta(name="create_account", phase=4, risk=Risk.PROVISIONING, implemented=True)

    async def _fn() -> dict:
        return {"ok": True}

    result = asyncio.run(run_tool(meta, {}, _fn, settings=settings))
    assert result["ok"] is False
    assert result["error"]["code"] == "phase_disabled"


def test_excluded_returns_not_implemented() -> None:
    settings = Settings(IIQ_MCP_ENABLED_PHASES="1,2,3,4,99")
    meta = ToolMeta(
        name="update_rule_source",
        phase=99,
        risk=Risk.EXCLUDED,
        implemented=False,
        gap_id=None,
    )
    result = asyncio.run(run_tool(meta, {}, lambda: None, settings=settings))
    assert result["ok"] is False
    assert result["error"]["code"] == "not_implemented"


def test_openapi_index_loaded() -> None:
    from iiq_mcp.client.openapi_index import load_index

    idx = load_index()
    assert idx.get("operation_count", 0) > 0
    assert "scim" in idx.get("surfaces", {})
