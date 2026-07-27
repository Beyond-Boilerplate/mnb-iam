# Lesson 61 — Password Management & Interceptor

**Level:** Intermediate  
**Track:** Connectors — Directory  
**Time:** 75–90 min  
**Prereq:** Lessons 55–56 (AD Direct / PASSWORD features); Lesson 53 IQService TLS design; Lesson 60 LDIF limits  

**Lab data:**
- Repo: `lab-data/connectors/ad/iqservice-checklist.md` (copy to `~/iiq-lab-data/connectors/ad/`)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Runtime notes: `~/iiq-lab-data/connectors/ad/MNB-password-policy-61.md` (you create)

---

## Learning objectives

You will be able to:

- Separate **IIQ password policy objects** from **target AD/Entra domain password rules** and keep IIQ ≥ target strength
- Inventory which Meridian applications accept `PASSWORD` operations from the feature matrix
- Design Password Interceptor scope (Yes/No) using the IQService checklist — and defend the decision
- Write helpdesk and joiner initial-password procedures that never put cleartext in tickets or logs
- Complete lab-without-live-AD test cases (PW-AD-01 … PW-LOG-01) with Expected result / If it fails
- Explain why LDIF and HR apps must never accept password set

---

## Why this matters

**Business.** When `nina.joiner` starts on Monday, someone must deliver an initial AD password. When `amelia.brooks` locks herself out before a wire window, helpdesk must reset without creating a fraud channel. Guessing which apps IIQ may set passwords on — or assuming Password Interceptor “just syncs everything” — produces account lockout storms, dual-path resets, and passwords sitting in ServiceNow tickets.

**Control / audit.** Password flows need named control owners, TLS evidence to IQService, and an explicit answer to the checklist line: *Password interception in scope?* Examiners ask: *“Show that helpdesk password resets never write the password to tickets or cleartext logs.”* “We use IdentityIQ” is not an answer; redacted Task Results and a written delivery channel are.

---

## Concepts

### Three layers people confuse

| Layer | What it is | Meridian example |
| --- | --- | --- |
| **IIQ password policy** | Complexity / history / length enforced in IIQ UX and LCM | Lab policy object used by helpdesk reset forms |
| **Target domain policy** | AD Fine-Grained / domain policy or Entra password protection | Still enforced when the password reaches AD |
| **Connector PASSWORD feature** | Whether that application type can emit a password operation | `MNB-ActiveDirectory` = Y via IQService |

IIQ policy does **not** replace AD policy. If IIQ accepts 8-character passwords and AD requires 14 with complexity, resets “succeed” in IIQ and fail (or worse, behave inconsistently) on the target. Rule: **IIQ policy strength ≥ AD/Entra strength** for any app IIQ sets passwords on.

### PASSWORD vs CURRENT_PASSWORD vs UNLOCK

- **PASSWORD** — set or reset the password (helpdesk / joiner path).
- **CURRENT_PASSWORD** — change requires the existing password (self-service change).
- **UNLOCK** — clear lockout; **not** a password reset. Mixing these in runbooks causes helpdesk to “reset” when they only needed unlock — and vice versa.

### Password Interceptor (AD)

**Password Interceptor** is an AD-side component (paired with IQService patterns) that can capture *native* password changes made directly in Active Directory and optionally sync them toward IIQ-managed targets. It is **not** automatic with AD Direct. Meridian must decide:

- **In scope:** document install host, which apps receive sync, failure mode if interceptor is down, and monitoring.
- **Out of scope (curriculum default for lab v1):** native AD changes are **not** captured into IIQ; helpdesk uses the IIQ LCM reset path only.

Leaving the checklist as “TBD” is itself a finding — dual undocumented paths are how passwords diverge across apps.

```
  User / helpdesk / LCM
        │
        ▼
  IIQ password policy check
        │
        ▼
  Provisioning plan (PASSWORD)
        │
        ▼
  IQService (TLS) → Active Directory
        │
        ├── optional: Password Interceptor captures native AD changes
        │         └── sync to other PASSWORD=Y targets (if in scope)
        └── Entra Graph password ops (separate rights — Lesson 59)
```

### What must never accept PASSWORD

| App | PASSWORD? | Why |
| --- | --- | --- |
| `MNB-ActiveDirectory` | Y (design) | Primary on-prem target via IQService |
| `MNB-EntraID` | Maybe | Graph rights / cloud-only contractors |
| `MNB-OpenLDAP` | Design | Only if bind ACLs allow password modify |
| `MNB-HR` / `MNB-LDIF-DirectoryDump` / `MNB-IT-Access` | **N** | Authoritative file / offline evidence / non-password targets |

Never store passwords in binders, git, CHANGELOG, or screenshots. Lab notes say “temporary password delivered via approved channel” — never the value.

---

## How it works

IdentityIQ evaluates password policy, builds a provisioning plan with a password AttributeRequest, and the AD Direct connector ships the operation through **IQService** to the domain controller. Interceptor, if installed, sits on the AD change path and can push captured hashes/changes back into IIQ workflows — exact packaging is version-specific; your job is scope and evidence, not inventing UI labels.

| Path | Trigger | Evidence |
| --- | --- | --- |
| LCM / helpdesk reset | IIQ plan → IQService → AD | Provisioning Transaction / Task Result (redacted) |
| Self-service change | CURRENT_PASSWORD flow | Same + user acknowledgment |
| Native AD change | ADUC / Ctrl-Alt-Del | Captured **only if** Interceptor in scope |
| Joiner create | Create + initial password + force-change flag | Create plan + secure delivery record |

---

## Real-world setup (outside IIQ)

### Step 1 — IQService and TLS

1. Confirm Lesson 53 worksheet: IQService host, TLS certs, service account rights for password set — **not** Domain Admin if avoidable.
2. Without TLS, password operations over the wire are a finding even if “lab only.”

### Step 2 — Answer the interceptor checklist

1. Open `~/iiq-lab-data/connectors/ad/iqservice-checklist.md`.
2. Resolve: *Password interception in scope? (Password Interceptor)* → **Yes** or **No** with rationale.
3. Curriculum default: **No (design only)** unless your homelab actually installs Interceptor.

### Step 3 — Align domain and IIQ policies

1. Pull AD domain (or FGPP) min length, complexity, history, lockout threshold from the AD team.
2. Configure IIQ password policy to meet or exceed those values.
3. Name the control owner for password policy drift (usually IAM + AD engineering).

### Step 4 — Secure delivery channel

1. Approve one channel for joiner initial passwords (e.g., sealed envelope to manager, approved vault one-time secret, or IdP invite) — **not** email to distribution lists.
2. Ticket templates must forbid pasting passwords into work notes.

---

## Before you start

- [ ] Feature matrix / `features-string-glossary.md` PASSWORD column reviewed
- [ ] IQService TLS worksheet from Lesson 53 available
- [ ] Checklist interceptor question unanswered or TBD → resolve this lesson
- [ ] Never use real production passwords in lab notes
- [ ] IIQ up at `http://localhost:8080/identityiq`

---

## Lab procedure

### Task 1 — Inventory PASSWORD-capable Meridian apps

Helpdesk must know which apps appear on a reset form. Build that list from features, not memory.

1. Open the provisioning feature matrix from Lesson 55 (`MNB-provisioning-feature-matrix-55.csv` or selection matrix + glossary).
2. List apps with PASSWORD=Y or Unknown.
3. Record training expectations:

| App | PASSWORD | Notes |
| --- | --- | --- |
| `MNB-ActiveDirectory` | Y | Via IQService |
| `MNB-EntraID` | Maybe | Graph rights |
| `MNB-OpenLDAP` | Design | If bind allows |
| `MNB-HR` / LDIF / IT-Access | N | Not password targets |

**Expected result:** Short inventory in `MNB-password-policy-61.md`.

### Task 2 — IIQ vs AD policy alignment

Misalignment is the #1 cause of “IIQ said success, AD said no.”

1. Create `~/iiq-lab-data/connectors/ad/MNB-password-policy-61.md` with:

| Rule | IIQ policy intent | AD domain intent |
| --- | --- | --- |
| Min length | Document lab value | Must be ≥ AD |
| Complexity | On | On |
| History | Document | Document |
| Lockout | Helpdesk process | AD lockout threshold |

2. Add the statement: *IIQ policy must not be weaker than AD for any app IIQ sets AD passwords on.*

**Expected result:** Alignment file with “IIQ ≥ AD strength” statement.

### Task 3 — Interceptor scope decision (lab-without-live-target)

This is a design decision even when you never install the binary.

1. Answer checklist: Password Interceptor in scope for Meridian lab v1? Curriculum default: **No** (design only), unless your homelab installs it.
2. If **Yes** (future): document install host, sync targets (which apps receive password), and failure mode if interceptor is down (queue? alert? freeze sync?).
3. If **No**: write *“Native AD password changes are not captured into IIQ in v1; helpdesk uses IIQ LCM reset path only.”*
4. If interceptor is wanted but IQService TLS is missing: stop and fix Lesson 53 first.

**Expected result:** Interceptor Yes/No with rationale in the password policy file.

### Task 4 — Test cases (design-only OK)

Write failures before you cause them in production.

| Test ID | Scenario | Expected result | If it fails |
| --- | --- | --- | --- |
| PW-AD-01 | LCM reset for lab user on `MNB-ActiveDirectory` | Plan PASSWORD success | IQService/TLS/rights |
| PW-POL-01 | Too-weak password in IIQ | Rejected by IIQ policy | Tighten policy |
| PW-SCOPE-01 | Reset attempted on `MNB-IT-Access` or LDIF | Not offered / fails closed | Remove from password app list |
| PW-LOG-01 | Review task/provisioning logs after reset | No cleartext password | Fix logging redaction; incident if found |

**Expected result:** Four tests documented; live execution optional without AD.

### Task 5 — Helpdesk operating procedure stub

1. Draft one page: authenticate helpdesk → verify caller (out-of-band) → LCM password reset → select only PASSWORD=Y apps → confirm user login → never paste password into ticket.
2. Personas for rehearsal: `nina.joiner` (joiner initial), `amelia.brooks` (helpdesk-style reset demo).
3. Forbid shared “break-glass” passwords in tickets.

**Expected result:** Proc stub in binder / policy file.

### Task 6 — Joiner initial-password path

1. For `nina.joiner`, document: temporary password set on AD create → force change at first logon (AD flag) → delivery via approved secure channel only.
2. Explicit ban: never email cleartext to shared lists or put the value in CHANGELOG.

**Expected result:** Joiner password path in policy file.

**If it fails (password emailed in cleartext):** Stop; treat as a security incident pattern and redesign delivery.

### Task 7 — UNLOCK vs PASSWORD drill

1. Write two sentences distinguishing unlock (clear lockout) from reset (new password).
2. Add helpdesk decision: lockout with known password → try UNLOCK first; forgotten password → PASSWORD reset.

**Expected result:** Distinction recorded next to the test matrix.

### Task 8 — CHANGELOG

1. Record interceptor scope decision and path to `MNB-password-policy-61.md`.
2. Confirm no secrets were pasted into the CHANGELOG.

**Expected result:** CHANGELOG updated; secrets absent.

---

## Acceptance criteria

- [ ] PASSWORD-capable app inventory listed
- [ ] IIQ vs AD policy alignment file created (IIQ ≥ AD)
- [ ] Interceptor Yes/No decided with rationale on the checklist
- [ ] ≥4 test cases with Expected result / If it fails
- [ ] Helpdesk proc stub + joiner initial-password path written
- [ ] UNLOCK vs PASSWORD distinction recorded
- [ ] No secrets in repo/notes

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Password op fails | IQService / TLS / rights | Lesson 53 checks |
| Accepted by IIQ, rejected by AD | IIQ weaker than AD | Align policies (IIQ ≥ AD) |
| Password in logs or tickets | Misconfigured logging / bad proc | Redact; incident process; fix templates |
| Interceptor duplicates resets | Dual paths both active | Narrow sync targets or disable one path |
| Unlock confused with reset | Feature mix-up | UNLOCK ≠ PASSWORD in runbooks |
| Reset offered on LDIF/HR | Scope inventory wrong | Remove from PASSWORD app list |

---

## Training binder evidence

- `MNB-password-policy-61.md` with interceptor decision and alignment table
- Feature matrix PASSWORD column screenshot/export
- Helpdesk proc stub + joiner delivery channel note
- PW-LOG-01 evidence approach (how you would prove no cleartext)

**Examiner question:** *“Show that helpdesk password resets never write the password to tickets or cleartext logs.”*

---

## Knowledge check

1. Does IIQ password policy replace AD domain policy?
2. Which Meridian app is the primary PASSWORD target on-prem?
3. What checklist item covers native AD password capture?
4. Should `MNB-LDIF-DirectoryDump` accept password set?
5. Name one failure mode if IIQ policy is weaker than AD.
6. Why document a secure delivery channel for joiner initial passwords?

### Answers

1. No — it must align; AD still enforces domain rules on the target.
2. `MNB-ActiveDirectory` (via IQService).
3. Password Interceptor in scope (Yes/No).
4. No — offline evidence, no live password target.
5. IIQ accepts a password AD rejects — inconsistent UX, failed plans, or lockout churn.
6. Cleartext email/tickets create audit and fraud risk; use approved secure channels only.

---

## Further reading

- [Microsoft — Password must meet complexity requirements](https://learn.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/password-must-meet-complexity-requirements) — what AD actually enforces when IIQ sends a password.
- [Microsoft — Fine-Grained Password Policies](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/adac/introduction-to-active-directory-administrative-center-enhancements--level-100-#fine_grained_pswd_policy_intro) — how banks apply different strengths to privileged vs standard users.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “password management” and “Password Interceptor” for your IIQ version.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real IQService password and interceptor troubleshooting threads.
- [NIST SP 800-63B — Digital Identity Guidelines (Authentication)](https://pages.nist.gov/800-63-3/sp800-63b.html) — modern password length/complexity guidance and why memorized secrets need careful handling.

---

## Stretch lab

Map CURRENT_PASSWORD flows for self-service change vs helpdesk set. Design an Entra-only password path for cloud contractors without AD. Add a SIEM alert idea for mass password resets (Lesson 104) — threshold, window, and who gets paged.

---

## Summary

- Password capability is feature- and IQService-bound, not universal across Meridian apps.
- Interceptor scope is an explicit Yes/No decision; lab v1 defaults to out of scope with LCM-only resets.
- Helpdesk and joiner paths succeed only when policies align, TLS is proven, and cleartext never hits tickets or logs.

---

**Previous:** [Lesson 60 — LDIF Connector](60-ldif-connector.md)  
**Next:** [Lesson 62 — Directory Authoritative vs Target](62-directory-authoritative-vs-target.md)
