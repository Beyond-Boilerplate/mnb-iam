# Lesson 61 — Password Management & Interceptor

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Directory |
| **Time** | 60–90 minutes |
| **Prereq** | Lessons 55–56; AD PASSWORD=Y + IQService design |
| **Lab data** | `~/iiq-lab-data/connectors/ad/iqservice-checklist.md`; feature glossary |

## Learning objectives

You will be able to:

- Separate IIQ password policy objects from target AD/Entra password rules
- Design Meridian password sync / interceptor scope using the AD checklist
- Document which apps accept PASSWORD operations from the feature matrix
- Complete lab-without-live-target interceptor worksheets and test cases
- Avoid storing passwords in logs, binders, or git

## Why this matters

Helpdesk resets and joiner initial passwords are high-risk banking operations. Meridian must know whether Password Interceptor captures native AD changes into IIQ, and which apps IIQ may set passwords on. Guessing creates account lockout storms and audit gaps.

**Control / audit:** Password flows need control owners, encryption/TLS evidence, and explicit “interceptor in scope?” answers on the IQService checklist.

## Concepts

| Concept | Meaning |
| --- | --- |
| Password policy (IIQ) | Complexity / history rules enforced in IIQ UX |
| Target policy | AD/Entra domain password policy still applies |
| PASSWORD feature | Connector can set/change password |
| CURRENT_PASSWORD | Change requires existing password |
| Password Interceptor | Captures password changes on AD for sync/governance patterns |

```text
  User / helpdesk / LCM
        |
        v
  IIQ password policy check
        |
        v
  Provisioning plan (PASSWORD)
        |
        v
  IQService → AD  (and/or Entra Graph)
        |
        v
  Optional Password Interceptor → IIQ (native AD change path)
```

Checklist line: “Password interception in scope? (Password Interceptor)” → answer Yes/No for Meridian v1.

## Before you start

- [ ] Feature matrix PASSWORD column reviewed
- [ ] IQService TLS worksheet from Lesson 53
- [ ] Checklist interceptor question unanswered or TBD → resolve this lesson
- [ ] Never use real production passwords in lab notes

## Lab procedure

### Task 1 — Inventory PASSWORD-capable Meridian apps

1. Open `MNB-provisioning-feature-matrix-55.csv`.
2. List apps with PASSWORD=Y or Unknown.
3. Default training expectations:

| App | PASSWORD | Notes |
| --- | --- | --- |
| `MNB-ActiveDirectory` | Y | Via IQService |
| `MNB-EntraID` | Maybe | Graph rights |
| `MNB-OpenLDAP` | Design | If bind allows |
| `MNB-HR` / LDIF / IT-Access | N | Not targets |

**Expected result:** Short inventory list in notebook.

### Task 2 — IIQ vs AD policy alignment worksheet

1. Create `~/iiq-lab-data/connectors/ad/MNB-password-policy-61.md`:

| Rule | IIQ policy intent | AD domain intent |
| --- | --- | --- |
| Min length | Document lab value | Must be ≥ AD |
| Complexity | On | On |
| History | Document | Document |
| Lockout | Helpdesk process | AD lockout threshold |

2. Rule: IIQ policy must not be weaker than AD if IIQ sets AD passwords.

**Expected result:** Alignment file with “IIQ ≥ AD strength” statement.

### Task 3 — Lab without live target — interceptor design

1. Answer checklist: Password Interceptor in scope for Meridian lab v1? Curriculum default: **No** (design only), unless your homelab installs it.
2. If Yes (future): document install host, sync targets (which apps receive password), and failure mode if interceptor down.
3. If No: write “Native AD password changes are not captured into IIQ in v1; helpdesk uses IIQ LCM reset path only.”
4. Expected result: written scope decision. If it fails (interceptor wanted but IQService TLS missing): fix Lesson 53 first.

**Expected result:** Interceptor Yes/No with rationale in password policy file.

### Task 4 — Test cases (design-only OK)

| Test ID | Scenario | Expected result | If it fails |
| --- | --- | --- | --- |
| PW-AD-01 | LCM reset for lab user on `MNB-ActiveDirectory` | Plan PASSWORD success | IQService/TLS/rights |
| PW-POL-01 | Too-weak password in IIQ | Rejected by IIQ policy | Tighten policy |
| PW-SCOPE-01 | Reset attempted on `MNB-IT-Access` | Not offered / fails closed | Remove from password app list |
| PW-LOG-01 | Review task logs after reset | No cleartext password | Fix logging redaction |

**Expected result:** Four tests documented; live execution optional.

### Task 5 — Helpdesk operating procedure stub

1. Draft: authenticate helpdesk → verify caller → LCM password reset → select only PASSWORD=Y apps → confirm user login.
2. Personas for rehearsal: `nina.joiner` (joiner initial), `amelia.brooks` (helpdesk-style reset demo).
3. Forbid shared “break-glass” passwords in tickets.

**Expected result:** One-page proc stub in binder.

### Task 6 — Initial password / joiner path

1. For `nina.joiner`, document: temporary password set on AD create → force change at first logon (AD flag) → never email cleartext to shared lists.
2. Expected result: joiner password path written. If it fails (password emailed in cleartext): stop; use secure delivery channel only.

**Expected result:** Joiner password path in policy file.

### Task 7 — CHANGELOG

1. Record interceptor scope decision and policy alignment file path.

**Expected result:** CHANGELOG updated.

## Acceptance criteria

- [ ] PASSWORD-capable app inventory listed
- [ ] IIQ vs AD policy alignment file created
- [ ] Lab-without-live-target interceptor Yes/No decided
- [ ] ≥4 test cases with Expected result / If it fails
- [ ] Helpdesk proc stub written
- [ ] Joiner initial-password path documented
- [ ] No secrets in repo/notes

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Password op fails | IQService/TLS | Lesson 53 checks |
| Accepted by IIQ, rejected by AD | IIQ weaker than AD | Align policies |
| Password in logs | Misconfigured logging | Redact; incident process |
| Interceptor duplicates resets | Dual paths | Narrow sync targets |
| Unlock confused with reset | Feature mix-up | UNLOCK ≠ PASSWORD |

## Training binder evidence

- `MNB-password-policy-61.md` with interceptor decision
- Feature matrix PASSWORD column screenshot/export
- Helpdesk proc stub
- PW-LOG-01 evidence approach note

**Examiner question:** “Show that helpdesk password resets never write the password to tickets or cleartext logs.”

## Knowledge check

1. Does IIQ password policy replace AD domain policy?
2. Which Meridian app is the primary PASSWORD target on-prem?
3. What checklist item covers native AD password capture?
4. Should `MNB-LDIF-DirectoryDump` accept password set?
5. Name one failure mode if IIQ policy is weaker than AD.
6. Why document a secure delivery channel for joiner initial passwords?

### Answers

1. No—it must align; AD still enforces domain rules on the target.
2. `MNB-ActiveDirectory` (via IQService).
3. Password Interceptor in scope (Yes/No).
4. No.
5. IIQ accepts a password AD rejects—or worse, inconsistent UX and lockouts.
6. Cleartext email/tickets create audit and fraud risk; use approved secure channels only.

## Stretch lab

- Map CURRENT_PASSWORD flows for self-service change vs helpdesk set.
- Design Entra-only password path for cloud contractors without AD.
- Add SIEM alert idea for mass password resets (Lesson 104).

## Summary

- Password capability is feature- and IQService-bound, not universal.
- Interceptor scope is an explicit Meridian decision.
- Lab-without-live-target worksheets + test cases keep training safe.
- Joiner initial passwords need secure delivery; never cleartext tickets.

---

**Previous:** [Lesson 60 — LDIF Connector](60-ldif-connector.md)  
**Next:** [Lesson 62 — Directory Authoritative vs Target](62-directory-authoritative-vs-target.md)
