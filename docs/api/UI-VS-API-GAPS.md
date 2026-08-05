# UI vs API gaps (IdentityIQ 8.5 lab) — Meridian Custom APIs

**Related:** [`MCP-TOOLS.md`](MCP-TOOLS.md) · [`AUTO-STORY-BOARD-BACKLOG.md`](AUTO-STORY-BOARD-BACKLOG.md) · [`OOTB-IIQ-UX-GAPS.md`](OOTB-IIQ-UX-GAPS.md) (50 operator UX discoverability gaps) · [`openapi/openapi-meridian-agent.yaml`](openapi/openapi-meridian-agent.yaml) · plugin `mnb_iam_toolkit`.

Register IDs **UIAPI-01…90** plus ROI **97 / 98 / 105–107 / 139** are **implemented** in toolkit **1.3.16** under `/plugin/rest/mnbToolkit/{tasks,agent,agent/console}/*`, gated by feature flags. Waves A–F MCP wrappers cover console desks, SoD, workgroup/QL/email, schema/correlation/lifecycle/ObjectConfig/PasswordPolicy/provisioning policies, GroupFactory, role requirements/selector, capability rights, cert definition patch, access-request sunset/formAnswers, identity forwarding, risk weights, TaskDefinition upsert, aggregation stop, workflow patch, form upsert, connector deep config, SoD matrix import — see [`MCP-TOOLS.md`](MCP-TOOLS.md).

**Remaining open / hybrid / excluded** IDs in **UIAPI-91…167** (minus the ROI closings above) stay advertised on `GET /agent/gaps`. Sourced from a board-back pass: 40 auto-story-capable tickets vs 200 real-life IAM tickets that cannot be fully closed by the automated processor. Full story lists: [`AUTO-STORY-BOARD-BACKLOG.md`](AUTO-STORY-BOARD-BACKLOG.md).

## Feature flags

| Setting | Gates |
| --- | --- |
| `agentApiEnabled` | All `/mnbToolkit/agent/*` |
| `mutateGovernanceEnabled` | Approvals, certs, SoD, LCM launch, capabilities |
| `passwordResetEnabled` | Password set / unlock |
| `advancedOpsEnabled` | App config write, NCD, system config write, object import, plugin enable/install |
| `taskRunEnabled` + `allowedTaskNames` | Task run |

## Register — implemented (UIAPI-01…90)

| ID | Status | Primary path |
| --- | --- | --- |
| UIAPI-01/02 | implemented | `POST /mnbToolkit/tasks/run` |
| UIAPI-03 | implemented | `POST .../accessRequests` (+ sunset/sunrise/formAnswers) |
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
| UIAPI-28…90 | implemented | entitlements, roles, JML, certs campaigns, SoD CRUD/constraints/simulate, plugins, orgchart, console desks, schema/correlation, lifecycle, ObjectConfig, password policy, provisioning policies, GroupFactory, capability rights, role selector/requirements, cert definition patch, forwarding, risk config, TaskDefinition, aggregation stop — see MCP-TOOLS.md |
| UIAPI-97 | implemented | `GET\|POST .../workflows*` (list/get/patch; not visual designer) |
| UIAPI-98 | implemented | `POST .../forms` (upsert + fields) |
| UIAPI-105 | implemented | `POST .../applications/{name}/connector/ad` |
| UIAPI-106 | implemented | `POST .../applications/{name}/connector/jdbc` |
| UIAPI-107 | implemented | `POST .../applications/{name}/connector/oauth` |
| UIAPI-139 | implemented | `POST .../policies/sod/matrix/import` |

Discovery: `GET /plugin/rest/mnbToolkit/agent/gaps`.

**Still excluded (unsafe / no Custom API):** `update_rule_source`, `update_scope`, legacy `grant_capability`.

---

## Auto-story impossible board — gap register (UIAPI-91…167)

Status for all rows below: **open** (no Meridian Custom API / MCP tool sufficient for E2E auto-story).  
Priority is informational for roadmap triage — not a delivery commitment.

### Branding / UX

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-91 | IIQ web branding / CSS / war static assets | Lives in `web/` SSD + redeploy; not object import | 41–43, 45–47, 50–51, 53, 55, 138 |
| UIAPI-92 | Full UI i18n / locale packs | Message catalogs + JSF bundles | 44 |
| UIAPI-93 | Home dashboard widget layout editor | UI-only dashboard config | 48 |
| UIAPI-94 | Email chrome beyond template body | Partial: `update_email_template`; header/footer war assets remain | 49 |

### AuthN / MFA / federation

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-95 | SAML/OIDC/WebAuthn/MFA login UX | Login module + IdP metadata; partial system config only | 52, 122, 126–131, 140 |
| UIAPI-122 | Entra/SCIM inbound federation provisioning | External IdP + SCIM ingress design | 132–133 |
| UIAPI-123 | mTLS / cert-based API auth | Platform TLS / reverse proxy | 134, 193 |

### Rules / workflows / forms / debug

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-96 | Live Rule source authoring | **Denylisted** `update_rule_source`; SSD-only | 56–57, 60, 63, 66, 68–71, 74, 81, 83 |
| UIAPI-97 | Workflow visual designer / LCM clone | **Implemented (partial):** `list_workflows` / `get_workflow` / `patch_workflow` for meta/variables/named step — not a visual designer | 58–59, 64–65, 72–73, 78, 84 |
| UIAPI-98 | Forms designer (drag/drop, multi-page) | **Implemented (partial):** `upsert_form` for top-level Form + fields; not drag/drop UX | 61–62, 85 |
| UIAPI-99 | Policy violation owner Rule wiring | Partial policy CRUD; owner Rule UX | 67 |
| UIAPI-100 | QuickLink DynamicScope Rule | Denylist `update_scope` | 75 |
| UIAPI-101 | Lifecycle Event advanced wizard | Partial `upsert_lifecycle_event` | 76–77 |
| UIAPI-102 | Workflow unit test harness | No IIQ test runner API | 79 |
| UIAPI-103 | Debug Beanshell / connector trace consoles | Unsafe; intentional keep-out | 80, 96, 240 |
| UIAPI-104 | Rule revision diff UI | No SCM integration in MCP | 82 |

### Connectors / applications (deep UI)

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-105 | AD forest / IQService / proxy wizards | **Implemented (partial):** `configure_ad_connector` attribute pack | 86–87, 104 |
| UIAPI-106 | JDBC SQL map builder | **Implemented (partial):** `configure_jdbc_connector` + `sqlMap` | 88 |
| UIAPI-107 | OAuth interactive / SCIM deep auth | **Implemented (partial):** `configure_oauth_connector` attrs; token dance still IdP | 89–91 |
| UIAPI-108 | SAP JCo destination UI | Proprietary connector UI | 92 |
| UIAPI-109 | Mainframe RACF connector | Out of lab product scope | 93 |
| UIAPI-110 | Logical / composite app editor | Partial wizard; no graph UI | 94–95, 107 |
| UIAPI-111 | Schema attribute drag UX | `apply_application_schema` ≠ designer | 97–98 |
| UIAPI-112 | Aggregation partitioning / watermark UX | Partial task/agg APIs | 99–101, 110 |
| UIAPI-113 | App maintenance calendar | No schedule calendar object API | 102 |
| UIAPI-114 | Custom connector JAR deploy | File drop + restart | 103 |
| UIAPI-115 | Keystore upload test-connection UI | File upload not MCP | 105 |
| UIAPI-116 | Risk weight designer UI | Partial `update_risk_score_config` | 106, 229 |
| UIAPI-117 | Unstructured / file targets | Thin coverage | 108, 226–227 |
| UIAPI-118 | Secrets vault / SFTP credential UX | Env/secrets managers | 109, 115, 118, 135, 192 |

### PAM / privileged / physical

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-119 | PAM brokers (CyberArk/BT/JIT) | External products | 111–114, 116–117, 119–120, 123–124 |
| UIAPI-120 | SMS firecall / paging | External notification | 121 |
| UIAPI-121 | Cloud privilege brokers | AWS/Azure PE outside IIQ | 125 |
| UIAPI-155 | Physical badge / door SoD | Non-IIQ systems | 215–216 |

### Compliance / reporting / SIEM

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-125 | SIEM stream / UEBA / WORM | Platform integration | 139, 150–152, 213 |
| UIAPI-126 | Exam binder / control frameworks | Document generation | 141–143, 153–156, 210 |
| UIAPI-127 | GDPR DSAR / erasure / legal hold | Process + multi-system | 144–145, 160 |
| UIAPI-128 | Jasper Studio pixel layout | Authoring tool | 146–147 |
| UIAPI-129 | Executive slide / CCM dashboards | BI tools | 148–149 |
| UIAPI-130 | AI/ML model risk / IdentityAI | Product/process | 157, 170, 214, 222 |
| UIAPI-131 | Data classification glossary | Governance content | 158, 179 |
| UIAPI-132 | Retention purge / archive warehouse | DBA + policy | 159, 169 |

### HR / data / org

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-133 | HR ETL / bad-row remediation outside IIQ | Lab scripts + human | 161–162, 175 |
| UIAPI-134 | Workday/position/cost-center masters | HRIS integration | 163–166 |
| UIAPI-135 | Merge/cutover/M&A identity programs | Program management + partial `merge_identities` | 167–168, 219–220 |
| UIAPI-136 | Preferred vs legal name UX | ObjectConfig partial; UX HYBRID | 171–172 |
| UIAPI-137 | Vacant / matrix manager models | Org design | 173–174 |
| UIAPI-138 | Job-code / birthright Excel codegen | Offline planning | 176–177 |
| UIAPI-139 | SoD matrix Excel → policy codegen | **Implemented:** `import_sod_matrix` (CSV/rows → constraints) | 178 |
| UIAPI-140 | Orphan owner campaign (business) | Process; console_orphans is read assist | 180 |

### Platform / DevOps / multi-product

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-141 | IIQ version upgrades / hotfixes | Ops | 181–182 |
| UIAPI-142 | Cluster / JVM / scale | Ops | 183, 186–187 |
| UIAPI-143 | Database DBA work | Ops | 184–185 |
| UIAPI-144 | Backup / DR drills | Ops | 188–189 |
| UIAPI-145 | Container image / CVE / Helm | DevOps | 190–191 |
| UIAPI-146 | WAF / API rate limits | Edge security | 194–195 |
| UIAPI-147 | Chaos / soak performance | QA | 196–197 |
| UIAPI-148 | Full OTel for IIQ core | Observability stack | 198 |
| UIAPI-149 | Multi-tenant IIQ | Architecture | 199 |
| UIAPI-150 | Migrate off IIQ / to ISC | Program | 200–202 |
| UIAPI-151 | ServiceNow CMDB/RITM | ITSM | 203–204 |
| UIAPI-152 | ChatOps / mobile approvals | Collab channels | 205–207, 236–237 |
| UIAPI-153 | CAB / change-freeze process | GRC process | 208–209 |
| UIAPI-154 | Incident tabletop / ransomware playbooks | IR process | 211–212 |
| UIAPI-156 | Vendor / fourth-party risk portals | GRC SaaS | 217–218 |

### Advanced IIQ features (thin MCP)

| ID | Gap | Why MCP insufficient | Example stories |
| --- | --- | --- | --- |
| UIAPI-157 | Rapid Setup full click-path | Wizard UI | 221 |
| UIAPI-158 | Access History analytics UI | Status API ≠ analytics | 223 |
| UIAPI-159 | AI role mining / peer outlier UX | Partial mine APIs | 224–225 |
| UIAPI-160 | Activity monitoring policy UI | Thin | 228 |
| UIAPI-161 | Advanced Analytics saved-search share | UI | 230 |
| UIAPI-162 | Identity snapshot compare UI | UI | 231 |
| UIAPI-163 | Account group inheritance visualizer | UI | 232 |
| UIAPI-164 | Business request portal UX | Partial LCM APIs | 233 |
| UIAPI-165 | Password sync interceptor / DPR client | Client software | 234–235 |
| UIAPI-166 | E-signature legal meaning authoring | Partial list API | 238 |
| UIAPI-167 | Policy simulation campaign UI mode | Partial `simulate_sod_policy` | 239 |

---

## Prioritization hints (auto-story ROI)

| Tier | Gaps | Rationale |
| --- | --- | --- |
| Do not automate | UIAPI-96, 100, 103 | Safety denylist / Debug |
| High ROI if built | _(closed in 1.3.16)_ UIAPI-97/98/105–107/139 | Workflow patch, form upsert, connector deep config, SoD matrix import |
| Keep HYBRID | UIAPI-91 branding, 126 exam packs, 133 HR ETL | Human artifacts are the deliverable |
| Out of product | UIAPI-119 PAM, 125 SIEM, 141–150 platform/migration | Wrong control plane |

## Install

```bash
./pluginsrc/mnb-iam-toolkit/package.sh && ./pluginsrc/mnb-iam-toolkit/install.sh
python3 tools/iiq-api-mine/generate_meridian_agent_openapi.py
./docs/api/serve.py   # Swagger → Meridian Custom APIs
```

_Last updated: toolkit 1.3.16 — ROI closings UIAPI-97/98/105–107/139 + gaps honesty for remaining 91…167._
