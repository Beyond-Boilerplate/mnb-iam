#!/usr/bin/env python3
"""Generate docs/api/openapi/openapi-meridian-agent.yaml — MCP-oriented agent contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "api" / "openapi" / "openapi-meridian-agent.yaml"

# Every UIAPI gap with agent posture
GAPS = [
    ("UIAPI-01", "tasks", "implemented", "POST /mnbToolkit/tasks/run", "Run allowlisted aggregation-style tasks"),
    ("UIAPI-02", "tasks", "implemented", "POST /mnbToolkit/tasks/run", "Run Identity Refresh / allowlisted refresh tasks"),
    ("UIAPI-03", "access-requests", "implemented", "POST /mnbToolkit/agent/accessRequests", "Launch LCM-style workflow with plan args"),
    ("UIAPI-04", "work-items", "implemented", "POST /mnbToolkit/agent/workItems/{id}/decide", "Approve/reject work item via Workflower"),
    ("UIAPI-05", "certifications", "implemented", "POST /mnbToolkit/agent/certifications/items/{id}/decide", "Decide certification item (approve/revoke/mitigate)"),
    ("UIAPI-06", "sod", "implemented", "POST /mnbToolkit/agent/sod/violations/{id}/mitigate", "Mitigate SoD violation (gated setting)"),
    ("UIAPI-07", "applications", "implemented", "POST /mnbToolkit/agent/applications/wizard", "Create/update Application via wizard fields"),
    ("UIAPI-08", "applications", "implemented", "GET|POST /mnbToolkit/agent/applications/{name}/config", "Read/update Application attributes (gated)"),
    ("UIAPI-09", "populations", "implemented", "POST /mnbToolkit/agent/populations", "Create/update GroupDefinition population"),
    ("UIAPI-10", "workgroups", "implemented", "POST /mnbToolkit/agent/workgroups/{name}/members", "Add/remove workgroup members"),
    ("UIAPI-11", "capabilities", "implemented", "POST /mnbToolkit/agent/identities/{name}/capabilities", "Assign/revoke Capability on identity"),
    ("UIAPI-12", "passwords", "implemented", "POST /mnbToolkit/agent/identities/{name}/password", "Admin password set / unlock (gated)"),
    ("UIAPI-13", "schedules", "implemented", "POST /mnbToolkit/agent/schedules", "Create simple TaskSchedule (cron string)"),
    ("UIAPI-14", "reports", "implemented", "POST /mnbToolkit/agent/reports/run", "Run report TaskDefinition via toolkit task runner"),
    ("UIAPI-15", "forms", "implemented", "GET /mnbToolkit/agent/forms", "List/get Form objects"),
    ("UIAPI-16", "quicklinks", "implemented", "GET /mnbToolkit/agent/quicklinks", "List QuickLinks"),
    ("UIAPI-17", "email-templates", "implemented", "GET /mnbToolkit/agent/emailTemplates", "List/get EmailTemplate (edit = SSB)"),
    ("UIAPI-18", "audit", "implemented", "GET /mnbToolkit/agent/audit/events", "Search recent AuditEvent rows"),
    ("UIAPI-19", "batch", "implemented", "POST /mnbToolkit/agent/batchRequests", "Create BatchRequest object from payload"),
    ("UIAPI-20", "access-history", "implemented", "GET /mnbToolkit/agent/accessHistory/status", "Probe Access History / IAI Configuration presence"),
    ("UIAPI-21", "connectors", "implemented", "POST /mnbToolkit/agent/connectors/testConnection", "ConnectorFactory.testConfiguration for an Application"),
    ("UIAPI-22", "connectors", "implemented", "POST /mnbToolkit/agent/applications/{name}/nativeChangeDetection", "Enable NCD flags on Application"),
    ("UIAPI-23", "plugins", "implemented", "GET|POST /mnbToolkit/agent/plugins*", "List / enable / base64-install plugins"),
    ("UIAPI-24", "system", "implemented", "GET|POST /mnbToolkit/agent/system/config", "Read/merge SystemConfiguration attributes (gated)"),
    ("UIAPI-25", "config", "implemented", "GET|POST /mnbToolkit/agent/objects/*", "Export/import SailPointObject XML"),
    ("UIAPI-26", "plugins", "implemented", "GET /mnbToolkit/agent/study/catalog", "Study plugin catalog + installed matches"),
    ("UIAPI-27", "toolkit", "implemented", "GET /mnbToolkit/ping", "Toolkit health ping"),
]


def op(summary, gap_id, status, method_impl="java"):
    return {
        "tags": [gap_id.split("-")[0] + "-" + gap_id.split("-")[1] if False else gap_id[:5], "meridian-agent"],
        "summary": summary,
        "operationId": None,  # filled later
        "x-uiapi-id": gap_id,
        "x-agent-status": status,
        "x-mcp-tool": None,
        "responses": {
            "200": {
                "description": "OK",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentEnvelope"}}},
            },
            "400": {"description": "Bad request", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentError"}}}},
            "403": {"description": "Forbidden / kill switch", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentError"}}}},
            "404": {"description": "Not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentError"}}}},
            "501": {"description": "Not implemented / rejected posture", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentError"}}}},
        },
        "security": [{"basicAuth": []}, {"oAuth2ClientCredentials": []}],
    }


def dump_yaml(obj, indent=0):
    # reuse simple emitter from generate_openapi if needed — emit JSON for reliability then note yaml
    # Prefer writing JSON OpenAPI which Swagger accepts, PLUS yaml via json for portability
    pass


def main():
    paths = {}

    def add(path, method, gap_id, summary, status, body=False):
        item = paths.setdefault(path, {})
        o = {
            "tags": [gap_id, "meridian-agent"],
            "summary": summary,
            "operationId": f"{method}_{path.strip('/').replace('/', '_').replace('{', '').replace('}', '')}",
            "x-uiapi-id": gap_id,
            "x-agent-status": status,
            "x-mcp-tool": f"iiq_{gap_id.lower().replace('-', '_')}_{method}",
            "responses": {
                "200": {
                    "description": "Success envelope",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentEnvelope"}}},
                },
                "403": {
                    "description": "Denied / feature flag off",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentError"}}},
                },
                "501": {
                    "description": "Rejected or deferred for agents",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentError"}}},
                },
            },
            "security": [{"basicAuth": []}],
        }
        if "{" in path:
            o["parameters"] = []
            for part in path.split("/"):
                if part.startswith("{") and part.endswith("}"):
                    name = part[1:-1]
                    o["parameters"].append(
                        {"name": name, "in": "path", "required": True, "schema": {"type": "string"}}
                    )
        if body:
            o["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AgentRequest"}}},
            }
        item[method] = o

    # Meta
    add("/mnbToolkit/agent/gaps", "get", "UIAPI-META", "Gap matrix for MCP planners", "implemented")
    add("/mnbToolkit/ping", "get", "UIAPI-27", "Toolkit health ping", "implemented")

    # Tasks
    add("/mnbToolkit/tasks/run", "post", "UIAPI-01", "Run allowlisted task (aggregation)", "implemented", True)
    add("/mnbToolkit/tasks/run", "post", "UIAPI-02", "Run allowlisted task (refresh)", "implemented", True)
    add("/mnbToolkit/tasks/results/{id}", "get", "UIAPI-01", "Poll TaskResult", "implemented")
    add("/mnbToolkit/tasks/allowed", "get", "UIAPI-01", "List allowlisted task patterns", "implemented")

    # P0
    add("/mnbToolkit/agent/accessRequests", "post", "UIAPI-03", "Submit access request via workflow launch", "implemented", True)
    add("/mnbToolkit/agent/workItems", "get", "UIAPI-04", "List open work items (limit)", "implemented")
    add("/mnbToolkit/agent/workItems/{id}", "get", "UIAPI-04", "Get work item", "implemented")
    add("/mnbToolkit/agent/workItems/{id}/decide", "post", "UIAPI-04", "Approve or reject work item", "implemented", True)
    add("/mnbToolkit/agent/certifications", "get", "UIAPI-05", "List certifications", "implemented")
    add("/mnbToolkit/agent/certifications/items/{id}/decide", "post", "UIAPI-05", "Decide certification item", "implemented", True)
    add("/mnbToolkit/agent/certifications/{id}/sign", "post", "UIAPI-05", "Sign certification", "implemented", True)
    add("/mnbToolkit/agent/sod/openCount", "get", "UIAPI-06", "Count open policy violations", "implemented")
    add("/mnbToolkit/agent/sod/violations", "get", "UIAPI-06", "List open policy violations", "implemented")
    add("/mnbToolkit/agent/sod/violations/{id}/mitigate", "post", "UIAPI-06", "Mitigate policy violation", "implemented", True)
    add("/mnbToolkit/agent/applications/wizard", "post", "UIAPI-07", "Create/update Application (wizard fields)", "implemented", True)
    add("/mnbToolkit/agent/applications/stubs", "post", "UIAPI-07", "Create Application stub (alias of wizard)", "implemented", True)
    add("/mnbToolkit/agent/applications/{name}/config", "get", "UIAPI-08", "Get Application config", "implemented")
    add("/mnbToolkit/agent/applications/{name}/config", "post", "UIAPI-08", "Update Application config", "implemented", True)
    add("/mnbToolkit/agent/applications/{name}/nativeChangeDetection", "post", "UIAPI-22", "Configure native change detection", "implemented", True)

    # P1
    add("/mnbToolkit/agent/populations", "get", "UIAPI-09", "List populations", "implemented")
    add("/mnbToolkit/agent/populations", "post", "UIAPI-09", "Create population", "implemented", True)
    add("/mnbToolkit/agent/populations/{name}", "get", "UIAPI-09", "Get population", "implemented")
    add("/mnbToolkit/agent/workgroups", "get", "UIAPI-10", "List workgroups", "implemented")
    add("/mnbToolkit/agent/workgroups/{name}/members", "post", "UIAPI-10", "Add/remove workgroup member", "implemented", True)
    add("/mnbToolkit/agent/identities/{name}/capabilities", "post", "UIAPI-11", "Assign/revoke capability", "implemented", True)
    add("/mnbToolkit/agent/identities/{name}/password", "post", "UIAPI-12", "Set password or unlock", "implemented", True)
    add("/mnbToolkit/agent/schedules", "get", "UIAPI-13", "List task schedules", "implemented")
    add("/mnbToolkit/agent/schedules", "post", "UIAPI-13", "Create task schedule", "implemented", True)
    add("/mnbToolkit/agent/reports/run", "post", "UIAPI-14", "Run report task", "implemented", True)
    add("/mnbToolkit/agent/forms", "get", "UIAPI-15", "List forms", "implemented")
    add("/mnbToolkit/agent/forms/{name}", "get", "UIAPI-15", "Get form", "implemented")
    add("/mnbToolkit/agent/quicklinks", "get", "UIAPI-16", "List quicklinks", "implemented")
    add("/mnbToolkit/agent/emailTemplates", "get", "UIAPI-17", "List email templates", "implemented")
    add("/mnbToolkit/agent/emailTemplates/{name}", "get", "UIAPI-17", "Get email template", "implemented")
    add("/mnbToolkit/agent/audit/events", "get", "UIAPI-18", "Search audit events", "implemented")
    add("/mnbToolkit/agent/batchRequests", "post", "UIAPI-19", "Create batch request", "implemented", True)
    add("/mnbToolkit/agent/accessHistory/status", "get", "UIAPI-20", "Access history / AI config status", "implemented")
    add("/mnbToolkit/agent/connectors/testConnection", "post", "UIAPI-21", "Test application connector", "implemented", True)
    add("/mnbToolkit/agent/plugins", "get", "UIAPI-23", "List installed plugins", "implemented")
    add("/mnbToolkit/agent/plugins/{name}/state", "post", "UIAPI-23", "Enable/disable plugin", "implemented", True)
    add("/mnbToolkit/agent/plugins/install", "post", "UIAPI-23", "Install plugin from zipBase64", "implemented", True)
    add("/mnbToolkit/agent/system/config", "get", "UIAPI-24", "Get SystemConfiguration (redacted)", "implemented")
    add("/mnbToolkit/agent/system/config", "post", "UIAPI-24", "Merge SystemConfiguration attributes", "implemented", True)
    add("/mnbToolkit/agent/objects/export", "get", "UIAPI-25", "Export SailPointObject as XML", "implemented")
    add("/mnbToolkit/agent/objects/import", "post", "UIAPI-25", "Import SailPointObject XML", "implemented", True)
    add("/mnbToolkit/agent/study/catalog", "get", "UIAPI-26", "Study plugin catalog", "implemented")

    gap_table = [
        {
            "id": g[0],
            "category": g[1],
            "status": g[2],
            "primaryPath": g[3],
            "notes": g[4],
            "mcpTool": f"iiq_{g[0].lower().replace('-', '_')}",
        }
        for g in GAPS
    ]

    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Meridian Custom APIs",
            "version": "1.3.0",
            "description": (
                "Bank-owned IdentityIQ Custom APIs for MCP / ITSM orchestration. "
                "Closes UI-VS-API gaps (UIAPI-01…27). "
                "High-risk ops require plugin settings (mutateGovernanceEnabled, passwordResetEnabled, advancedOpsEnabled). "
                "See docs/api/UI-VS-API-GAPS.md and docs/api/MCP-TOOLS.md."
            ),
            "x-gap-register": gap_table,
        },
        "servers": [
            {"url": "/identityiq/plugin/rest", "description": "Via docs/api/serve.py proxy"},
            {"url": "http://localhost:8080/identityiq/plugin/rest", "description": "Direct lab IIQ"},
        ],
        "tags": [{"name": "meridian-agent", "description": "Meridian toolkit agent verbs"}]
        + [{"name": g[0], "description": g[4]} for g in GAPS],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "basicAuth": {"type": "http", "scheme": "basic"},
                "oAuth2ClientCredentials": {
                    "type": "oauth2",
                    "flows": {
                        "clientCredentials": {
                            "tokenUrl": "http://localhost:8080/identityiq/oauth2/token",
                            "scopes": {},
                        }
                    },
                },
            },
            "schemas": {
                "AgentEnvelope": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "gapId": {"type": "string"},
                        "bank": {"type": "string", "example": "MNB"},
                        "plugin": {"type": "string", "example": "mnb_iam_toolkit"},
                        "data": {"type": "object", "additionalProperties": True},
                        "messages": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "AgentError": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "detail": {"type": "string"},
                        "status": {"type": "integer"},
                        "gapId": {"type": "string"},
                        "guidance": {"type": "string"},
                    },
                },
                "AgentRequest": {
                    "type": "object",
                    "additionalProperties": True,
                    "description": "Operation-specific JSON body (see MCP-TOOLS.md).",
                },
            },
        },
        "security": [{"basicAuth": []}],
    }

    # Write YAML via shared dumper if available
    import sys

    sys.path.insert(0, str(ROOT / "tools" / "iiq-api-mine"))
    from generate_openapi import dump_yaml

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dump_yaml(spec), encoding="utf-8")
    # Also JSON for MCP servers that prefer JSON
    (OUT.with_suffix(".json")).write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} and {OUT.with_suffix('.json')} ({len(paths)} paths)")


if __name__ == "__main__":
    main()
