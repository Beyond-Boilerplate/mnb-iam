# Lesson 59 — Azure / Entra ID Connector

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors — Directory |
| **Time** | 60–90 minutes |
| **Prereq** | Lesson 58; matrix row Entra ID / Azure AD |
| **Lab data** | `~/iiq-lab-data/connectors/connector-selection-matrix.csv`; Lesson 55 feature matrix |

## Learning objectives

You will be able to:

- Position Entra ID as Meridian’s cloud directory / SaaS SSO hub vs Corporate AD
- Create Application shell `MNB-EntraID` (Azure Active Directory connector type)
- Document app registration, permissions, and correlation without a live tenant
- Choose when SCIM 2.0 is an alternate
- Write cloud aggregation and disable test cases with Expected result / If it fails

## Why this matters

Meridian hybrid identity: AD remains on-prem for many bank apps; Entra ID brokers cloud SaaS. Duplicating both as authoritative sources creates split-brain identities. Wrong connector (generic Web Services instead of Azure AD) loses group/role semantics.

**Control / audit:** Cloud apps need documented tenant IDs, least-privilege Graph permissions, and non-authoritative flags. Secrets never live in git.

## Concepts

| Topic | Meridian stance |
| --- | --- |
| Preferred connector | Azure Active Directory |
| Alternate | SCIM 2.0 |
| Authoritative | No (HR authoritative) |
| Typical account id | UPN / mailNickname / objectId (document choice) |
| Correlation | UPN↔email or employeeId extension attribute |

```text
  MNB-HR → cubes
             ^
             | correlate
  MNB-ActiveDirectory (on-prem target)
  MNB-EntraID (cloud directory target)
             |
             v
        SaaS SSO apps (later lessons)
```

## Before you start

- [ ] Selection record: Entra preferred Azure AD
- [ ] Feature matrix row for `MNB-EntraID`
- [ ] No requirement for live Azure tenant this lesson
- [ ] IIQ up for Application shell if type present

## Lab procedure

### Task 1 — Hybrid identity decision note

1. Write `~/iiq-lab-data/connectors/MNB-Entra-hybrid-59.md`:

> Corporate AD is the on-prem account target. Entra ID is the cloud directory target. Neither creates workforce identities; `MNB-HR` does. Joiner may create AD then sync/cloud create per Architecture—document actual pattern TBD.

2. List risks of dual authoritative directories.

**Expected result:** Hybrid note file with “HR only creates identities.”

### Task 2 — Lab without live target — app registration worksheet

1. Complete fictional worksheet (no real secrets):

| Item | Lab value |
| --- | --- |
| Tenant ID | `00000000-lab-tenant` |
| Application (client) ID | `11111111-lab-app` |
| Client secret | Stored in vault — **not** in file |
| Graph permissions (intent) | User.Read.All, Group.Read.All (least privilege refine) |
| Certificate auth preferred? | Yes for prod |

2. Add: “Production values from cloud team; rotate secrets.”

**Expected result:** Worksheet without real credentials.

### Task 3 — Create Application shell MNB-EntraID

1. Applications → Add New → **Azure Active Directory** (or equivalent menu path).
2. Name: `MNB-EntraID`. Owner: Cloud IAM / Technology (lab `spadmin`).
3. Enter placeholders from worksheet; skip live Test Connection.
4. Mark non-authoritative; create-identities off.
5. If type missing: write shell notes file instead.

**Expected result:** Application or notes shell exists.

**If it fails:** Document alternate build path: SCIM 2.0 app `MNB-EntraID-SCIM` as temporary alternate per matrix.

### Task 4 — Schema & correlation plan

1. Account attributes: UPN, displayName, mail, accountEnabled, objectId, department.
2. Correlation preferred: employeeId via onPremisesExtensionAttributes / custom attr if present; else UPN↔`email`.
3. Entitlements: Entra groups / app roles—document which Meridian certifies.

**Expected result:** Schema section appended to hybrid note.

### Task 5 — Test cases (design)

| Test ID | Action | Expected result | If it fails |
| --- | --- | --- | --- |
| ENTRA-AGG-01 | Aggregate | Cloud accounts linked to HR cubes | Check Graph perms / filters |
| ENTRA-EN-01 | Disable | `accountEnabled=false` on leaver | Feature ENABLE / API rights |
| ENTRA-GRP-01 | Group certify | Security groups appear as entitlements | Group read scope |

Personas: `sofia.torres`, `kai.nguyen` as cloud-heavy users (lab assumption).

**Expected result:** Three tests in notes with Expected result / If it fails.

### Task 6 — Guest / B2B boundary

1. Write: Entra guest users (`#EXT#` / external UPN patterns) must not create Meridian workforce cubes.
2. Filter or population strategy: certify guests separately or exclude from HR correlation path.
3. Expected result: guest boundary paragraph. If it fails (guests become cubes): create-identities off + correlation rules tightened.

**Expected result:** Guest/B2B note in hybrid file.

### Task 7 — Aggregation naming & CHANGELOG

1. Task name: `Aggregate MNB-EntraID` (delta when supported).
2. Order: after HR; coordinate with AD aggregate to avoid race on same identity attrs.
3. CHANGELOG entry for Lesson 59.

**Expected result:** Task named; CHANGELOG updated; live run optional.

## Acceptance criteria

- [ ] Hybrid identity note states HR authoritative
- [ ] App registration worksheet without secrets
- [ ] `MNB-EntraID` shell or notes (+ optional SCIM alternate note)
- [ ] Correlation plan documented
- [ ] ≥3 design tests with Expected result / If it fails
- [ ] Guest/B2B boundary documented
- [ ] Aggregate task named

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Auth 401/403 | Bad secret/permissions | Fix vault secret; reduce to needed Graph scopes |
| Duplicate cubes | Create-identities on | Disable; clean carefully |
| UPN mismatch | Email drift | Prefer employeeId extension |
| Type missing | IIQ edition | Use SCIM alternate + document |
| Overlap with AD certs | Dual cert noise | Scope entitlements per app owner |

## Training binder evidence

- `MNB-Entra-hybrid-59.md` including registration worksheet
- Application screenshot or shell notes
- Feature matrix row updated if Unknown→Y/N refined

**Examiner question:** “Which system creates the identity cube when a banker joins—Entra, AD, or HR?”

## Knowledge check

1. Preferred connector for Entra ID in Meridian matrix?
2. Alternate connector?
3. Should `MNB-EntraID` create identities?
4. Where do client secrets belong?
5. Name one disable Expected result field.
6. Why exclude Entra guests from normal workforce cube creation?

### Answers

1. Azure Active Directory.
2. SCIM 2.0.
3. No.
4. Secret vault / secure config—not git or lesson notes with real values.
5. `accountEnabled=false` (or equivalent disabled state) on the cloud account.
6. Guests are B2B/external; creating workforce cubes bypasses HR joiner controls.

## Stretch lab

- Compare Azure AD connector attributes to SCIM Enterprise User schema for Lesson 69–70.
- Draft Conditional Access / MFA governance notes pointing to Lesson 87 (Duo patterns).
- Design delta aggregation watermark approach for large tenants.

## Summary

- `MNB-EntraID` is Meridian’s cloud directory Application—non-authoritative.
- App registration and correlation are lab-without-live-tenant deliverables.
- AD and Entra coexist under HR identity truth.
- Guest/B2B accounts stay outside workforce cube creation unless Architecture exceptions apply.

---

**Previous:** [Lesson 58 — LDAP / OpenLDAP Connector](58-ldap-openldap-connector.md)  
**Next:** [Lesson 60 — LDIF Connector](60-ldif-connector.md)
