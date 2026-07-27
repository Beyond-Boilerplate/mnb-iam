# Lesson 88 — Connector Gateway / Cloud Patterns

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 90–120 min  
**Prereq:** Lesson 87 — Duo MFA Integration Patterns; Lessons 74–76 (Google, M365, AWS) recommended for the design worksheet  

**Lab data:**
- Repo: `lab-data/connectors/README.md`
- Repo: `lab-data/connectors/ad/iqservice-checklist.md`
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Runtime: `~/iiq-lab-data/connectors/gateway/`
- Optional: `docker-compose.connectors.yml` at repo root

---

## Learning objectives

You will be able to:

- Explain how on-prem IdentityIQ reaches SaaS and cloud APIs under bank network constraints (proxy / gateway / VA-like hosts, outbound-only firewalls)
- Distinguish **IQService**, **Cloud Gateway / VA-style connector hosts**, and **direct-from-IIQ** paths — and know when each is wrong
- Complete a Meridian placement and allowlist design worksheet for Google Workspace, M365, and AWS connectors from earlier lessons
- Document TLS, outbound allowlists, TLS inspection risks, and secret distribution for gateway hosts
- Define ops SLAs that separate gateway health failures from Application aggregation logic failures

---

## Why this matters

**Business.** Meridian’s IdentityIQ runs in the bank’s on-prem / private cloud estate. Targets do not: Google Workspace, Microsoft 365, and AWS IAM live on the public internet; AD and RACF live in locked segments. When `helen.ross` schedules nightly aggregations and every SaaS Task Result fails with timeouts, the business sees “IAM is down” — usually the gateway host, egress allowlist, or TLS inspection path is the real culprit. Connectors designed in Lessons 74–76 are useless without a path that Security will actually approve.

**Control / audit.** Examiners and network security ask: what leaves the bank, to which FQDNs, with which credentials, over which TLS trust? Outbound-only designs (no inbound from internet to IIQ) are the default Meridian answer. Residual risk remains: brittle allowlists, TLS inspection breaking mutual TLS, and connector secrets sitting cleartext on a DMZ host. This lesson makes those risks explicit and owned.

---

## Concepts

### The problem: IIQ is inside; SaaS is outside

IdentityIQ application servers often cannot (and should not) have unrestricted internet egress. Meridian’s firewall posture is **outbound-only** for connector traffic to approved destinations — no inbound connections from Google/Microsoft/AWS into the IIQ tier. Something must originate TLS from a controlled host:

| Pattern | What it is | Meridian use |
| --- | --- | --- |
| **Direct from IIQ** | App server calls APIs itself | Lab laptops / open lab nets only — not bank prod default |
| **IQService** | Windows service near AD/Windows targets | AD Direct, Windows Local (Lesson 84 family) |
| **Cloud Gateway / VA-like host** | Hardened host or appliance that runs connector traffic with controlled egress | SaaS/cloud APIs when IIQ pods lack egress |
| **File / Delimited proxy** | Extract dropped for IIQ to read | Training fallback or regulated batch — not continuous cloud truth |

“VA-like” here means **Virtual Appliance–style** connector hosting patterns familiar from SailPoint cloud deployments — a dedicated connector runtime separate from the UI/task engines. Exact product packaging differs by IdentityIQ version and deployment; Meridian’s teaching point is **architectural separation**, not a single SKU name. Never invent UI labels for a gateway product you have not verified in your build.

### Meridian bank network constraints (typical)

```
┌─────────────────┐   no raw internet    ┌──────────────────────┐
│ IdentityIQ      │ ───────────────────► │ Cloud Gateway /      │
│ (K8s / VM)      │      TLS internal      │ VA-like connector    │
└─────────────────┘                      │ host (DMZ/egress)    │
                                         └──────────┬───────────┘
                                                    │ outbound-only
                                                    │ allowlisted FQDNs
                         ┌──────────────────────────┼──────────────────────────┐
                         ▼                          ▼                          ▼
                   Google APIs                Microsoft Graph              AWS IAM API
                   (Lesson 74)                (Lesson 75)                 (Lesson 76)

Separate path:
 IdentityIQ ──TLS──► IQService (AD tier) ──► Domain Controllers
```

Rules of thumb:

1. **AD / Windows** → IQService in the AD tier (see `iqservice-checklist.md`).
2. **SaaS / public cloud APIs** → gateway/VA-like egress host with allowlists.
3. **Mainframe / segmented DBs** → segment-local gateway or approved middleware — not the SaaS DMZ host.
4. **Never** install IQService “for convenience” on the IIQ UI container.

### Residual risks you must name

| Risk | Why it hurts | Mitigations |
| --- | --- | --- |
| Outbound allowlists incomplete | Aggregations fail after vendor IP/FQDN changes | Monitor Task Results; change process with Network; prefer FQDN docs from vendors |
| TLS inspection (SSL break-and-inspect) | Breaks client cert / pinning / some OAuth flows | Exclude connector egress from inspection or install bank CA correctly — Security-approved design |
| Credential storage on gateway | DMZ host becomes a treasure chest | OS secret store / HSM patterns; no cleartext in config files; rotate ≤90 days |
| Blast radius | One host holds keys for Google + M365 + AWS | Split gateways by risk domain where feasible; least-privilege AppIDs per target |

---

## How it works

```
Task server triggers Account Aggregation (MNB-Google-Workspace, etc.)
        │
        ▼
IIQ connector framework
        │  either direct OR delegated to gateway/IQService
        ▼
Controlled egress host ──TLS 1.2+──► Vendor API
        │
        ▼
Paged accounts/entitlements → IIQ Task Result (audit evidence)
```

| Failure class | Looks like | Check first | Owner |
| --- | --- | --- | --- |
| Gateway down | Many SaaS apps fail together | Host process, disk, cert expiry | Platform |
| Allowlist miss | One vendor fails; others OK | Egress logs / denied FQDN | Network + Platform |
| Bad secrets | 401/403 on one app | Vaulted credential / App registration | App owner + IAM |
| IQService down | AD / Windows only | Windows service + TLS to IIQ | Windows Ops |
| IIQ task engines stuck | Everything queued | Task servers / queues | IAM Ops |

---

## Real-world setup (outside IIQ)

Production engineers negotiate this **before** turning on Google/M365/AWS connectors:

### Step 1 — Choose the path per connector class

1. Classify each Meridian application: on-prem directory, database, SaaS, cloud IAM, mainframe, PAM.
2. Assign path type: IQService / Gateway / Direct (lab only) / File proxy.
3. Get Security architecture sign-off on outbound-only design.

### Step 2 — Build the egress allowlist

1. From vendor documentation, list required FQDNs (token endpoints + API endpoints) for Google Admin SDK, Microsoft Graph/Entra, AWS IAM.
2. Submit firewall change: source = gateway host(s); destination = those FQDNs; ports 443.
3. Reject “allow \*.googleapis.com to the whole IIQ subnet” when a dedicated gateway exists — keep blast radius small.

### Step 3 — TLS and inspection

1. Require TLS to all targets; manage trust stores on the gateway.
2. Document whether TLS inspection applies; if yes, coordinate exclusions or bank CA install **before** go-live testing.
3. Cert expiry monitoring (&lt; 30 days warning) on gateway and IQService hosts.

### Step 4 — Secret distribution

1. Connector secrets live in the bank secret store; injected at runtime to IIQ/gateway — not baked into images.
2. Separate credentials per major SaaS (Google SA key, M365 app registration secret/cert, AWS connector role/keys).
3. Record rotation owners and dates.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`
- [ ] Read `lab-data/connectors/README.md` live-vs-lab statement
- [ ] IQService checklist available at `lab-data/connectors/ad/iqservice-checklist.md`
- [ ] Recall design cards from Lessons 74–76 if completed (`MNB-Google-Workspace`, M365, `MNB-AWS-IAM`)
- [ ] Binder: `~/iiq-lab-data/connectors/gateway/`
- [ ] No production secrets in worksheets

---

## Lab procedure

### Task 1 — Inventory connector network needs

Ground the architecture in Meridian’s actual connector classes — not abstracts.

1. From the selection matrix and your course progress, classify at least these rows into path types:

| System class | Example Meridian app | Path type |
| --- | --- | --- |
| On-prem directory | `MNB-ActiveDirectory` | IQService |
| Windows local | Windows Local apps | IQService |
| SaaS collaboration | `MNB-Google-Workspace` | Cloud Gateway / VA-like |
| SaaS M365 | M365 / SharePoint Online app | Cloud Gateway / VA-like |
| Cloud IAM | `MNB-AWS-IAM` | Cloud Gateway / VA-like |
| Privileged vault | `MNB-PAM-CyberArk` | Segment / controlled path to PVWA |
| Mainframe | RACF (if in curriculum) | Segment gateway |
| Training file | Delimited extracts | File proxy / direct read |

2. Save as `~/iiq-lab-data/connectors/gateway/path-classification.md` (minimum **6** rows).

**Expected result:** Classification table with path type per system class.

**If it fails:** Use AD=IQService, SaaS=Gateway, RACF=segment gateway, CSV=file as the minimum set.

### Task 2 — Meridian placement worksheet

Fill and file:

| Host role | Example name | Zone | Owns patching | Stores connector secrets? |
| --- | --- | --- | --- | --- |
| IIQ app | `iiq-app` | App | Platform | Prefer no — inject at runtime |
| IIQ task | `iiq-task` | App | Platform | Prefer no |
| IQService | `iqsvc-ad-01` | AD tier | Windows Ops | Minimal; AD bind as designed |
| Cloud Gateway | `mnb-gw-saas-01` | DMZ/egress | Platform | Yes — hardened secret store |
| Connector stubs | docker compose | Laptop | Trainee | Lab placeholders only |

1. Require TLS everywhere; note cert owner (Platform or Windows Ops).
2. State anti-pattern: IQService on the IIQ app container.

**Expected result:** Placement worksheet with zones, owners, and secret locations.

### Task 3 — IQService vs Cloud Gateway contrast

1. Open `lab-data/connectors/ad/iqservice-checklist.md` and annotate: used for Windows/AD operations near DCs.
2. Write **five** bullets for Cloud Gateway / VA-like hosts:
   - Outbound allowlist only (no inbound from internet to IIQ)
   - Mutual TLS or equivalent to IIQ where the architecture requires it
   - Health endpoint / process monitoring independent of IIQ UI
   - Separate autoscaling / patching from IIQ application pods
   - Per-vendor credentials — not one shared “internet password”
3. Write **three** bullets for IQService: Windows service, AD proximity, TLS back to IIQ.
4. Explicit anti-pattern line: installing IQService on the IIQ UI/app container “for convenience.”

**Expected result:** Contrast page in the binder.

**If it fails:** Minimum three bullets each still passes; expand when you can.

### Task 4 — Design worksheet: Google / M365 / AWS egress

Reuse earlier connector lessons. For each, document FQDN categories (not every ephemeral IP) and secret type:

| Connector | Egress needed (categories) | Secret material | Gateway notes |
| --- | --- | --- | --- |
| `MNB-Google-Workspace` (L74) | Google OAuth token endpoint + Admin SDK Directory API hosts | Service account JSON key (vaulted) + admin impersonation email | DWD scopes unchanged; path is network |
| M365 / SharePoint Online (L75) | Microsoft identity platform token + Graph endpoints | App registration cert/secret | Prefer cert auth |
| `MNB-AWS-IAM` (L76) | `iam.amazonaws.com` (global IAM API) via SigV4 | Connector user keys **or** AssumeRole | Prefer role assumption; keys if unavoidable rotate ≤90d |

1. Create `~/iiq-lab-data/connectors/gateway/saas-egress-design.md` with the table above plus: source host `mnb-gw-saas-01`, port 443, outbound-only, change ticket stub field.
2. Add a line for TLS inspection: “Inspection enabled? Y/N — if Y, exclusion or bank CA plan: ____.”

**Expected result:** SaaS egress design worksheet covering all three cloud connectors.

**If it fails:** Complete Google + AWS rows at minimum; leave M365 as “same gateway pattern / Graph allowlist TBD.”

### Task 5 — Lab docker / stub awareness

1. Open repo `docker-compose.connectors.yml` if present; list stub services (LDAP/DB/etc.).
2. Write three sentences: stubs are **learn track**, not a production gateway; they do not implement bank DMZ allowlists; homelab CD (if any) differs from Meridian egress control.
3. Optional: note which local stubs still taught connector mechanics without public internet.

**Expected result:** Short note distinguishing lab stubs vs enterprise gateway.

**If it fails:** Skip compose; still complete Tasks 1–4 and 6–8.

### Task 6 — Failure matrix and SLAs

Extend the ops view:

| Symptom | Check first | Owner | Severity hint |
| --- | --- | --- | --- |
| All AD provisioning fails | IQService service / TLS | Windows Ops | Sev2 if prolonged |
| One SaaS app fails | Gateway allowlist / API creds | Platform + App owner | Sev3→Sev2 if privileged |
| All SaaS aggregations fail | Gateway host health / shared egress | Platform | Sev2 |
| All aggregations stuck | IIQ task servers | IAM Ops | Sev2 |
| Intermittent timeouts | Network path / DNS / inspection | Network | Investigate Sev3 |

Add Meridian SLA lines: gateway host disk/CPU/cert alert = **Sev3**; complete connector egress outage = **Sev2**; privileged cloud aggregation dark &gt; 24h = escalate toward **Sev1** per local major-incident policy.

**Expected result:** Failure matrix + SLA lines in the binder.

### Task 7 — Residual risk register

Record at least:

1. **`RR-GW-ALLOW-01`:** Vendor FQDN/IP changes break allowlists → compensating: Task Result alarms + Network change window ownership. Owner: Platform.
2. **`RR-GW-TLS-01`:** TLS inspection may break connector auth → compensating: documented exclusion or CA strategy before prod. Owner: Security architecture.
3. **`RR-GW-SECRET-01`:** Gateway disk cleartext secrets → compensating: secret store / HSM pattern; scrub configs from backups. Owner: Platform + IAM.

**Expected result:** Three residual risks with owners and compensating controls.

### Task 8 — Lab-without-live-target acceptance path

1. Do **not** require a live Cloud Gateway or production firewall change.
2. Attach: classification table, placement worksheet, IQService vs Gateway contrast, SaaS egress design (Google/M365/AWS), failure matrix, residual risks.
3. Optional: on one existing SaaS Application Description, note “Expected path: Cloud Gateway / VA-like egress host” — without inventing product-specific UI labels.

**Expected result:** Six artifacts bound; optional Application annotation.

---

## Acceptance criteria

- [ ] System class → path type table complete (≥6 rows)
- [ ] Placement worksheet with zones, owners, secret locations
- [ ] IQService vs Gateway contrast written (anti-pattern included)
- [ ] SaaS egress design covers Google, M365, and AWS patterns
- [ ] Lab stubs vs enterprise note written (or compose skipped with note)
- [ ] Failure matrix + SLAs + `RR-GW-*` residual risks documented
- [ ] No secrets committed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| IIQ pod cannot reach SaaS | Egress policy / no gateway route | Route via gateway allowlist |
| AD works in DC, fails from K8s | Missing IQService path | Place IQService near AD; fix TLS |
| TLS handshake errors | Trust store / inspection | Fix gateway trust; review inspection exclusions |
| Only Google fails; M365 OK | Allowlist or Google SA key | Check Admin SDK hosts + vaulted key |
| AWS `AccessDenied` after network OK | IAM policy — not gateway | Return to Lesson 76 connector policy |
| Trainee blocked | No live GW | Use worksheet acceptance path |
| Secrets on gateway disk cleartext | Bad install | OS secret store / HSM pattern; rotate |

---

## Training binder evidence

- Path classification table
- Placement worksheet
- IQService vs Gateway contrast
- `saas-egress-design.md` (Google / M365 / AWS)
- docker-compose / lab stub note
- Failure matrix + SLAs
- `RR-GW-ALLOW-01`, `RR-GW-TLS-01`, `RR-GW-SECRET-01`
- Optional Application “Expected path” note

---

## Knowledge check

1. What Windows component commonly fronts AD Direct at Meridian?
2. Why separate a Cloud Gateway / VA-like host from the IIQ UI pod?
3. What firewall posture does Meridian prefer for SaaS connector traffic?
4. Name two residual risks of gateway-based SaaS connectivity.
5. Are docker connector stubs production gateways?
6. Who typically owns IQService patching vs SaaS gateway patching in the placement worksheet?

### Answers

1. IQService.
2. Controlled egress, blast-radius isolation, independent health/scaling/patching from the UI.
3. Outbound-only from a controlled gateway host to allowlisted FQDNs — no inbound from internet to IIQ.
4. Any two of: brittle allowlists, TLS inspection breakage, cleartext secrets on the gateway, shared blast radius across vendors.
5. No — learn/lab stubs only.
6. Windows Ops for IQService; Platform for the Cloud Gateway host (per worksheet).

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “IQService”, connector gateway, and your version’s deployment guidance for hybrid connectivity.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — threads on aggregation timeouts, proxy/egress, and IQService TLS issues.
- Repo: `lab-data/connectors/ad/iqservice-checklist.md` — Meridian’s AD-near checklist companion to this lesson.
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) — complementary view of authenticated sessions; useful when explaining why TLS and credential handling on gateways matter.
- [FFIEC Information Security / Architecture topics](https://www.ffiec.gov/) — search the IT Handbook for network security and perimeter concepts that frame outbound allowlists and DMZ placement in exams.
- Vendor allowlist starting points: Google API / Admin SDK docs, Microsoft Graph endpoint docs, and AWS IAM API endpoints — always pull current FQDNs from vendor documentation when opening firewall changes.

---

## Stretch lab

Draft a Prometheus-style (or equivalent) health checklist for gateway hosts: process up, cert expiry &lt; 30 days, disk &gt; 20% free, recent successful test connection per major SaaS app. Then propose splitting `mnb-gw-saas-01` into separate Google/M365 vs AWS gateways — write the blast-radius rationale in one paragraph.

---

## Summary

- On-prem IIQ reaches SaaS/cloud through controlled outbound paths (gateway/VA-like hosts) and reaches AD through IQService — not through unrestricted pod egress.
- Google, M365, and AWS connectors need explicit allowlists, TLS plans, and vaulted secrets on hardened hosts.
- Ops must separate gateway failure from application logic failure; residual risks around allowlists, TLS inspection, and secret storage stay owned.

---

**Previous:** [Lesson 87 — Duo MFA Integration Patterns](87-duo-mfa-integration-patterns.md)  
**Next:** [Lesson 89 — Rule Types Catalog](89-rule-types-catalog.md)
