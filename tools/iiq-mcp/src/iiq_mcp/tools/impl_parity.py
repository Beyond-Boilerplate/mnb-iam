"""Wave B–F MCP tools closing high-ROI UI↔MCP parity gaps (UIAPI-10/16/17/73–90)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.tools.agent_helpers import agent_get, agent_post
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    # —— Workgroups create/delete (UIAPI-10) ——
    meta_cwg = ToolMeta(
        name="create_workgroup",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-10",
    )

    @mcp.tool(
        name=meta_cwg.name,
        description=tool_description(
            meta_cwg,
            "Create or update an IIQ workgroup Identity. Args: name; optional description, display_name.",
        ),
    )
    async def create_workgroup(
        name: str,
        description: str | None = None,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name}
            if description:
                body["description"] = description
            if display_name:
                body["displayName"] = display_name
            return await agent_post(client, "/workgroups", json_body=body)

        return await run_tool(
            meta_cwg,
            {"name": name, "description": description, "display_name": display_name},
            _run,
            audit=audit,
        )

    meta_dwg = ToolMeta(
        name="delete_workgroup",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-10",
    )

    @mcp.tool(
        name=meta_dwg.name,
        description=tool_description(
            meta_dwg, "Delete a workgroup by name (advancedOpsEnabled)."
        ),
    )
    async def delete_workgroup(name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/workgroups/{encode_path_segment(name)}/delete"
            )

        return await run_tool(meta_dwg, {"name": name}, _run, audit=audit)

    # —— QuickLinks (UIAPI-16) ——
    meta_cql = ToolMeta(
        name="create_quicklink",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-16",
    )

    @mcp.tool(
        name=meta_cql.name,
        description=tool_description(
            meta_cql,
            "Create/update a QuickLink. Args: name; optional message_key, action, category, "
            "url, workflow_name, hidden, description.",
        ),
    )
    async def create_quicklink(
        name: str,
        message_key: str | None = None,
        action: str | None = None,
        category: str | None = None,
        url: str | None = None,
        workflow_name: str | None = None,
        hidden: bool | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name}
            if message_key:
                body["messageKey"] = message_key
            if action:
                body["action"] = action
            if category:
                body["category"] = category
            if url:
                body["url"] = url
            if workflow_name:
                body["workflowName"] = workflow_name
            if hidden is not None:
                body["hidden"] = hidden
            if description:
                body["description"] = description
            return await agent_post(client, "/quicklinks", json_body=body)

        return await run_tool(
            meta_cql,
            {
                "name": name,
                "message_key": message_key,
                "action": action,
                "category": category,
                "url": url,
                "workflow_name": workflow_name,
                "hidden": hidden,
            },
            _run,
            audit=audit,
        )

    meta_dql = ToolMeta(
        name="delete_quicklink",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-16",
    )

    @mcp.tool(
        name=meta_dql.name,
        description=tool_description(meta_dql, "Delete a QuickLink by name."),
    )
    async def delete_quicklink(name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/quicklinks/{encode_path_segment(name)}/delete"
            )

        return await run_tool(meta_dql, {"name": name}, _run, audit=audit)

    # —— Email templates (UIAPI-17) ——
    meta_uet = ToolMeta(
        name="update_email_template",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-17",
    )

    @mcp.tool(
        name=meta_uet.name,
        description=tool_description(
            meta_uet,
            "Create/update EmailTemplate subject/body/from/to/cc. Args: name; optional subject, "
            "body, from_addr, to, cc, description.",
        ),
    )
    async def update_email_template(
        name: str,
        subject: str | None = None,
        body: str | None = None,
        from_addr: str | None = None,
        to: str | None = None,
        cc: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            payload: dict[str, Any] = {}
            if subject is not None:
                payload["subject"] = subject
            if body is not None:
                payload["body"] = body
            if from_addr is not None:
                payload["from"] = from_addr
            if to is not None:
                payload["to"] = to
            if cc is not None:
                payload["cc"] = cc
            if description is not None:
                payload["description"] = description
            return await agent_post(
                client,
                f"/emailTemplates/{encode_path_segment(name)}",
                json_body=payload,
            )

        return await run_tool(
            meta_uet,
            {"name": name, "subject": subject, "body_set": body is not None},
            _run,
            audit=audit,
        )

    # —— Schema apply (UIAPI-73) ——
    meta_schema = ToolMeta(
        name="apply_application_schema",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-73",
    )

    @mcp.tool(
        name=meta_schema.name,
        description=tool_description(
            meta_schema,
            "Apply account schema identity/display attributes (and optional attribute list) "
            "to an Application. Args: application; optional identity_attribute, display_attribute, attributes.",
        ),
    )
    async def apply_application_schema(
        application: str,
        identity_attribute: str | None = None,
        display_attribute: str | None = None,
        attributes: list[Any] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if identity_attribute:
                body["identityAttribute"] = identity_attribute
            if display_attribute:
                body["displayAttribute"] = display_attribute
            if attributes:
                body["attributes"] = attributes
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(application)}/schema/apply",
                json_body=body,
            )

        return await run_tool(
            meta_schema,
            {
                "application": application,
                "identity_attribute": identity_attribute,
                "display_attribute": display_attribute,
                "attributes": attributes,
            },
            _run,
            audit=audit,
        )

    # —— Correlation config (UIAPI-74) ——
    meta_corr = ToolMeta(
        name="update_correlation_config",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-74",
    )

    @mcp.tool(
        name=meta_corr.name,
        description=tool_description(
            meta_corr,
            "Create/attach CorrelationConfig mapping accountAttribute→identityAttribute on an Application.",
        ),
    )
    async def update_correlation_config(
        application: str,
        account_attribute: str,
        identity_attribute: str,
        name: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {
                "accountAttribute": account_attribute,
                "identityAttribute": identity_attribute,
            }
            if name:
                body["name"] = name
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(application)}/correlationConfig",
                json_body=body,
            )

        return await run_tool(
            meta_corr,
            {
                "application": application,
                "account_attribute": account_attribute,
                "identity_attribute": identity_attribute,
                "name": name,
            },
            _run,
            audit=audit,
        )

    # —— Provisioning cancel (UIAPI-75) ——
    meta_cancel = ToolMeta(
        name="cancel_provisioning_transaction",
        phase=3,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-75",
    )

    @mcp.tool(
        name=meta_cancel.name,
        description=tool_description(
            meta_cancel,
            "Cancel/mark-failed a ProvisioningTransaction by id.",
        ),
    )
    async def cancel_provisioning_transaction(id: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/provisioning/{encode_path_segment(id)}/cancel"
            )

        return await run_tool(meta_cancel, {"id": id}, _run, audit=audit)

    # —— Lifecycle events (UIAPI-76) ——
    meta_lle = ToolMeta(
        name="list_lifecycle_events",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-76",
    )

    @mcp.tool(
        name=meta_lle.name,
        description=tool_description(
            meta_lle, "List IdentityTrigger lifecycle events. Optional limit."
        ),
    )
    async def list_lifecycle_events(limit: int | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            params = {"limit": limit} if limit is not None else None
            return await agent_get(client, "/lifecycleEvents", params=params)

        return await run_tool(meta_lle, {"limit": limit}, _run, audit=audit)

    meta_ule = ToolMeta(
        name="upsert_lifecycle_event",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-76",
    )

    @mcp.tool(
        name=meta_ule.name,
        description=tool_description(
            meta_ule,
            "Create/update IdentityTrigger. Args: name; optional type, workflow_name, "
            "attribute_name, description.",
        ),
    )
    async def upsert_lifecycle_event(
        name: str,
        type: str = "Create",
        workflow_name: str | None = None,
        attribute_name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name, "type": type}
            if workflow_name:
                body["workflowName"] = workflow_name
            if attribute_name:
                body["attributeName"] = attribute_name
            if description:
                body["description"] = description
            return await agent_post(client, "/lifecycleEvents", json_body=body)

        return await run_tool(
            meta_ule,
            {
                "name": name,
                "type": type,
                "workflow_name": workflow_name,
                "attribute_name": attribute_name,
            },
            _run,
            audit=audit,
        )

    # —— ObjectConfig (UIAPI-77) ——
    meta_oc = ToolMeta(
        name="patch_object_config_attribute",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-77",
    )

    @mcp.tool(
        name=meta_oc.name,
        description=tool_description(
            meta_oc,
            "Patch ObjectConfig attribute (e.g. Identity). Args: object_config, attribute; "
            "optional searchable, extended_number, display_name, named_column.",
        ),
    )
    async def patch_object_config_attribute(
        object_config: str,
        attribute: str,
        searchable: bool | None = None,
        extended_number: int | None = None,
        display_name: str | None = None,
        named_column: bool | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"attribute": attribute}
            if searchable is not None:
                body["searchable"] = searchable
            if extended_number is not None:
                body["extendedNumber"] = extended_number
            if display_name is not None:
                body["displayName"] = display_name
            if named_column is not None:
                body["namedColumn"] = named_column
            return await agent_post(
                client,
                f"/objectConfigs/{encode_path_segment(object_config)}/attributes",
                json_body=body,
            )

        return await run_tool(
            meta_oc,
            {
                "object_config": object_config,
                "attribute": attribute,
                "searchable": searchable,
                "extended_number": extended_number,
            },
            _run,
            audit=audit,
        )

    # —— Password policy (UIAPI-78) ——
    meta_pp = ToolMeta(
        name="upsert_password_policy",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-78",
    )

    @mcp.tool(
        name=meta_pp.name,
        description=tool_description(
            meta_pp,
            "Create/update PasswordPolicy. Args: name; optional description, constraints map.",
        ),
    )
    async def upsert_password_policy(
        name: str,
        description: str | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name}
            if description:
                body["description"] = description
            if constraints:
                body["constraints"] = constraints
            return await agent_post(client, "/passwordPolicies", json_body=body)

        return await run_tool(
            meta_pp,
            {"name": name, "description": description, "constraints": constraints},
            _run,
            audit=audit,
        )

    # —— Role requirements (UIAPI-79) ——
    meta_rr = ToolMeta(
        name="set_role_requirements",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-79",
    )

    @mcp.tool(
        name=meta_rr.name,
        description=tool_description(
            meta_rr,
            "Add/remove required roles on a business/IT Bundle. Args: role; required_roles list; "
            "optional op=add|remove.",
        ),
    )
    async def set_role_requirements(
        role: str,
        required_roles: list[str],
        op: str = "add",
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/roles/{encode_path_segment(role)}/requirements",
                json_body={"op": op, "requiredRoles": required_roles},
            )

        return await run_tool(
            meta_rr,
            {"role": role, "required_roles": required_roles, "op": op},
            _run,
            audit=audit,
        )

    # —— SoD constraints (UIAPI-80) ——
    meta_sodc = ToolMeta(
        name="update_sod_constraints",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-80",
    )

    @mcp.tool(
        name=meta_sodc.name,
        description=tool_description(
            meta_sodc,
            "Add left/right role bundles to an SoD Policy constraint. Args: policy; "
            "optional constraint_name, left_roles, right_roles.",
        ),
    )
    async def update_sod_constraints(
        policy: str,
        left_roles: list[str] | None = None,
        right_roles: list[str] | None = None,
        constraint_name: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if constraint_name:
                body["constraintName"] = constraint_name
            if left_roles:
                body["leftRoles"] = left_roles
            if right_roles:
                body["rightRoles"] = right_roles
            return await agent_post(
                client,
                f"/policies/sod/{encode_path_segment(policy)}/constraints",
                json_body=body,
            )

        return await run_tool(
            meta_sodc,
            {
                "policy": policy,
                "left_roles": left_roles,
                "right_roles": right_roles,
                "constraint_name": constraint_name,
            },
            _run,
            audit=audit,
        )

    # —— Provisioning policies (UIAPI-81) ——
    meta_lpp = ToolMeta(
        name="list_provisioning_policies",
        phase=3,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-81",
    )

    @mcp.tool(
        name=meta_lpp.name,
        description=tool_description(
            meta_lpp,
            "List Application provisioning Forms/Templates. Args: application.",
        ),
    )
    async def list_provisioning_policies(application: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(
                client,
                f"/applications/{encode_path_segment(application)}/provisioningPolicies",
            )

        return await run_tool(
            meta_lpp, {"application": application}, _run, audit=audit
        )

    meta_upp = ToolMeta(
        name="upsert_provisioning_policy",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-81",
    )

    @mcp.tool(
        name=meta_upp.name,
        description=tool_description(
            meta_upp,
            "Create/update an Application provisioning Form. Args: application; name; "
            "type (Create|Update|…); optional object_type; fields=[{name,type,required,value,script}].",
        ),
    )
    async def upsert_provisioning_policy(
        application: str,
        name: str,
        type: str = "Create",
        object_type: str = "account",
        fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {
                "name": name,
                "type": type,
                "objectType": object_type,
            }
            if fields is not None:
                body["fields"] = fields
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(application)}/provisioningPolicies",
                json_body=body,
            )

        return await run_tool(
            meta_upp,
            {
                "application": application,
                "name": name,
                "type": type,
                "object_type": object_type,
                "fields": fields,
            },
            _run,
            audit=audit,
        )

    # —— SoD simulate (UIAPI-82) ——
    meta_simsod = ToolMeta(
        name="simulate_sod_policy",
        phase=3,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-82",
    )

    @mcp.tool(
        name=meta_simsod.name,
        description=tool_description(
            meta_simsod,
            "Simulate SoD left/right role conflicts for an identity + proposed roles. "
            "Args: policy; optional identity, proposed_roles, remove_roles.",
        ),
    )
    async def simulate_sod_policy(
        policy: str,
        identity: str | None = None,
        proposed_roles: list[str] | None = None,
        remove_roles: list[str] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if identity:
                body["identity"] = identity
            if proposed_roles:
                body["proposedRoles"] = proposed_roles
            if remove_roles:
                body["removeRoles"] = remove_roles
            return await agent_post(
                client,
                f"/policies/sod/{encode_path_segment(policy)}/simulate",
                json_body=body,
            )

        return await run_tool(
            meta_simsod,
            {
                "policy": policy,
                "identity": identity,
                "proposed_roles": proposed_roles,
                "remove_roles": remove_roles,
            },
            _run,
            audit=audit,
        )

    # —— GroupFactory (UIAPI-83) ——
    meta_ugf = ToolMeta(
        name="upsert_group_factory",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-83",
    )

    @mcp.tool(
        name=meta_ugf.name,
        description=tool_description(
            meta_ugf,
            "Create/update a GroupFactory. Args: name; factory_attribute; optional enabled, description.",
        ),
    )
    async def upsert_group_factory(
        name: str,
        factory_attribute: str,
        enabled: bool = True,
        description: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {
                "name": name,
                "factoryAttribute": factory_attribute,
                "enabled": enabled,
            }
            if description:
                body["description"] = description
            return await agent_post(client, "/groupFactories", json_body=body)

        return await run_tool(
            meta_ugf,
            {
                "name": name,
                "factory_attribute": factory_attribute,
                "enabled": enabled,
                "description": description,
            },
            _run,
            audit=audit,
        )

    meta_rgf = ToolMeta(
        name="run_group_factory",
        phase=3,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-83",
    )

    @mcp.tool(
        name=meta_rgf.name,
        description=tool_description(
            meta_rgf, "Refresh a GroupFactory via Grouper (advancedOpsEnabled)."
        ),
    )
    async def run_group_factory(name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/groupFactories/{encode_path_segment(name)}/run"
            )

        return await run_tool(meta_rgf, {"name": name}, _run, audit=audit)

    # —— Capability rights (UIAPI-84) ——
    meta_scr = ToolMeta(
        name="set_capability_rights",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-84",
    )

    @mcp.tool(
        name=meta_scr.name,
        description=tool_description(
            meta_scr,
            "Set SPRights on a Capability. Args: capability; rights list; optional op=replace|add|remove.",
        ),
    )
    async def set_capability_rights(
        capability: str,
        rights: list[str],
        op: str = "replace",
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/capabilities/{encode_path_segment(capability)}/rights",
                json_body={"rights": rights, "op": op},
            )

        return await run_tool(
            meta_scr,
            {"capability": capability, "rights": rights, "op": op},
            _run,
            audit=audit,
        )

    # —— Role selector (UIAPI-85) ——
    meta_srs = ToolMeta(
        name="set_role_selector",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-85",
    )

    @mcp.tool(
        name=meta_srs.name,
        description=tool_description(
            meta_srs,
            "Set Bundle assignment selector via population, script, or match_terms. "
            "Args: role; optional population, script, match_terms, clear.",
        ),
    )
    async def set_role_selector(
        role: str,
        population: str | None = None,
        script: str | None = None,
        match_terms: list[dict[str, Any]] | None = None,
        clear: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if clear:
                body["clear"] = True
            if population:
                body["population"] = population
            if script:
                body["script"] = script
            if match_terms:
                body["matchTerms"] = match_terms
            return await agent_post(
                client,
                f"/roles/{encode_path_segment(role)}/selector",
                json_body=body,
            )

        return await run_tool(
            meta_srs,
            {
                "role": role,
                "population": population,
                "script": script,
                "match_terms": match_terms,
                "clear": clear,
            },
            _run,
            audit=audit,
        )

    # —— Certification definition (UIAPI-86) ——
    meta_ucd = ToolMeta(
        name="update_certification_definition",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-86",
    )

    @mcp.tool(
        name=meta_ucd.name,
        description=tool_description(
            meta_ucd,
            "Patch CertificationDefinition fields (description, owner, certifiers, name_template, type).",
        ),
    )
    async def update_certification_definition(
        name: str,
        description: str | None = None,
        owner: str | None = None,
        certifiers: list[str] | None = None,
        name_template: str | None = None,
        type: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if description is not None:
                body["description"] = description
            if owner is not None:
                body["owner"] = owner
            if certifiers is not None:
                body["certifiers"] = certifiers
            if name_template is not None:
                body["nameTemplate"] = name_template
            if type is not None:
                body["type"] = type
            return await agent_post(
                client,
                f"/certifications/definitions/{encode_path_segment(name)}",
                json_body=body,
            )

        return await run_tool(
            meta_ucd,
            {
                "name": name,
                "description": description,
                "owner": owner,
                "certifiers": certifiers,
                "name_template": name_template,
                "type": type,
            },
            _run,
            audit=audit,
        )

    # —— Identity forwarding / OOO (UIAPI-87) ——
    meta_fwd = ToolMeta(
        name="set_identity_forwarding",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-87",
    )

    @mcp.tool(
        name=meta_fwd.name,
        description=tool_description(
            meta_fwd,
            "Set or clear identity work-item forwarding (OOO). Args: identity; "
            "forward_to; optional start_date, end_date; or clear=true.",
        ),
    )
    async def set_identity_forwarding(
        identity: str,
        forward_to: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        clear: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if clear:
                body["clear"] = True
            if forward_to:
                body["forwardTo"] = forward_to
            if start_date:
                body["startDate"] = start_date
            if end_date:
                body["endDate"] = end_date
            return await agent_post(
                client,
                f"/identities/{encode_path_segment(identity)}/forwarding",
                json_body=body,
            )

        return await run_tool(
            meta_fwd,
            {
                "identity": identity,
                "forward_to": forward_to,
                "start_date": start_date,
                "end_date": end_date,
                "clear": clear,
            },
            _run,
            audit=audit,
        )

    # —— Risk score config (UIAPI-88) ——
    meta_rsc = ToolMeta(
        name="update_risk_score_config",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-88",
    )

    @mcp.tool(
        name=meta_rsc.name,
        description=tool_description(
            meta_rsc,
            "Patch ScoreConfig identity score weights. Args: identity_scores=[{name,weight}] "
            "or score+weight; optional maximum_score.",
        ),
    )
    async def update_risk_score_config(
        identity_scores: list[dict[str, Any]] | None = None,
        score: str | None = None,
        weight: int | None = None,
        maximum_score: int | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if identity_scores is not None:
                body["identityScores"] = identity_scores
            if score is not None:
                body["score"] = score
            if weight is not None:
                body["weight"] = weight
            if maximum_score is not None:
                body["maximumScore"] = maximum_score
            return await agent_post(client, "/risk/scoreConfig", json_body=body)

        return await run_tool(
            meta_rsc,
            {
                "identity_scores": identity_scores,
                "score": score,
                "weight": weight,
                "maximum_score": maximum_score,
            },
            _run,
            audit=audit,
        )

    # —— TaskDefinition (UIAPI-89) ——
    meta_utd = ToolMeta(
        name="upsert_task_definition",
        phase=4,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-89",
    )

    @mcp.tool(
        name=meta_utd.name,
        description=tool_description(
            meta_utd,
            "Create/update TaskDefinition by cloning a template. Args: name; optional template, "
            "description, arguments map.",
        ),
    )
    async def upsert_task_definition(
        name: str,
        template: str | None = None,
        description: str | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name}
            if template:
                body["template"] = template
            if description:
                body["description"] = description
            if arguments is not None:
                body["arguments"] = arguments
            return await agent_post(client, "/taskDefinitions", json_body=body)

        return await run_tool(
            meta_utd,
            {
                "name": name,
                "template": template,
                "description": description,
                "arguments": arguments,
            },
            _run,
            audit=audit,
        )

    # —— Stop aggregation (UIAPI-90) ——
    meta_stop = ToolMeta(
        name="stop_aggregation",
        phase=3,
        risk=Risk.ADMIN,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-90",
    )

    @mcp.tool(
        name=meta_stop.name,
        description=tool_description(
            meta_stop,
            "Terminate a running aggregation TaskResult. Args: task_result_id or application "
            "(+ optional task_name_contains).",
        ),
    )
    async def stop_aggregation(
        task_result_id: str | None = None,
        application: str | None = None,
        task_name_contains: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if task_result_id:
                body["taskResultId"] = task_result_id
            if application:
                body["application"] = application
            if task_name_contains:
                body["taskNameContains"] = task_name_contains
            return await agent_post(client, "/connectors/aggregate/stop", json_body=body)

        return await run_tool(
            meta_stop,
            {
                "task_result_id": task_result_id,
                "application": application,
                "task_name_contains": task_name_contains,
            },
            _run,
            audit=audit,
        )
