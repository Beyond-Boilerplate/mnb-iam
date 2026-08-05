"""High-ROI Custom API MCP tools (UIAPI-97/98/105–107/139)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.tools.agent_helpers import agent_get, agent_post
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    # —— UIAPI-97 Workflow ——
    meta_lw = ToolMeta(
        name="list_workflows",
        phase=2,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-97",
    )

    @mcp.tool(
        name=meta_lw.name,
        description=tool_description(
            meta_lw, "List Workflow definitions (name, step count). Args: limit?"
        ),
    )
    async def list_workflows(limit: int | None = 50) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, "/workflows", params={"limit": limit})

        return await run_tool(meta_lw, {"limit": limit}, _run, audit=audit)

    meta_gw = ToolMeta(
        name="get_workflow",
        phase=2,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-97",
    )

    @mcp.tool(
        name=meta_gw.name,
        description=tool_description(
            meta_gw, "Get Workflow detail including stepNames and variables. Args: name."
        ),
    )
    async def get_workflow(name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(client, f"/workflows/{encode_path_segment(name)}")

        return await run_tool(meta_gw, {"name": name}, _run, audit=audit)

    meta_pw = ToolMeta(
        name="patch_workflow",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-97",
    )

    @mcp.tool(
        name=meta_pw.name,
        description=tool_description(
            meta_pw,
            "Patch Workflow description/variables and optional named step "
            "(stepAction/stepCondition/stepArgs). Not a visual designer. Args: name; "
            "optional description, variables{}, step_name, step_action, step_condition, "
            "step_description, step_args{}.",
        ),
    )
    async def patch_workflow(
        name: str,
        description: str | None = None,
        variables: dict[str, Any] | None = None,
        step_name: str | None = None,
        step_action: str | None = None,
        step_condition: str | None = None,
        step_description: str | None = None,
        step_args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if description:
                body["description"] = description
            if variables:
                body["variables"] = variables
            if step_name:
                body["stepName"] = step_name
            if step_action:
                body["stepAction"] = step_action
            if step_condition:
                body["stepCondition"] = step_condition
            if step_description:
                body["stepDescription"] = step_description
            if step_args:
                body["stepArgs"] = step_args
            return await agent_post(
                client, f"/workflows/{encode_path_segment(name)}/patch", json_body=body
            )

        return await run_tool(
            meta_pw,
            {
                "name": name,
                "description": description,
                "variables": variables,
                "step_name": step_name,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-98 Form upsert ——
    meta_uf = ToolMeta(
        name="upsert_form",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-98",
    )

    @mcp.tool(
        name=meta_uf.name,
        description=tool_description(
            meta_uf,
            "Create or update a top-level Form. Args: name; optional description, "
            "fields[{name,type,required,value,script,displayName}].",
        ),
    )
    async def upsert_form(
        name: str,
        description: str | None = None,
        fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name}
            if description:
                body["description"] = description
            if fields is not None:
                body["fields"] = fields
            return await agent_post(client, "/forms", json_body=body)

        return await run_tool(
            meta_uf, {"name": name, "description": description, "fields": fields}, _run, audit=audit
        )

    # —— UIAPI-139 SoD matrix ——
    meta_im = ToolMeta(
        name="import_sod_matrix",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-139",
    )

    @mcp.tool(
        name=meta_im.name,
        description=tool_description(
            meta_im,
            "Import SoD left/right role pairs into policies. Args: rows[{left,right,policy?,"
            "constraint?}] and/or csv; optional policy_name default, dry_run, replace_constraints.",
        ),
    )
    async def import_sod_matrix(
        rows: list[dict[str, Any]] | None = None,
        csv: str | None = None,
        policy_name: str | None = None,
        dry_run: bool = False,
        replace_constraints: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {
                "dryRun": dry_run,
                "replaceConstraints": replace_constraints,
            }
            if rows is not None:
                body["rows"] = rows
            if csv:
                body["csv"] = csv
            if policy_name:
                body["policyName"] = policy_name
            return await agent_post(client, "/policies/sod/matrix/import", json_body=body)

        return await run_tool(
            meta_im,
            {
                "rows": rows,
                "csv": csv,
                "policy_name": policy_name,
                "dry_run": dry_run,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-105/106/107 connector deep config ——
    meta_ad = ToolMeta(
        name="configure_ad_connector",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-105",
    )

    @mcp.tool(
        name=meta_ad.name,
        description=tool_description(
            meta_ad,
            "Set AD/IQService connector attributes on an Application. Args: name; optional "
            "IQServiceHost/Port/User/Password, forest, domain, host, user, password, useSSL, "
            "searchDNs, or attributes{}.",
        ),
    )
    async def configure_ad_connector(
        name: str,
        attributes: dict[str, Any] | None = None,
        iq_service_host: str | None = None,
        iq_service_port: str | None = None,
        forest: str | None = None,
        domain: str | None = None,
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if attributes:
                body["attributes"] = attributes
            if iq_service_host:
                body["IQServiceHost"] = iq_service_host
            if iq_service_port:
                body["IQServicePort"] = iq_service_port
            if forest:
                body["forest"] = forest
            if domain:
                body["domain"] = domain
            if host:
                body["host"] = host
            if user:
                body["user"] = user
            if password:
                body["password"] = password
            return await agent_post(
                client, f"/applications/{encode_path_segment(name)}/connector/ad", json_body=body
            )

        return await run_tool(meta_ad, {"name": name, "attributes": attributes}, _run, audit=audit)

    meta_jdbc = ToolMeta(
        name="configure_jdbc_connector",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-106",
    )

    @mcp.tool(
        name=meta_jdbc.name,
        description=tool_description(
            meta_jdbc,
            "Set JDBC connector attributes / SQL maps. Args: name; optional url, driver_class, "
            "user, password, sql_map{}, attributes{}.",
        ),
    )
    async def configure_jdbc_connector(
        name: str,
        attributes: dict[str, Any] | None = None,
        url: str | None = None,
        driver_class: str | None = None,
        user: str | None = None,
        password: str | None = None,
        sql_map: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if attributes:
                body["attributes"] = attributes
            if url:
                body["url"] = url
            if driver_class:
                body["driverClass"] = driver_class
            if user:
                body["user"] = user
            if password:
                body["password"] = password
            if sql_map:
                body["sqlMap"] = sql_map
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(name)}/connector/jdbc",
                json_body=body,
            )

        return await run_tool(meta_jdbc, {"name": name, "url": url}, _run, audit=audit)

    meta_oa = ToolMeta(
        name="configure_oauth_connector",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-107",
    )

    @mcp.tool(
        name=meta_oa.name,
        description=tool_description(
            meta_oa,
            "Set OAuth/SCIM connector attributes (token dance still external). Args: name; "
            "optional token_url, client_id, client_secret, grant_type, scope, scim_base_url, "
            "base_url, attributes{}.",
        ),
    )
    async def configure_oauth_connector(
        name: str,
        attributes: dict[str, Any] | None = None,
        token_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        grant_type: str | None = None,
        scope: str | None = None,
        scim_base_url: str | None = None,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if attributes:
                body["attributes"] = attributes
            if token_url:
                body["tokenUrl"] = token_url
            if client_id:
                body["clientId"] = client_id
            if client_secret:
                body["clientSecret"] = client_secret
            if grant_type:
                body["grantType"] = grant_type
            if scope:
                body["scope"] = scope
            if scim_base_url:
                body["scimBaseUrl"] = scim_base_url
            if base_url:
                body["baseUrl"] = base_url
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(name)}/connector/oauth",
                json_body=body,
            )

        return await run_tool(meta_oa, {"name": name, "token_url": token_url}, _run, audit=audit)
