# Lesson 86 — PAM / CyberArk Module

**Level:** Advanced  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 75–90 min  
**Prereq:** Lesson 85 — Logical Applications; Lesson 28 — Privileged Access Roles recommended  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Privileged vault)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Position **CyberArk / PAM module** connectors as privileged account governance, not birthright IAM
- Create Application shell `MNB-PAM-CyberArk` with safe/account entitlement model (offline)
- Align IIQ privileged roles (`CloudAdmin`, BreakGlass) with vault dual-control
- Document joiner/leaver and certification flows that include vault evidence
- Complete lab-without-live-target connection and RACI worksheets

---

## Why this matters

**Business.** Shared root, Domain Admin, and payment switch passwords must live in a vault with session recording—not in tickets or spreadsheets.

**Control / audit.** Examiners ask whether privileged passwords rotate, who can check out break-glass credentials, and how IAM requests relate to vault membership. IIQ without PAM leaves the highest-risk accounts half-governed.

---

## Concepts

Matrix: Privileged vault → **CyberArk** / PAM module.

```
IIQ request / role (privileged)
        │
        ▼
 Approval (Tech Director + Security)
        │
        ▼
 Provision vault safe membership / account link  ──► CyberArk
        │
        ▼
 Checkout / session / rotate (PAM platform)
```

| Layer | Owner | Meridian object |
| --- | --- | --- |
| Governance | IAM | `MNB-PAM-CyberArk`, privileged roles |
| Vault | PAM team | Safes, platforms, accounts |
| Platform | Ops | Jump hosts, connectors |

**Lab-without-live-target:** Application shell, safe catalog stub, provisioning policy forms, RACI, and network worksheet. No live CyberArk API calls required.

---

## Before you start

- [ ] IIQ up; Debug access
- [ ] Matrix row for Privileged vault reviewed
- [ ] Privileged role names known (Lesson 28): CloudAdmin / BreakGlass patterns
- [ ] Personas: `kai.nguyen` (engineer), `amelia.brooks` (security), `jordan.reed` (ops)
- [ ] Binder: `connectors/pam/`

---

## Lab procedure

### Task 1 — RACI for privileged access

1. Create RACI table:

| Activity | IAM | PAM | Security | Manager |
| --- | --- | --- | --- | --- |
| Approve standing privileged role | C | C | A | C |
| Add user to CyberArk safe | C | A/R | C | I |
| Rotate break-glass password | I | A/R | C | I |
| Monthly privileged cert | A/R | C | C | C |

2. Define SLA: break-glass vault add within 1 hour after approvals; standing privileged within 2 business days.

**Expected result:** RACI + SLA page in binder.

**If it fails:** Minimum: PAM team owns vault; IAM owns IIQ request evidence.

---

### Task 2 — Create `MNB-PAM-CyberArk` shell

1. Applications → Add New → CyberArk / PAM connector template if available.
2. Name: `MNB-PAM-CyberArk`.
3. Owner: Security (`amelia.brooks` if identity exists) + PAM technical owner note.
4. Not authoritative.
5. Description: “Lab shell — privileged vault governance.”
6. Save.

**Expected result:** Named Application exists.

**If it fails:** Placeholder Application with connector type documented in Description.

---

### Task 3 — Safe / account catalog (offline)

1. Document Meridian safes:
   - `MNB-Safe-CloudAdmin`
   - `MNB-Safe-BreakGlass-AD`
   - `MNB-Safe-Payments-Switch`
2. Entitlements = safe membership and/or privileged account links (version-dependent)—capture both in worksheet.
3. Mark all as **privileged / non-birthright**.
4. Correlation: vault user ↔ `userName` / email `@meridiannb.com`.

**Expected result:** Safe catalog with privilege flags and correlation key.

**If it fails:** CSV stub `~/iiq-lab-data/connectors/pam-safes-stub.csv`.

---

### Task 4 — Provisioning policies and IIQ role linkage

1. Policy stubs: Add user to safe, Remove from safe, Disable vault user (if applicable).
2. Link design: IIQ role `MNB-Role-CloudAdmin` → entitlement on `MNB-PAM-CyberArk` for `MNB-Safe-CloudAdmin` (document; implement later if connector live).
3. Break-glass: time-bound assignment note (8 hours) + mandatory remove on expiry.
4. Never put vault API keys in git—use encrypted IIQ config / K8s secrets.

**Expected result:** Policy stubs + role-to-safe mapping table.

---

### Task 5 — Lab-without-live-target connection worksheet

| Item | Lab value |
| --- | --- |
| PVWA / API URL | `https://pam-lab.meridiannb.local` (example) |
| Auth | AppID / certificate — vault owned |
| TLS | Required |
| Aggregate | Nightly Account Aggregation |
| Test plan | aggregate → correlate → add safe → remove safe |

Complete without live calls; checkbox “blocked pending PAM lab” if needed.

**Expected result:** Worksheet signed; secrets absent.

---

### Task 6 — Evidence pack for examiners

Write answers:

1. How do you prove checkout of break-glass was approved?
2. What IIQ artifact shows safe membership?
3. What happens on leaver for vault users?

**Expected result:** Evidence pack page with pointers (IdentityRequest, aggregation, PAM reports).

---

## Acceptance criteria

- [ ] RACI + SLA complete
- [ ] `MNB-PAM-CyberArk` shell exists
- [ ] Three safes catalogued as privileged
- [ ] Role-to-safe mapping documented
- [ ] Connection worksheet complete (no secrets in git)
- [ ] Examiner evidence pack written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Connector missing | Module not installed | Shell + escalate license/pack |
| API 401 | AppID/cert | PAM team rotates; update encrypted config |
| Birthright privileged | Role mistake | Remove assignment rule; request-only |
| Dual systems drift | No aggregation | Schedule Account Aggregation; cert monthly |
| Secrets in XML | Bad export | Scrub; re-encrypt |

---

## Training binder evidence

- RACI/SLA
- Application screenshot
- Safe catalog
- Role-to-safe map
- Connection worksheet
- Examiner evidence answers

---

## Knowledge check

1. Matrix preferred connector for privileged vault?
2. Name the Meridian PAM application.
3. Are PAM safes birthright?
4. Who is Accountable for adding users to CyberArk safes in the lab RACI?
5. What is the lab-without-live-target requirement?

### Answers

1. CyberArk / PAM module.  
2. `MNB-PAM-CyberArk`.  
3. No—privileged / request-only.  
4. PAM team (A/R) with IAM/Security consulted.  
5. App shell, safe catalog, policies, RACI, and connection worksheet without live API calls.

---

## Stretch lab

Draft IdentityRequest acceptance criteria: approval screenshots + CyberArk safe membership proof attached before closing privileged ticket.

---

## Summary

- PAM/CyberArk is Meridian’s privileged credential control plane, governed via `MNB-PAM-CyberArk`.
- IIQ roles request vault access; PAM operates checkout and rotation.
- Advanced lab completes offline with RACI, catalog, and worksheets.

---

**Previous:** [Lesson 85 — Logical Applications](85-logical-applications.md)  
**Next:** [Lesson 87 — Duo MFA Integration Patterns](87-duo-mfa-integration-patterns.md)
