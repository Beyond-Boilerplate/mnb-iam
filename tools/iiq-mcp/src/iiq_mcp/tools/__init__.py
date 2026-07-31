"""Register all MCP tools (Phase 1 + extended implementations + exclusions)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient
from iiq_mcp.tools import (
    impl_agent_ops,
    impl_coverage,
    impl_custom_apis,
    impl_lifecycle,
    impl_ops_ext,
    impl_scim_catalog,
    phase1_apps,
    phase1_certs,
    phase1_identity,
    phase1_policies,
    phase1_tasks,
    phase1_work_items,
    stubs_catalog,
)


def register_all(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    phase1_identity.register(mcp, client, **ctx)
    phase1_apps.register(mcp, client, **ctx)
    phase1_certs.register(mcp, client, **ctx)
    phase1_policies.register(mcp, client, **ctx)
    phase1_work_items.register(mcp, client, **ctx)
    phase1_tasks.register(mcp, client, **ctx)
    impl_scim_catalog.register(mcp, client, **ctx)
    impl_agent_ops.register(mcp, client, **ctx)
    impl_lifecycle.register(mcp, client, **ctx)
    impl_custom_apis.register(mcp, client, **ctx)
    impl_ops_ext.register(mcp, client, **ctx)
    impl_coverage.register(mcp, client, **ctx)
    stubs_catalog.register(mcp, client, **ctx)
    # Auto-derive implemented name set from registration (no hand-maintained frozenset).
    stubs_catalog.refresh_implemented_from_mcp(mcp)
