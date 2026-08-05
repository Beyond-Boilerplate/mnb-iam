# Lesson 86 — PAM / CyberArk Module

**Level:** Advanced  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 90–120 min  
**Prereq:** Lesson 85 — Logical Applications; Lesson 28 — Privileged Access Roles; Lesson 37 — Break-Glass strongly recommended  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Privileged vault row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/pam/`
- **Live enterprise path:** `./tools/lab/docker/up.sh --enterprise` → Vault `:8200` + pam-lab `:8097` — Sandbox Lesson [255](255-privileged-vault-checkout.md) / [`lab-data/enterprise/pam/README.md`](../../lab-data/enterprise/pam/README.md)

---

## Learning objectives

You will be able to:

- Position **CyberArk / PAM module** connectors as privileged account governance — not birthright IAM or a password spreadsheet replacement alone
- Explain the vault object model (safes, platforms, accounts, checkout, session recording, rotation) and how IIQ maps onto it
- Create Application shell **`MNB-PAM-CyberArk`** with a safe/account entitlement model suitable for lab-without-live-target work
- Align IIQ privileged roles (`CloudAdmin`, BreakGlass from Lessons 28 and 37) with vault dual-control: request → approval → safe membership
- Produce examiner-ready evidence for **password rotation** and **checkout** without requiring a live CyberArk tenant

---

## Why this matters

**Business.** Shared root, Domain Admin, cloud break-glass, and payment-switch passwords must live in a vault with checkout controls and session recording — not in tickets, password managers shared by a team chat, or a spreadsheet on a jump host. When `jordan.reed` needed emergency cloud admin access during an outage, the correct path was a time-bound BreakGlass role that provisioned membership into a CyberArk safe — not a Slack DM with a static password. The wrong path is how privileged credentials become immortal.

**Control / audit.** Examiners ask whether privileged passwords **rotate**, who can **check out** break-glass credentials, whether sessions are recorded, and how IAM requests relate to vault membership. IIQ without PAM leaves the highest-risk accounts half-governed: you may certify a role named CloudAdmin while the actual password still sits unmanaged. This lesson builds the joined story: IIQ owns request/approval/evidence; CyberArk owns vault mechanics.

---

## Concepts

### Privileged access is not birthright

Birthright (joiner defaults) must never include vault safes that hold Domain Admin, cloud root-equivalent, or payment-switch credentials. Privileged access is **request-only**, dual-approved, time-aware where BreakGlass applies, and continuously inventoriable. Lesson 28’s `CloudAdmin` and Lesson 37’s BreakGlass patterns are the IIQ-side language; CyberArk is where those entitlements become real credential custody.

### The CyberArk object model (governance view)

| CyberArk object | What it is | Meridian example |
| --- | --- | --- |
| **Safe** | Access-controlled container of privileged accounts | `MNB-Safe-CloudAdmin`, `MNB-Safe-BreakGlass-AD`, `MNB-Safe-Payments-Switch` |
| **Platform** | Policy template (rotation interval, complexity, reconciliation) | Windows Domain, AWS console/API, network device |
| **Account** | A privileged credential managed in a safe | `mnb-da-breakglass`, cloud emergency user |
| **Checkout** | Temporary retrieval / use of a password (often exclusive) | Engineer checks out DA for a change window |
| **Session recording / PSM** | Proxied interactive session with audit video/log | Jump to domain controller via PSM |
| **Rotation** | Automatic or forced password change after use / on schedule | Post-checkout rotate; 30/60/90-day platform policy |

IIQ typically treats **safe membership** (and sometimes links to specific privileged accounts) as entitlements. Checkout, recording, and rotation remain PAM-platform operations — but your governance story must *prove they exist*, not pretend IIQ performs them.

### IIQ request → approval → vault membership

```
Identity Request (role or PAM entitlement)
        │
        ▼
 Approvals (e.g. Tech Director + Security)     ← IIQ evidence
        │
        ▼
 Provision: add user to CyberArk safe          ← connector / PAM module
        │
        ▼
 Checkout / PSM session / rotate               ← CyberArk platform
        │
        ▼
 Account Aggregation → safe membership on cube ← continuous inventory
```

| Layer | Owner | Meridian object |
| --- | --- | --- |
| Governance / request | IAM | `MNB-PAM-CyberArk`, privileged roles |
| Vault operations | PAM team | Safes, platforms, accounts, rotation |
| Platform / jump | Ops | PSM, connectors, jump hosts |
| Security policy | Security (`amelia.brooks`) | Who may request; BreakGlass rules |

### Aligning CloudAdmin and BreakGlass

| IIQ construct (Lessons 28 / 37) | Vault target | Standing vs temporary |
| --- | --- | --- |
| Role `MNB-Role-CloudAdmin` (or equivalent CloudAdmin) | Safe `MNB-Safe-CloudAdmin` | Standing privileged — monthly cert |
| BreakGlass assignment (Lesson 37) | Safe `MNB-Safe-BreakGlass-AD` | Time-bound (lab: 8 hours) + mandatory remove |
| Payments privileged operators | Safe `MNB-Safe-Payments-Switch` | Request-only; dual control with payments SoD |

The naive failure: granting CloudAdmin in IIQ with no vault membership — theater governance. The opposite failure: vault membership with no IIQ request trail — invisible privilege.

---

## How it works

The SailPoint CyberArk / PAM module (exact connector name varies by IdentityIQ version and licensed pack) integrates with CyberArk’s API / PVWA so IdentityIQ can aggregate vault users and safe memberships and, when enabled, provision add/remove.

```
IdentityIQ (MNB-PAM-CyberArk)
        │  AppID / certificate (vault-owned secrets)
        ▼
CyberArk PVWA / API
        ├── List users / safes / memberships     → aggregation
        ├── Add / remove safe member             → provisioning
        └── (PAM native) checkout, PSM, rotate   → evidence via PAM reports
```

| Operation | Where it runs | IIQ artifact |
| --- | --- | --- |
| Request privileged access | IIQ LCM / roles | IdentityRequest |
| Approve | IIQ workflows | Approval history |
| Grant safe membership | CyberArk via connector | Provisioning plan / Task Result |
| Checkout + session | CyberArk | PAM checkout / recording reports |
| Rotate password | CyberArk platform policy | Rotation logs / reconcile reports |
| Inventory | Account Aggregation | Cube entitlements + Task Result |

**Lab-without-live-target:** Classic track can still complete offline (Application shell, safe catalog stub, policy forms, RACI, connection worksheet). Prefer the **enterprise stack** when available: HashiCorp Vault + CyberArk-shaped pam-lab give real checkout/deny proofs (Lesson 255) without a licensed CyberArk tenant.

---

## Real-world setup (outside IIQ)

This is what a production engineer coordinates with the PAM team before the connector works:

### Step 1 — Vault integration identity

1. PAM team creates an application identity (AppID / certificate auth — prefer cert over static password).
2. Scope that identity to the safes IIQ is allowed to manage — least privilege, not “all safes.”
3. Vault the credential material in the bank’s secret store; never commit to git or leave in Application XML exports.

### Step 2 — Network and TLS

1. IIQ (or its connector gateway — Lesson 88) reaches PVWA / API over TLS only.
2. Allowlist source IPs; no inbound from internet to the vault.
3. Document the URL (e.g. internal `https://pam.meridiannb.local`) and cert trust chain owner.

### Step 3 — Safe and platform readiness

1. Create/confirm safes: `MNB-Safe-CloudAdmin`, `MNB-Safe-BreakGlass-AD`, `MNB-Safe-Payments-Switch`.
2. Attach platforms with rotation and (where required) exclusive checkout + PSM recording.
3. Confirm break-glass accounts exist *inside* the BreakGlass safe — not as static passwords in a runbook wiki.

### Step 4 — Governance records

Document: RACI, SLAs, which IIQ roles map to which safes, certification cadence (monthly privileged), and the examiner evidence map (Task 6).

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`; Debug access available
- [ ] Matrix row for Privileged vault reviewed; glossary skimmed
- [ ] Privileged role names known from Lesson 28; BreakGlass pattern from Lesson 37
- [ ] Personas: `kai.nguyen` (engineer), `amelia.brooks` (security), `jordan.reed` (ops/cloud)
- [ ] Binder: `~/iiq-lab-data/connectors/pam/`
- [ ] No CyberArk secrets on disk in cleartext; lab uses placeholders only

---

## Lab procedure

### Task 1 — RACI and SLAs for privileged access

Privileged failures are ownership failures first. Write who does what before you name an Application.

1. Create this RACI (adjust only with justification):

| Activity | IAM | PAM | Security | Manager |
| --- | --- | --- | --- | --- |
| Approve standing privileged role | C | C | A | C |
| Add user to CyberArk safe | C | A/R | C | I |
| Rotate break-glass password | I | A/R | C | I |
| Review session recording on demand | I | A/R | C | I |
| Monthly privileged certification | A/R | C | C | C |

2. Define SLAs: break-glass vault add within **1 hour** after approvals; standing privileged within **2 business days**; leaver vault remove within rapid-offboarding window (align Lesson 34 — privileged vault remove with sensitive access revoke).

**Expected result:** RACI + SLA page in `~/iiq-lab-data/connectors/pam/`.

**If it fails:** Minimum viable ownership: PAM owns vault operations; IAM owns IIQ request evidence; Security is Accountable for policy.

### Task 2 — Create `MNB-PAM-CyberArk` shell

1. Applications → Add New → **CyberArk** / **PAM** connector template if your build’s registry shows one — or equivalent menu path.
2. Name: `MNB-PAM-CyberArk`. Owner: Security (`amelia.brooks` if the identity exists) with PAM technical owner noted in Description.
3. Not authoritative. Create identities: **OFF**. Description: “Privileged vault governance — lab shell; secrets in vault only.”
4. Save. If the connector type is missing (module not installed), create a named Application placeholder and document intended type in Description — continue offline tasks.

**Expected result:** Named Application exists; no secrets stored in the object for lab.

**If it fails:** Placeholder Application with exact name `MNB-PAM-CyberArk` is acceptable for lab-without-live-target.

### Task 3 — Safe / account catalog stub (offline)

Build the entitlement dictionary the connector would populate.

1. Create `~/iiq-lab-data/connectors/pam/pam-safes-stub.csv`:

```csv
safeName,platformHint,privileged,requestable,standingOrTemp,linkedRole
MNB-Safe-CloudAdmin,AWS-or-Cloud,true,true,standing,MNB-Role-CloudAdmin
MNB-Safe-BreakGlass-AD,Windows-Domain,true,true,temporary-8h,BreakGlass
MNB-Safe-Payments-Switch,Network-or-App,true,true,standing,(payments-privileged)
```

2. In binder notes: entitlements = **safe membership** and/or privileged account links (version-dependent) — capture both concepts even if your build only surfaces one.
3. Mark all as **privileged / non-birthright**.
4. Correlation key: vault user ↔ IdentityIQ `userName` / email `@meridiannb.com` (e.g. `kai.nguyen@meridiannb.com`).

**Expected result:** Safe catalog stub on disk with privilege flags, role linkage, and correlation key.

### Task 4 — Provisioning policy stubs and role-to-safe map

1. Document policy stubs (forms / plan operations — names vary): Add user to safe; Remove from safe; Disable vault user (if applicable).
2. Link design table:

| IIQ role / pattern | PAM entitlement / safe | Notes |
| --- | --- | --- |
| `MNB-Role-CloudAdmin` (Lesson 28) | `MNB-Safe-CloudAdmin` | Standing; monthly cert; never birthright |
| BreakGlass (Lesson 37) | `MNB-Safe-BreakGlass-AD` | Max **8 hours**; auto-remove on expiry; Security + Tech approval |
| Payments privileged | `MNB-Safe-Payments-Switch` | Coordinate with Wire dual-control SoD (Lesson 85) |

3. Write the anti-pattern: IIQ role assigned with no safe membership provisioning plan — or safe membership granted in CyberArk UI with no IdentityRequest.

**Expected result:** Policy stubs + role-to-safe mapping table in the binder.

### Task 5 — Lab-without-live-target connection worksheet

Complete without live API calls:

| Item | Lab value |
| --- | --- |
| PVWA / API URL | `https://pam-lab.meridiannb.local` (example — not live) |
| Auth | AppID / certificate — vault owned |
| TLS | Required; trust store owner: Platform |
| Aggregate | Nightly Account Aggregation task name stub: `MNB-PAM-CyberArk-Account-Aggregation` |
| Test plan | aggregate → correlate → add safe → remove safe → re-aggregate |
| Secrets | Placeholder only — “credential in bank secret store” |

Checkbox if needed: “blocked pending PAM lab — worksheets complete.”

**Expected result:** Worksheet signed; **no secrets** in git or binder screenshots.

### Task 6 — Examiner evidence pack (rotation + checkout)

Write concrete answers — this is the advanced bar for the lesson:

1. **How do you prove checkout of break-glass was approved?**  
   IdentityRequest + approval history in IIQ **and** CyberArk checkout / PSM report showing who checked out which account and when. Neither alone is enough.

2. **How do you prove password rotation?**  
   CyberArk platform rotation / reconcile report for the account (e.g. post-checkout rotate or scheduled rotate) **plus** IIQ aggregation showing continued safe membership only for still-authorized users — rotation is PAM evidence; membership is IAM evidence.

3. **What IIQ artifact shows safe membership?**  
   Account Aggregation Task Result for `MNB-PAM-CyberArk` and the identity cube entitlement/safe listing for `kai.nguyen` / `jordan.reed`.

4. **What happens on leaver for vault users?**  
   Rapid offboarding (Lesson 34): remove safe memberships → disable/delete vault user per runbook → confirm next aggregation shows absence → retain PAM session/checkout history for the investigation window.

**Expected result:** Evidence pack page with pointers to IdentityRequest, aggregation, and PAM reports.

### Task 7 — Residual risk

Record `RR-PAM-01`: *Checkout, session recording, and rotation occur in CyberArk; IIQ aggregation proves membership, not that a session was recorded.* Compensating control: monthly sample of BreakGlass IdentityRequests joined to PAM checkout reports, owned by Security (`amelia.brooks`) with PAM executing the pull.

**Expected result:** Residual risk logged with compensating control and owner.

---

## Acceptance criteria

- [ ] RACI + SLAs complete
- [ ] `MNB-PAM-CyberArk` shell (or exact-name placeholder) exists
- [ ] Three safes catalogued as privileged in `pam-safes-stub.csv`
- [ ] Role-to-safe mapping aligns CloudAdmin and BreakGlass (Lessons 28 / 37)
- [ ] Connection worksheet complete with no secrets in git
- [ ] Examiner pack covers approval, checkout, rotation, leaver, and `RR-PAM-01`

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Connector type missing | PAM module / license not installed | Shell + escalate pack; complete offline worksheets |
| API 401 / cert errors | AppID/cert expired or wrong safe rights | PAM rotates credential; update encrypted config only |
| Birthright privileged safe | Assignment rule mistake | Remove birthright; request-only |
| IIQ role without vault access | Provisioning plan never linked | Map role → safe entitlement; test add/remove |
| Dual-system drift | No aggregation | Schedule Account Aggregation; certify monthly |
| Secrets in exported XML | Bad export hygiene | Scrub; re-encrypt; treat as incident |

---

## Training binder evidence

- RACI / SLA page
- Application screenshot (or placeholder note)
- `pam-safes-stub.csv` + privilege flags
- Role-to-safe map (CloudAdmin / BreakGlass / payments)
- Connection worksheet (no secrets)
- Examiner evidence answers (checkout + rotation) and `RR-PAM-01`

---

## Knowledge check

1. What is the matrix-preferred connector family for a privileged vault at Meridian?
2. Name the Meridian PAM application object.
3. Are PAM safes birthright? Why?
4. Who is Accountable/Responsible for adding users to CyberArk safes in the lab RACI?
5. What two artifacts together prove an approved break-glass **checkout**?
6. What does `RR-PAM-01` say IIQ aggregation cannot prove by itself?

### Answers

1. CyberArk / PAM module.
2. `MNB-PAM-CyberArk`.
3. No — privileged / request-only; birthright would put Domain Admin–class access on every joiner path.
4. PAM team (A/R) with IAM and Security consulted; Security Accountable for standing privileged policy.
5. IIQ IdentityRequest/approval history **and** CyberArk checkout (or PSM) report.
6. That a session was recorded or that a password actually rotated — those are PAM-platform evidence.

---

## Further reading

- [CyberArk technical documentation](https://docs.cyberark.com/) — start at the docs landing page; search PVWA, safes, platforms, CPM rotation, and PSM session management for the object model in this lesson.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “CyberArk” or “PAM connector” for your version’s application guide and aggregation attributes.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — integration troubleshooting threads (auth, safe rights, aggregation gaps).
- [NIST SP 800-63B — Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html) — authenticator lifecycle and session considerations that parallel privileged credential handling.
- [FFIEC Information Security booklet](https://www.ffiec.gov/) — search the IT Handbook for privileged access and logging expectations examiners reuse in vault reviews.

---

## Stretch lab

Draft IdentityRequest acceptance criteria for closing a privileged ticket: (1) approval screenshots, (2) CyberArk safe membership proof (aggregation or PAM admin export), (3) for BreakGlass — checkout report sample and confirmation of remove-on-expiry. Optionally sketch a monthly join query narrative: BreakGlass requests in IIQ vs checkout events in CyberArk for the same window.

---

## Summary

- PAM/CyberArk is Meridian’s privileged credential control plane; `MNB-PAM-CyberArk` is how IIQ inventories and requests safe membership.
- CloudAdmin and BreakGlass roles only become real when mapped to safes with approval evidence, rotation, and checkout audit.
- Classic track can finish offline with worksheets; enterprise Lab v3 adds live Vault + pam-lab checkout (Lesson 255).

---

**Previous:** [Lesson 85 — Logical Applications](85-logical-applications.md)  
**Next:** [Lesson 87 — Duo MFA Integration Patterns](87-duo-mfa-integration-patterns.md)
