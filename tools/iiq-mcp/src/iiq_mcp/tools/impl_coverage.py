"""MCP tools for Teller 300-scenario coverage (UIAPI-30..57).

Wraps ``MnbAgentCoverageResource`` under ``/plugin/rest/mnbToolkit/agent/*``.
Teller discovers these via live ``tools/list`` — no Teller catalog hardcoding.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.tools.agent_helpers import agent_get, agent_post
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    # —— UIAPI-30 JML ——
    meta_jml = ToolMeta(
        name="run_jml_event",
        phase=3,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-30",
    )

    @mcp.tool(
        name=meta_jml.name,
        description=tool_description(
            meta_jml,
            "Launch joiner/mover/leaver/reinstate JML workflow for an identity "
            "(RapidSetup / Lifecycle Event). Args: event, identity; optional manager, reason, dry_run.",
        ),
    )
    async def run_jml_event(
        event: str,
        identity: str,
        manager: str | None = None,
        reason: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"identityName": identity, "dryRun": dry_run}
            if manager:
                body["manager"] = manager
            if reason:
                body["reason"] = reason
            return await agent_post(
                client, f"/jml/{encode_path_segment(event.lower())}", json_body=body
            )

        return await run_tool(
            meta_jml,
            {
                "event": event,
                "identity": identity,
                "manager": manager,
                "reason": reason,
                "dry_run": dry_run,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-31 Cert campaigns ——
    meta_camp = ToolMeta(
        name="create_certification_campaign",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-31",
    )

    @mcp.tool(
        name=meta_camp.name,
        description=tool_description(
            meta_camp,
            "Create a CertificationDefinition campaign from a template; optional generateNow "
            "runs Certification Manager. Args: name; optional template, description, generate_now.",
        ),
    )
    async def create_certification_campaign(
        name: str,
        template: str | None = None,
        description: str | None = None,
        generate_now: bool = False,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name, "generateNow": generate_now}
            if template:
                body["template"] = template
            if description:
                body["description"] = description
            return await agent_post(client, "/certifications/campaigns", json_body=body)

        return await run_tool(
            meta_camp,
            {
                "name": name,
                "template": template,
                "description": description,
                "generate_now": generate_now,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-32 SoD ——
    meta_sod = ToolMeta(
        name="create_sod_policy",
        phase=3,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-32",
    )

    @mcp.tool(
        name=meta_sod.name,
        description=tool_description(
            meta_sod,
            "Create or update an SoD Policy (clone from template when present). "
            "Args: name; optional description, template.",
        ),
    )
    async def create_sod_policy(
        name: str, description: str | None = None, template: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name}
            if description:
                body["description"] = description
            if template:
                body["template"] = template
            return await agent_post(client, "/policies/sod", json_body=body)

        return await run_tool(
            meta_sod,
            {"name": name, "description": description, "template": template},
            _run,
            audit=audit,
        )

    # —— UIAPI-33 Target password ——
    meta_tpw = ToolMeta(
        name="reset_target_password",
        phase=3,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-33",
    )

    @mcp.tool(
        name=meta_tpw.name,
        description=tool_description(
            meta_tpw,
            "Set/reset/unlock a target-application account password via LCM. "
            "Args: application, native_identity; optional identity, password, op=set|reset|unlock.",
        ),
    )
    async def reset_target_password(
        application: str,
        native_identity: str,
        identity: str | None = None,
        password: str | None = None,
        op: str = "reset",
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"op": op}
            if identity:
                body["identity"] = identity
            if password:
                body["password"] = password
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(application)}/accounts/"
                f"{encode_path_segment(native_identity)}/password",
                json_body=body,
            )

        return await run_tool(
            meta_tpw,
            {
                "application": application,
                "native_identity": native_identity,
                "identity": identity,
                "op": op,
                "password_set": bool(password),
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-34 Report download ——
    meta_dl = ToolMeta(
        name="download_report_result",
        phase=2,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-34",
    )

    @mcp.tool(
        name=meta_dl.name,
        description=tool_description(
            meta_dl,
            "Fetch TaskResult report attributes/messages for a completed report run.",
        ),
    )
    async def download_report_result(task_result_id: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(
                client, f"/reports/{encode_path_segment(task_result_id)}/download"
            )

        return await run_tool(meta_dl, {"task_result_id": task_result_id}, _run, audit=audit)

    # —— UIAPI-35 Executive digest ——
    meta_exec = ToolMeta(
        name="get_executive_digest",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-35",
    )

    @mcp.tool(
        name=meta_exec.name,
        description=tool_description(
            meta_exec,
            "Rollup counts: open SoD, certifications, apps, identities, open work items, failed tasks.",
        ),
    )
    async def get_executive_digest() -> dict[str, Any]:
        return await run_tool(
            meta_exec, {}, lambda: agent_get(client, "/executive/digest"), audit=audit
        )

    # —— UIAPI-36 Batch execute ——
    meta_batch = ToolMeta(
        name="execute_batch_request",
        phase=3,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-36",
    )

    @mcp.tool(
        name=meta_batch.name,
        description=tool_description(
            meta_batch, "Execute an existing BatchRequest via Batch Request Processing Task."
        ),
    )
    async def execute_batch_request(batch_request_id: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/batchRequests/{encode_path_segment(batch_request_id)}/execute"
            )

        return await run_tool(
            meta_batch, {"batch_request_id": batch_request_id}, _run, audit=audit
        )

    # —— UIAPI-37 Correlate ——
    meta_corr = ToolMeta(
        name="correlate_account",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-37",
    )

    @mcp.tool(
        name=meta_corr.name,
        description=tool_description(
            meta_corr,
            "Correlate an application account (native identity) to an IIQ identity cube.",
        ),
    )
    async def correlate_account(
        application: str, native_identity: str, identity: str
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/accounts/correlate",
                json_body={
                    "application": application,
                    "nativeIdentity": native_identity,
                    "identity": identity,
                },
            )

        return await run_tool(
            meta_corr,
            {
                "application": application,
                "native_identity": native_identity,
                "identity": identity,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-38 Preview access ——
    meta_prev = ToolMeta(
        name="preview_access_request",
        phase=2,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-38",
    )

    @mcp.tool(
        name=meta_prev.name,
        description=tool_description(
            meta_prev,
            "Dry-run preview of an access grant (identity + access name/type) before submit.",
        ),
    )
    async def preview_access_request(
        identity: str,
        access_name: str,
        access_type: str | None = None,
        sunrise: str | None = None,
        sunset: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"identity": identity, "accessName": access_name}
            if access_type:
                body["accessType"] = access_type
            if sunrise:
                body["sunrise"] = sunrise
            if sunset:
                body["sunset"] = sunset
            return await agent_post(client, "/accessRequests/preview", json_body=body)

        return await run_tool(
            meta_prev,
            {
                "identity": identity,
                "access_name": access_name,
                "access_type": access_type,
                "sunrise": sunrise,
                "sunset": sunset,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-39 Role mining ——
    meta_mine = ToolMeta(
        name="mine_business_roles",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-39",
    )

    @mcp.tool(
        name=meta_mine.name,
        description=tool_description(
            meta_mine,
            "Trigger Business Role Mining (or named task). Optional department/application filters.",
        ),
    )
    async def mine_business_roles(
        department: str | None = None,
        application: str | None = None,
        task_name: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if department:
                body["department"] = department
            if application:
                body["application"] = application
            if task_name:
                body["taskName"] = task_name
            return await agent_post(client, "/roles/mine", json_body=body)

        return await run_tool(
            meta_mine,
            {"department": department, "application": application, "task_name": task_name},
            _run,
            audit=audit,
        )

    # —— UIAPI-40 Entitlement classify ——
    meta_cls = ToolMeta(
        name="classify_entitlements",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-40",
    )

    @mcp.tool(
        name=meta_cls.name,
        description=tool_description(
            meta_cls,
            "Classify ManagedAttributes: privileged/requestable/owner filters by application/value.",
        ),
    )
    async def classify_entitlements(
        application: str | None = None,
        value: str | None = None,
        privileged: bool | None = None,
        requestable: bool | None = None,
        owner: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if application:
                body["application"] = application
            if value:
                body["value"] = value
            if privileged is not None:
                body["privileged"] = privileged
            if requestable is not None:
                body["requestable"] = requestable
            if owner:
                body["owner"] = owner
            return await agent_post(client, "/entitlements/classify", json_body=body)

        return await run_tool(
            meta_cls,
            {
                "application": application,
                "value": value,
                "privileged": privileged,
                "requestable": requestable,
                "owner": owner,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-41 Group aggregation ——
    meta_gagg = ToolMeta(
        name="trigger_group_aggregation",
        phase=2,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-41",
    )

    @mcp.tool(
        name=meta_gagg.name,
        description=tool_description(
            meta_gagg, "Run Account Group Aggregation for an application."
        ),
    )
    async def trigger_group_aggregation(application: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/connectors/aggregate/groups",
                json_body={"application": application},
            )

        return await run_tool(meta_gagg, {"application": application}, _run, audit=audit)

    # —— UIAPI-42 Forward WI: registered in impl_agent_ops (agent API) ——

    # —— UIAPI-43 Form submit ——
    meta_form = ToolMeta(
        name="submit_form",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-43",
    )

    @mcp.tool(
        name=meta_form.name,
        description=tool_description(
            meta_form,
            "Submit/acknowledge an IIQ Form by name with optional field values (best-effort).",
        ),
    )
    async def submit_form(form_name: str, values: dict[str, Any] | None = None) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/forms/{encode_path_segment(form_name)}/submit",
                json_body={"values": values or {}},
            )

        return await run_tool(
            meta_form, {"form_name": form_name, "values": values}, _run, audit=audit
        )

    # —— UIAPI-44 Email ——
    meta_email = ToolMeta(
        name="send_email_template",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-44",
    )

    @mcp.tool(
        name=meta_email.name,
        description=tool_description(
            meta_email,
            "Send an EmailTemplate to an address or identity (requires SMTP).",
        ),
    )
    async def send_email_template(
        template_name: str,
        to: str | None = None,
        identity_name: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {}
            if to:
                body["to"] = to
            if identity_name:
                body["identityName"] = identity_name
            if variables:
                body["variables"] = variables
            return await agent_post(
                client,
                f"/emailTemplates/{encode_path_segment(template_name)}/send",
                json_body=body,
            )

        return await run_tool(
            meta_email,
            {
                "template_name": template_name,
                "to": to,
                "identity_name": identity_name,
                "variables": variables,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-45 Audit export ——
    meta_aud = ToolMeta(
        name="export_audit_events",
        phase=2,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-45",
    )

    @mcp.tool(
        name=meta_aud.name,
        description=tool_description(
            meta_aud, "Export recent AuditEvent rows (SIEM-friendly) with optional limit."
        ),
    )
    async def export_audit_events(limit: int | None = 100) -> dict[str, Any]:
        async def _run() -> Any:
            params = {"limit": limit} if limit is not None else None
            return await agent_get(client, "/audit/export", params=params)

        return await run_tool(meta_aud, {"limit": limit}, _run, audit=audit)

    # —— UIAPI-46 Capability create ——
    meta_cap = ToolMeta(
        name="create_capability",
        phase=4,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-46",
    )

    @mcp.tool(
        name=meta_cap.name,
        description=tool_description(
            meta_cap, "Create a Capability object (advanced ops). Prefer assign_identity_capability to grant."
        ),
    )
    async def create_capability(
        name: str, description: str | None = None, rights: list[str] | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"name": name}
            if description:
                body["description"] = description
            if rights:
                body["rights"] = rights
            return await agent_post(client, "/capabilities", json_body=body)

        return await run_tool(
            meta_cap,
            {"name": name, "description": description, "rights": rights},
            _run,
            audit=audit,
        )

    # —— UIAPI-47 Object validate ——
    meta_val = ToolMeta(
        name="validate_sailpoint_object",
        phase=2,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-47",
    )

    @mcp.tool(
        name=meta_val.name,
        description=tool_description(
            meta_val, "Validate XML/object class+name exists and is loadable (pre-promotion check)."
        ),
    )
    async def validate_sailpoint_object(
        object_class: str, name: str | None = None, xml: str | None = None
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"class": object_class}
            if name:
                body["name"] = name
            if xml:
                body["xml"] = xml
            return await agent_post(client, "/objects/validate", json_body=body)

        return await run_tool(
            meta_val,
            {"object_class": object_class, "name": name, "xml_len": len(xml or "")},
            _run,
            audit=audit,
        )

    # —— UIAPI-48 Workflow resume ——
    meta_res = ToolMeta(
        name="resume_workflow_case",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-48",
    )

    @mcp.tool(
        name=meta_res.name,
        description=tool_description(
            meta_res, "Locate a WorkflowCase by id/name and mark for resume/inspection."
        ),
    )
    async def resume_workflow_case(case_id: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/workflows/cases/{encode_path_segment(case_id)}/resume"
            )

        return await run_tool(meta_res, {"case_id": case_id}, _run, audit=audit)

    # —— UIAPI-49 Risk ——
    meta_risk = ToolMeta(
        name="recalculate_risk_scores",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-49",
    )

    @mcp.tool(
        name=meta_risk.name,
        description=tool_description(meta_risk, "Run Refresh Risk Scores task."),
    )
    async def recalculate_risk_scores() -> dict[str, Any]:
        return await run_tool(
            meta_risk, {}, lambda: agent_post(client, "/risk/recalculate", json_body={}), audit=audit
        )

    # —— UIAPI-50 Transitive reports ——
    meta_tr = ToolMeta(
        name="list_transitive_reports",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-50",
    )

    @mcp.tool(
        name=meta_tr.name,
        description=tool_description(
            meta_tr, "List identities that report (transitively) to a manager."
        ),
    )
    async def list_transitive_reports(manager: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_get(
                client, f"/identities/{encode_path_segment(manager)}/reports/transitive"
            )

        return await run_tool(meta_tr, {"manager": manager}, _run, audit=audit)

    # —— UIAPI-51 Directory ops ——
    meta_dir = ToolMeta(
        name="directory_account_op",
        phase=3,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-51",
    )

    @mcp.tool(
        name=meta_dir.name,
        description=tool_description(
            meta_dir,
            "Directory/AD-style account op via LCM: addGroup|disable|enable|move. "
            "Args: application, op; optional identity, native_identity, group, ou.",
        ),
    )
    async def directory_account_op(
        application: str,
        op: str,
        identity: str | None = None,
        native_identity: str | None = None,
        group: str | None = None,
        ou: str | None = None,
    ) -> dict[str, Any]:
        async def _run() -> Any:
            body: dict[str, Any] = {"op": op}
            if identity:
                body["identity"] = identity
            if native_identity:
                body["nativeIdentity"] = native_identity
            if group:
                body["group"] = group
            if ou:
                body["ou"] = ou
            return await agent_post(
                client,
                f"/applications/{encode_path_segment(application)}/directory/ops",
                json_body=body,
            )

        return await run_tool(
            meta_dir,
            {
                "application": application,
                "op": op,
                "identity": identity,
                "native_identity": native_identity,
                "group": group,
                "ou": ou,
            },
            _run,
            audit=audit,
        )

    # —— UIAPI-52 Identity merge ——
    meta_merge = ToolMeta(
        name="merge_identities",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-52",
    )

    @mcp.tool(
        name=meta_merge.name,
        description=tool_description(
            meta_merge,
            "Best-effort merge source identity attributes into target (advanced ops).",
        ),
    )
    async def merge_identities(source: str, into: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                f"/identities/{encode_path_segment(source)}/merge",
                json_body={"into": into},
            )

        return await run_tool(
            meta_merge, {"source": source, "into": into}, _run, audit=audit
        )

    # —— UIAPI-53 Bulk onboard ——
    meta_bulk = ToolMeta(
        name="bulk_onboard_applications",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-53",
    )

    @mcp.tool(
        name=meta_bulk.name,
        description=tool_description(
            meta_bulk,
            "Queue multi-app onboard payloads [{name,type,attributes}]; fan-out with onboard_application.",
        ),
    )
    async def bulk_onboard_applications(
        applications: list[dict[str, Any]],
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/applications/bulk/onboard",
                json_body={"applications": applications},
            )

        return await run_tool(
            meta_bulk, {"count": len(applications or [])}, _run, audit=audit
        )

    # —— UIAPI-54 Provisioning retry ——
    meta_retry = ToolMeta(
        name="retry_provisioning_transaction",
        phase=3,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-54",
    )

    @mcp.tool(
        name=meta_retry.name,
        description=tool_description(
            meta_retry, "Retry a provisioning transaction id (best-effort via Perform Maintenance)."
        ),
    )
    async def retry_provisioning_transaction(transaction_id: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/provisioning/{encode_path_segment(transaction_id)}/retry"
            )

        return await run_tool(
            meta_retry, {"transaction_id": transaction_id}, _run, audit=audit
        )

    # —— UIAPI-55 Alerts: registered in impl_scim_catalog (agent API) ——

    # —— UIAPI-58 Rebuild managers ——
    meta_mgrs = ToolMeta(
        name="rebuild_manager_hierarchy",
        phase=3,
        risk=Risk.LOW_WRITE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-58",
    )

    @mcp.tool(
        name=meta_mgrs.name,
        description=tool_description(
            meta_mgrs,
            "Set Identity.manager from authoritative app Link attributes (default MNB-HR.manager). "
            "Use after HR aggregation when OOTB managerCorrelationMapping did not link cubes. "
            "Then run Refresh Identity Cube to update isManager flags.",
        ),
    )
    async def rebuild_manager_hierarchy(
        application: str = "MNB-HR",
        manager_attribute: str = "manager",
    ) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/identities/managers/rebuild",
                json_body={
                    "application": application,
                    "managerAttribute": manager_attribute,
                },
            )

        return await run_tool(
            meta_mgrs,
            {"application": application, "manager_attribute": manager_attribute},
            _run,
            audit=audit,
        )

    # —— UIAPI-56 Service restart ——
    meta_svc = ToolMeta(
        name="restart_iiq_service",
        phase=4,
        risk=Risk.PROVISIONING,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-56",
    )

    @mcp.tool(
        name=meta_svc.name,
        description=tool_description(
            meta_svc,
            "Lab guidance for restarting an IIQ service (does not SSH); returns operator steps.",
        ),
    )
    async def restart_iiq_service(service_name: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client, f"/system/services/{encode_path_segment(service_name)}/restart"
            )

        return await run_tool(meta_svc, {"service_name": service_name}, _run, audit=audit)

    # —— UIAPI-57 Scope assign ——
    meta_scope = ToolMeta(
        name="assign_identity_scope",
        phase=4,
        risk=Risk.COMPLIANCE,
        implemented=True,
        requires_confirmation=True,
        gap_id="UIAPI-57",
    )

    @mcp.tool(
        name=meta_scope.name,
        description=tool_description(
            meta_scope,
            "Assign an IIQ Scope to an identity (assignedScope). Prefer this over excluded update_scope.",
        ),
    )
    async def assign_identity_scope(identity: str, scope: str) -> dict[str, Any]:
        async def _run() -> Any:
            return await agent_post(
                client,
                "/scopes/assign",
                json_body={"identity": identity, "scope": scope},
            )

        return await run_tool(
            meta_scope, {"identity": identity, "scope": scope}, _run, audit=audit
        )
