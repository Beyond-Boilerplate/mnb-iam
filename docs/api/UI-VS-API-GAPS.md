# UI vs API gaps (IdentityIQ 8.5 lab) — Meridian Custom APIs

**Related:** [`MCP-TOOLS.md`](MCP-TOOLS.md) · [`openapi/openapi-meridian-agent.yaml`](openapi/openapi-meridian-agent.yaml) · plugin `mnb_iam_toolkit` display **Meridian Custom APIs**.

All register IDs **UIAPI-01…27** are **implemented** in toolkit **1.3.0** under `/plugin/rest/mnbToolkit/{tasks,agent}/*`, gated by feature flags.

## Feature flags

| Setting | Gates |
| --- | --- |
| `agentApiEnabled` | All `/mnbToolkit/agent/*` |
| `mutateGovernanceEnabled` | Approvals, certs, SoD, LCM launch, capabilities |
| `passwordResetEnabled` | Password set / unlock |
| `advancedOpsEnabled` | App config write, NCD, system config write, object import, plugin enable/install |
| `taskRunEnabled` + `allowedTaskNames` | Task run |

## Register

| ID | Status | Primary path |
| --- | --- | --- |
| UIAPI-01/02 | implemented | `POST /mnbToolkit/tasks/run` |
| UIAPI-03 | implemented | `POST .../accessRequests` |
| UIAPI-04 | implemented | `POST .../workItems/{id}/decide` |
| UIAPI-05 | implemented | `POST .../certifications/items/{id}/decide` |
| UIAPI-06 | implemented | `POST .../sod/violations/{id}/mitigate` |
| UIAPI-07 | implemented | `POST .../applications/wizard` |
| UIAPI-08 | implemented | `GET\|POST .../applications/{name}/config` |
| UIAPI-09…19 | implemented | populations, workgroups, caps, password, schedules, reports, forms, QLs, email, audit, batch |
| UIAPI-20 | implemented | `GET .../accessHistory/status` |
| UIAPI-21 | implemented | `POST .../connectors/testConnection` |
| UIAPI-22 | implemented | `POST .../applications/{name}/nativeChangeDetection` |
| UIAPI-23 | implemented | `GET .../plugins`, `POST .../plugins/{name}/state`, `POST .../plugins/install` |
| UIAPI-24 | implemented | `GET\|POST .../system/config` |
| UIAPI-25 | implemented | `GET .../objects/export`, `POST .../objects/import` |
| UIAPI-26 | implemented | `GET .../study/catalog` |
| UIAPI-27 | implemented | `GET /mnbToolkit/ping` |

Discovery: `GET /plugin/rest/mnbToolkit/agent/gaps`.

## Install

```bash
./pluginsrc/mnb-iam-toolkit/package.sh && ./pluginsrc/mnb-iam-toolkit/install.sh
python3 tools/iiq-api-mine/generate_meridian_agent_openapi.py
./docs/api/serve.py   # Swagger → Meridian Custom APIs
```

_Last updated: toolkit 1.3.0 Meridian Custom APIs._
