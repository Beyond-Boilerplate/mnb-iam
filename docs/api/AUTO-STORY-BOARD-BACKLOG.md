# Auto-story board-back catalog — Meridian IAM

**Method:** Start from tickets a real bank IAM team files on Jira (service desk + project board), then map backward to MCP tool coverage and the auto-story allowlist (`identity-admin`, `app-onboarding`, `task-ops`, `access-request`, `governance-admin`, `certification`, `policy-sod`, `jml-lifecycle`).

**Related:** [`MCP-TOOLS.md`](MCP-TOOLS.md) · [`UI-VS-API-GAPS.md`](UI-VS-API-GAPS.md) · `scripts/auto_story/config.yaml`

**Counts:** **40** MCP_E2E-capable · **200** real-life but not auto-story closable (gap / HYBRID / BLOCKED).

**Denylist (never auto):** `update_rule_source`, `update_scope`, `grant_capability`. Terminal Jira state: **In Review** only (never Done).

---

## A. Forty stories the processor can handle (MCP_E2E)

Paste into KAN with labels `agent-ready` + work-type. Prefer Meridian personas (`MNB000xx`) and lab apps.

### Identity admin (1–8)

| # | Summary | Labels | Primary MCP |
| --- | --- | --- | --- |
| 1 | Unlock Meera Torres after AD lock cascade | identity-admin | `search_identities`, `unlock_iiq_identity`, `get_identity_accounts` |
| 2 | Reset + expire contractor password at offboarding | identity-admin | `set_identity_password` / `reset_password`, `expire_password`, `get_password_policy` |
| 3 | Disable terminated Anita Ross; verify leaver accounts | identity-admin | `disable_identity`, `get_identity_accounts`, `search_audit_events` |
| 4 | Assign IIQ Capability (non-SystemAdmin) to backup SOC analyst | identity-admin | `list_agent_capabilities`, `assign_identity_capability` |
| 5 | Set out-of-office forwarding for manager on PTO | identity-admin | `set_identity_forwarding`, `search_identities` |
| 6 | Unlock + reset password for locked helpdesk queue identity | identity-admin | `unlock_iiq_identity`, `reset_password` |
| 7 | Correlate orphan AD account to HR identity | identity-admin | `correlate_account`, `search_identities`, `list_accounts_grid` |
| 8 | Uncorrelate wrong account link after twin hire | identity-admin | `uncorrelate_account`, `get_identity_accounts` |

### App onboarding / connector (9–14)

| # | Summary | Labels | Primary MCP |
| --- | --- | --- | --- |
| 9 | Onboard WirePortal delimited feed (Bengaluru) | app-onboarding | `create_application` / `onboard_application`, `update_application_config`, `trigger_aggregation` |
| 10 | Fix Salesforce-CRM correlation on email | app-onboarding | `get_application_config`, `update_correlation_config`, `trigger_aggregation` |
| 11 | Test ActiveDirectory connection + record health | app-onboarding | `test_application_connection`, `get_application_health` |
| 12 | Enable NCD on high-risk AD OUs | app-onboarding | `configure_native_change_detection` |
| 13 | Apply discovered schema attributes to SAP-Finance | app-onboarding | `discover_application_schema`, `apply_application_schema` |
| 14 | Trigger group aggregation for OpenLDAP | app-onboarding | `trigger_group_aggregation`, `get_task_result` |

### Task / schedule ops (15–19)

| # | Summary | Labels | Primary MCP |
| --- | --- | --- | --- |
| 15 | Run Identity Refresh now; triage last TaskResult failure | task-ops | `run_task_now`, `get_task_result`, `list_recent_task_failures` |
| 16 | Reschedule SAP-Finance aggregation after CST cutoff | task-ops | `list_agent_schedules`, `update_task_schedule` |
| 17 | Schedule daily open-SoD report to Helen Ross | task-ops | `upsert_task_definition`, `update_task_schedule`, `run_report` |
| 18 | Stop runaway aggregation; capture TaskResult | task-ops | `stop_aggregation`, `get_task_result` |
| 19 | Upsert TaskDefinition for nightly risk recalculation | task-ops | `upsert_task_definition`, `recalculate_risk_scores` |

### Access request / LCM (20–24)

| # | Summary | Labels | Primary MCP |
| --- | --- | --- | --- |
| 20 | Retail CSR → InternetBanking entitlement (manager approval) | access-request | `create_access_request`, `preview_access_request`, `get_access_request` |
| 21 | Revoke orphaned AWS admin after team transfer | access-request | `revoke_access` / `create_access_request`, `get_identity_accounts` |
| 22 | Batch birthright request for new branch cohort (5 users) | access-request | `submit_batch_request`, `execute_batch_request` |
| 23 | Time-boxed WireInit grant with sunset date | access-request | `create_access_request` (+ sunset), `simulate_sod_policy` |
| 24 | Complete pending access-request work item as approver bot | access-request | `list_agent_work_items`, `complete_work_item` |

### Governance admin / roles / populations (25–29)

| # | Summary | Labels | Primary MCP |
| --- | --- | --- | --- |
| 25 | Create population Kathmandu Hub risk reviewers | governance-admin | `create_population`, `preview_population_membership` |
| 26 | Add Chloe to IAM incident responders workgroup | governance-admin | `manage_workgroup_members`, `list_workgroups` |
| 27 | Birthright employee role: selector + Required IT packs | governance-admin | `list_agent_roles`, `set_role_selector`, `set_role_requirements` |
| 28 | Create IT pack role + attach entitlement profile | governance-admin | `create_role`, `attach_role_profile`, `list_managed_entitlements` |
| 29 | Soft-delete obsolete population after org restructure | governance-admin | `delete_population`, `list_populations` |

### Certification (30–33)

| # | Summary | Labels | Primary MCP |
| --- | --- | --- | --- |
| 30 | Launch manager certification for Retail Banking population | certification | `create_certification_campaign`, `launch_certification_campaign` |
| 31 | Record certify decisions for Hayes campaign sample items | certification | `make_certification_decision`, `list_certifications` |
| 32 | Sign off completed manager cert for Christopher Hayes | certification | `sign_off_certification`, `get_certification_progress` |
| 33 | Patch certification definition (email / duration) | certification | `update_certification_definition` |

### Policy / SoD (34–37)

| # | Summary | Labels | Primary MCP |
| --- | --- | --- | --- |
| 34 | Create wire exclusive Role SOD (WireInit vs WireAppr) | policy-sod | `create_sod_policy` (template **SOD Template**), `update_sod_constraints`, `list_agent_roles` |
| 35 | Simulate SoD for Finance GL + Wire initiator | policy-sod | `simulate_sod_policy`, `list_sod_policies` |
| 36 | Mitigate / exception open SoD with ≤30-day expiry | policy-sod | `list_open_sod_violations`, `create_policy_violation_exception` |
| 37 | Create Finance-Cloud SoD policy + constrain SAP_FI vs AWS_ADMIN roles | policy-sod | `create_sod_policy`, `update_sod_constraints` |

### JML lifecycle (38–40)

| # | Summary | Labels | Primary MCP |
| --- | --- | --- | --- |
| 38 | Joiner: HR agg + Identity Refresh; verify new hire searchable | jml-lifecycle | `trigger_aggregation`, `run_task_now`, `search_identities`, `run_jml_event` |
| 39 | Mover: dept birthright deltas after HR delta + refresh | jml-lifecycle | `trigger_aggregation`, `run_task_now`, `get_identity_roles` |
| 40 | Leaver: disable identity + revoke Wire/AWS access path | jml-lifecycle | `disable_identity`, `revoke_access`, `get_identity_accounts` |

---

## B. Two hundred real-life stories we cannot fully auto-close

Each row is a ticket that **routinely appears** on IAM boards. **Gap** codes are registered in [`UI-VS-API-GAPS.md`](UI-VS-API-GAPS.md) (§ Auto-story impossible board).  
**Class:** `BLOCKED` (no safe MCP path) · `HYBRID` (MCP partial; human SSD/UI/CAB) · `OUT` (outside IIQ MCP scope).

### Branding, UX, portal (41–55) — 15

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 41 | Replace IIQ login logo / favicon with bank brand | HYBRID | UIAPI-91 |
| 42 | Restyle LCM request pages to Meridian theme | HYBRID | UIAPI-91 |
| 43 | Customize password reset interstitial HTML | HYBRID | UIAPI-91 |
| 44 | Localize IIQ UI strings to Nepali | BLOCKED | UIAPI-92 |
| 45 | Build custom QuickLink icon set in theme | HYBRID | UIAPI-91 |
| 46 | Configure mobile-responsive cert UI CSS | HYBRID | UIAPI-91 |
| 47 | Embed bank privacy banner on every page | HYBRID | UIAPI-91 |
| 48 | Change default home dashboard layout widgets | HYBRID | UIAPI-93 |
| 49 | Rebrand email chrome (header/footer HTML beyond template body) | HYBRID | UIAPI-94 |
| 50 | Install custom fonts in IIQ war | BLOCKED | UIAPI-91 |
| 51 | Accessibility WCAG audit remediations in JSF | BLOCKED | UIAPI-91 |
| 52 | Custom login MFA interstitial page | HYBRID | UIAPI-95 |
| 53 | White-label plugin UI for business users | HYBRID | UIAPI-91 |
| 54 | Configure IIQ session timeout UX message copy | HYBRID | UIAPI-24* |
| 55 | Dark-mode operator console theme | OUT | UIAPI-91 |

\*Partial: `update_system_config` may set timeout; copy/UX still HYBRID.

### Rules, workflows, Beanshell, forms designer (56–85) — 30

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 56 | Author IdentityAttribute Rule for HR userId normalize | BLOCKED | UIAPI-96 |
| 57 | Live-edit correlation Rule source in Debug | BLOCKED | UIAPI-96 |
| 58 | Build LCM Provisioning Workflow with approval steps | HYBRID | UIAPI-97 |
| 59 | Add approval step to existing Access Request workflow | HYBRID | UIAPI-97 |
| 60 | Create BeforeProvisioning Rule for AD OU placement | BLOCKED | UIAPI-96 |
| 61 | Visual Forms designer: multi-page LCM form | HYBRID | UIAPI-98 |
| 62 | Drag-drop form section reorder | BLOCKED | UIAPI-98 |
| 63 | Beanshell library shared across rules | BLOCKED | UIAPI-96 |
| 64 | Workflow step email escalation ladder | HYBRID | UIAPI-97 |
| 65 | Custom Workflow subprocess for SoD exception CAB | HYBRID | UIAPI-97 |
| 66 | Rule: generate random SAMAccountName | BLOCKED | UIAPI-96 |
| 67 | Policy owner Rule (dynamic violation owner) | HYBRID | UIAPI-99 |
| 68 | Certification exclusion Rule | BLOCKED | UIAPI-96 |
| 69 | Manager correlation Rule rewrite | BLOCKED | UIAPI-96 |
| 70 | Rapid: transform joiner email domain | BLOCKED | UIAPI-96 |
| 71 | Rapid: skip aggregation for test OUs | BLOCKED | UIAPI-96 |
| 72 | Workflow: parallel approvals | HYBRID | UIAPI-97 |
| 73 | Workflow: loop until SoD clear | HYBRID | UIAPI-97 |
| 74 | Form validation Rule (SSN format) | BLOCKED | UIAPI-96 |
| 75 | QuickLink DynamicScope Rule | BLOCKED | UIAPI-100 |
| 76 | IdentityTrigger Rule (advanced) | HYBRID | UIAPI-101 |
| 77 | Build Lifecycle Event from UI wizard end-to-end | HYBRID | UIAPI-101 |
| 78 | Clone OOTB LCM Identity Create workflow | HYBRID | UIAPI-97 |
| 79 | Workflow Unit test harness in IIQ | BLOCKED | UIAPI-102 |
| 80 | Debug Beanshell in production console | BLOCKED | UIAPI-103 |
| 81 | Import Rule from Git with syntax check only | HYBRID | UIAPI-96 |
| 82 | Diff two Rule revisions in UI | BLOCKED | UIAPI-104 |
| 83 | Approve: password generation complexity | BLOCKED | UIAPI-96 |
| 84 | Workflow wait-for-manual step UX | HYBRID | UIAPI-97 |
| 85 | Form field conditional visibility designer | BLOCKED | UIAPI-98 |

### Connector / application deep UI (86–110) — 25

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 86 | AD connector forest/domain wizard full click-path | HYBRID | UIAPI-105 |
| 87 | Configure AD IQService host certificates | HYBRID | UIAPI-105 |
| 88 | JDBC connector SQL map builder UI | HYBRID | UIAPI-106 |
| 89 | Web Services connector OAuth2 interactive authorize | HYBRID | UIAPI-107 |
| 90 | SCIM connector paging/auth deep settings | HYBRID | UIAPI-107 |
| 91 | Salesforce connector OAuth connected app dance | HYBRID | UIAPI-107 |
| 92 | SAP JCo destination configuration UI | HYBRID | UIAPI-108 |
| 93 | Mainframe RACF connector install | OUT | UIAPI-109 |
| 94 | Logical application composition UI | HYBRID | UIAPI-110 |
| 95 | Application dependency graph editor | BLOCKED | UIAPI-110 |
| 96 | Connector debug trace UI session | HYBRID | UIAPI-103 |
| 97 | Account schema attribute drag reorder | HYBRID | UIAPI-111 |
| 98 | Group schema custom objectClass wizard | HYBRID | UIAPI-111 |
| 99 | Delta aggregation watermark UI reset | HYBRID | UIAPI-112 |
| 100 | Partitioned aggregation host affinity | HYBRID | UIAPI-112 |
| 101 | Multi-host connector load balance | HYBRID | UIAPI-112 |
| 102 | Application maintenance window calendar UI | BLOCKED | UIAPI-113 |
| 103 | Connector registry custom type JAR deploy | BLOCKED | UIAPI-114 |
| 104 | Proxy/bastion settings for connector | HYBRID | UIAPI-105 |
| 105 | Test connection with uploaded keystore UI | HYBRID | UIAPI-115 |
| 106 | Application risk score weight UI (beyond MCP patch) | HYBRID | UIAPI-116 |
| 107 | Composite application account correlation UI | HYBRID | UIAPI-110 |
| 108 | Unstructured target collection setup | HYBRID | UIAPI-117 |
| 109 | File feed SFTP credential vault UI | HYBRID | UIAPI-118 |
| 110 | Connector retry/backoff UI presets | HYBRID | UIAPI-112 |

### Privileged access / PAM / secrets (111–125) — 15

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 111 | Integrate CyberArk safe sync | OUT | UIAPI-119 |
| 112 | BeyondTrust session broker | OUT | UIAPI-119 |
| 113 | Break-glass checkout workflow with video | HYBRID | UIAPI-119 |
| 114 | Privileged session recording retention | OUT | UIAPI-119 |
| 115 | Rotate shared vault password nightly | OUT | UIAPI-118 |
| 116 | Just-in-time AD admin via PAM | OUT | UIAPI-119 |
| 117 | SSH certificate authority for servers | OUT | UIAPI-119 |
| 118 | Secrets Manager sync to IIQ | OUT | UIAPI-118 |
| 119 | Dual control on root password reveal | OUT | UIAPI-119 |
| 120 | PAM SoD with standing access ban | HYBRID | UIAPI-119 |
| 121 | Emergency access firecall list SMS | OUT | UIAPI-120 |
| 122 | Hardware token enrollment | OUT | UIAPI-95 |
| 123 | Privileged account discovery scan | OUT | UIAPI-119 |
| 124 | Domain admin tiering model in PAM | OUT | UIAPI-119 |
| 125 | Cloud IAM privilege broker (AWS PE) | OUT | UIAPI-121 |

### AuthN / federation / MFA (126–140) — 15

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 126 | Configure SAML IdP metadata upload | HYBRID | UIAPI-95 |
| 127 | OIDC RP client registration UI | HYBRID | UIAPI-95 |
| 128 | Force MFA step-up for Wire Approver | HYBRID | UIAPI-95 |
| 129 | Passwordless WebAuthn for operators | OUT | UIAPI-95 |
| 130 | Kerberos SSO for IIQ | HYBRID | UIAPI-95 |
| 131 | Conditional access by geo for IIQ login | OUT | UIAPI-95 |
| 132 | SCIM inbound from Entra ID | HYBRID | UIAPI-122 |
| 133 | Just-in-time federation provisioning | HYBRID | UIAPI-122 |
| 134 | Certificate-based auth for API accounts | HYBRID | UIAPI-123 |
| 135 | Rotate IIQ service account passwords via GPO | OUT | UIAPI-118 |
| 136 | Disable basic auth on IIQ | HYBRID | UIAPI-24* |
| 137 | Session fixation hardening review | BLOCKED | UIAPI-124 |
| 138 | CAPTCHA on login | HYBRID | UIAPI-91 |
| 139 | Impossible travel alerts for IIQ admins | OUT | UIAPI-125 |
| 140 | Federated logout SLO end-to-end | HYBRID | UIAPI-95 |

### Compliance, audit, reporting beyond MCP (141–160) — 20

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 141 | Produce FFIEC exam binder PDF pack | HYBRID | UIAPI-126 |
| 142 | SOX 404 access evidence zip | HYBRID | UIAPI-126 |
| 143 | FedRAMP continuous monitoring export | OUT | UIAPI-126 |
| 144 | GDPR DSARs export across apps | HYBRID | UIAPI-127 |
| 145 | Right-to-erasure orchestration | HYBRID | UIAPI-127 |
| 146 | Custom Jasper report pixel-perfect layout | BLOCKED | UIAPI-128 |
| 147 | Crystal/Jasper Studio authoring | BLOCKED | UIAPI-128 |
| 148 | Board risk heatmap slide deck | HYBRID | UIAPI-129 |
| 149 | Continuous control monitoring dashboard | HYBRID | UIAPI-129 |
| 150 | SIEM CEF stream of IIQ audits | OUT | UIAPI-125 |
| 151 | Splunk HEC integration | OUT | UIAPI-125 |
| 152 | Immutable WORM audit store | OUT | UIAPI-125 |
| 153 | Attestation letter generation (legal) | HYBRID | UIAPI-126 |
| 154 | Control mapping to NIST 800-53 | OUT | UIAPI-126 |
| 155 | Third-party SOC2 evidence request | HYBRID | UIAPI-126 |
| 156 | Access review sampling methodology doc | HYBRID | UIAPI-126 |
| 157 | Model risk documentation for AI access bots | OUT | UIAPI-130 |
| 158 | Data classification labeling in IIQ | HYBRID | UIAPI-131 |
| 159 | Retention schedule purge job UI | HYBRID | UIAPI-132 |
| 160 | eDiscovery legal hold on identities | HYBRID | UIAPI-127 |

### Data quality, HR, org design (161–180) — 20

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 161 | Fix HR feed column shift (bad CSV) | HYBRID | UIAPI-133 |
| 162 | Author HR ETL outside IIQ | OUT | UIAPI-133 |
| 163 | Rebuild entire org chart from Workday API | HYBRID | UIAPI-134 |
| 164 | Position management integration | OUT | UIAPI-134 |
| 165 | Cost-center hierarchy sync | HYBRID | UIAPI-134 |
| 166 | Contractor vendor master sync | HYBRID | UIAPI-134 |
| 167 | Duplicate identity merge policy (business) | HYBRID | UIAPI-135 |
| 168 | Soft-delete vs hard-delete identity standards | HYBRID | UIAPI-135 |
| 169 | Historical identity archive warehouse | OUT | UIAPI-132 |
| 170 | Rehire detection fuzzy match ML | OUT | UIAPI-130 |
| 171 | Nickname / aka attribute governance | HYBRID | UIAPI-136 |
| 172 | Preferred name vs legal name UX | HYBRID | UIAPI-136 |
| 173 | Manager vacant seat routing | HYBRID | UIAPI-137 |
| 174 | Matrix manager (dotted line) model | HYBRID | UIAPI-137 |
| 175 | Location → OU mapping spreadsheet import | HYBRID | UIAPI-133 |
| 176 | Job code taxonomy change management | HYBRID | UIAPI-138 |
| 177 | Birthright matrix Excel → roles codegen | HYBRID | UIAPI-138 |
| 178 | SoD matrix Excel → policies codegen | HYBRID | UIAPI-139 |
| 179 | Entitlement dictionary business glossary | HYBRID | UIAPI-131 |
| 180 | Orphan account business owner assignment campaign | HYBRID | UIAPI-140 |

### Platform, HA, performance, DevOps (181–200) — 20

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 181 | Blue/green IIQ upgrade 8.4→8.5 | OUT | UIAPI-141 |
| 182 | Patch IIQ hotfixes with downtime plan | OUT | UIAPI-141 |
| 183 | Cluster session replication tuning | OUT | UIAPI-142 |
| 184 | DB index rebuild for spt_identity | OUT | UIAPI-143 |
| 185 | PostgreSQL vacuum / partitioning | OUT | UIAPI-143 |
| 186 | JVM heap / GC tuning | OUT | UIAPI-142 |
| 187 | Horizontal scale task hosts | OUT | UIAPI-142 |
| 188 | Backup/restore runbook drill | OUT | UIAPI-144 |
| 189 | DR failover to secondary DC | OUT | UIAPI-144 |
| 190 | Kubernetes helm values for IIQ | OUT | UIAPI-145 |
| 191 | Image CVE remediation pipeline | OUT | UIAPI-145 |
| 192 | Secrets rotation for iiq.properties | HYBRID | UIAPI-118 |
| 193 | mTLS for plugin REST | HYBRID | UIAPI-123 |
| 194 | Rate-limit public plugin APIs | HYBRID | UIAPI-146 |
| 195 | WAF rules for /identityiq | OUT | UIAPI-146 |
| 196 | Chaos test kill task host mid-agg | OUT | UIAPI-147 |
| 197 | Performance soak test LCM | OUT | UIAPI-147 |
| 198 | OpenTelemetry full IIQ traces | OUT | UIAPI-148 |
| 199 | Multi-tenant IIQ (separate banks) | OUT | UIAPI-149 |
| 200 | Decommission IIQ for SaaS IGA migration | OUT | UIAPI-150 |

### Cloud IGA / peer products / org process (201–220) — 20

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 201 | Migrate campaign to IdentityNow | OUT | UIAPI-150 |
| 202 | ISC SaaS connector replace IIQ app | OUT | UIAPI-150 |
| 203 | ServiceNow CMDB sync to IIQ apps | HYBRID | UIAPI-151 |
| 204 | ServiceNow RITM → IIQ access request | HYBRID | UIAPI-151 |
| 205 | Jira Service Management auto-create KAN | OUT | UIAPI-152 |
| 206 | Slack approval bot for access | OUT | UIAPI-152 |
| 207 | Teams adaptive card approvals | OUT | UIAPI-152 |
| 208 | CAB ticket mandatory for SoD exception | HYBRID | UIAPI-153 |
| 209 | Change freeze calendar enforcement | OUT | UIAPI-153 |
| 210 | IAM runbook Confluence publish | OUT | UIAPI-126 |
| 211 | Tabletop incident: mass unlock | HYBRID | UIAPI-154 |
| 212 | Ransomware identity containment playbook | HYBRID | UIAPI-154 |
| 213 | Insider threat watchlist integration | OUT | UIAPI-125 |
| 214 | UEBA risk feed into IIQ scores | OUT | UIAPI-130 |
| 215 | Contractor badge system join | OUT | UIAPI-155 |
| 216 | Physical access SoD with logical | OUT | UIAPI-155 |
| 217 | Vendor risk portal onboarding | OUT | UIAPI-156 |
| 218 | Fourth-party access attestation | OUT | UIAPI-156 |
| 219 | M&A identity domain merger | HYBRID | UIAPI-135 |
| 220 | Divestiture identity cutover | HYBRID | UIAPI-135 |

### Advanced IIQ features thinly covered (221–240) — 20

| # | Story | Class | Gap |
| --- | --- | --- | --- |
| 221 | Full Rapid Setup click-path | HYBRID | UIAPI-157 |
| 222 | IdentityAI recommendations accept UI | OUT | UIAPI-130 |
| 223 | Access History deep UI analytics | HYBRID | UIAPI-158 |
| 224 | AI role mining accept/reject UX | HYBRID | UIAPI-159 |
| 225 | Peer group outlier certification | HYBRID | UIAPI-159 |
| 226 | Sensitive data discovery (file) | OUT | UIAPI-117 |
| 227 | Unstructured target permissions UI | HYBRID | UIAPI-117 |
| 228 | Activity monitoring policy full UI | HYBRID | UIAPI-160 |
| 229 | Risk model weight designer UI | HYBRID | UIAPI-116 |
| 230 | Advanced Analytics saved search share | HYBRID | UIAPI-161 |
| 231 | Identity snapshot compare UI | HYBRID | UIAPI-162 |
| 232 | Account group inheritance visualizer | HYBRID | UIAPI-163 |
| 233 | Entitlement catalog business request portal | HYBRID | UIAPI-164 |
| 234 | Password sync interceptor config | HYBRID | UIAPI-165 |
| 235 | Desktop Password Reset client | OUT | UIAPI-165 |
| 236 | IIQ Mobile app push approvals | OUT | UIAPI-152 |
| 237 | Offline work item sync | OUT | UIAPI-152 |
| 238 | Electronic signature meaning legal text | HYBRID | UIAPI-166 |
| 239 | Policy simulation UI campaign mode | HYBRID | UIAPI-167 |
| 240 | Full Debug pages / Beanshell console ops | BLOCKED | UIAPI-103 |

---

## C. Count check

| Bucket | Count |
| --- | --- |
| Possible (MCP_E2E auto-story) | **40** (§A #1–40) |
| Impossible / incomplete (gap board) | **200** (§B #41–240) |
| **Total catalogued** | **240** |

---

## D. How to use with auto-story

1. File any §A story in KAN → labels `agent-ready` + type → Poll UI / CLI.  
2. §B stories: label `blocked-needs-human` (or leave unlabeled); do **not** expect In Review from auto-story alone.  
3. Gaps UIAPI-91…167 are tracked in [`UI-VS-API-GAPS.md`](UI-VS-API-GAPS.md) for prioritization — not a commitment to implement.

_Last updated: board-back catalog v1 (40 possible / 200 gap)._
