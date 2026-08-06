# Lesson 216 — Birthright Roles Against Live Apps

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lesson 214  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 23–28

> **Why:** A birthright role that doesn’t provision a real entitlement is just a label. Prove what every employee gets on day one without a request — and keep Wire/CRM out of automatic assignment.

## What this is

Two Bundle patterns, opposite assignment paths:

| Pattern | Bundle | How you get it | Example entitlement |
| --- | --- | --- | --- |
| Birthright | `MNB-Bundle-Birthright-Employee` | Selector match + refresh | OpenLDAP `MNB-Employees` group |
| Request / IT | `MNB-Bundle-Wire-Initiator` | Access request or direct assign | `WIRE_INIT` on Wire/Core |

`MNB-Bundle-Birthright-Employee` is a `business`-type Bundle whose `IdentitySelector` matches active `employeeType=Employee`. `MNB-Bundle-Wire-Initiator` is `requestable=true` — nobody gets it automatically.

Classic 23–28 covered role types; this lesson closes the live gap: roles must attach real profiles/entitlements on `MNB-OpenLDAP`, Keycloak/`MNB-Okta`, or `MNB-WirePortal` before they count.

## Know these

```text
employeeType=Employee + inactive=false
  → birthright detection/assignment
  → provision profile → live group/entitlement

Wire / CRM / Cloud  → NEVER birthright (request + approval)
```

| Idea | Detail |
| --- | --- |
| Selector | Who *matches* the role — not the same as who *has access* yet |
| Profile / entitlement | What actually provisions on a live app |
| Detection vs assignment | Refresh with role flags materializes matches |

- **Wrong way:** Marking Wire Initiator as birthright “so Treasury isn’t delayed.” Dual-control and SoD (Lesson 224) collapse the moment initiate is automatic.

## Intent

- Wire birthright to a checkable OpenLDAP entitlement.
- Confirm Wire Initiator is requestable and provisions `WIRE_INIT` when assigned.
- Run role detection/assignment refresh for Helen vs Priya and show different outcomes.
- Confirm contractors do not match the birthright selector.

## Before you start

- [ ] Correlation from Lesson 214 clean for Helen / Priya / Marcus
- [ ] `MNB-Bundle-Birthright-Employee` and `MNB-Bundle-Wire-Initiator` imported (seed)
- [ ] OpenLDAP groups aggregated (Lesson 204)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/216
```

## Do this

### Task 1 — Inspect the birthright selector

Open **Setup → Roles → Bundles → MNB-Bundle-Birthright-Employee**. Confirm the MatchExpression:

- `employeeType=Employee`
- AND `inactive=false`

- **Why:** this is the gate that excludes contractors and terminated workers from day-one access.
- **Expect:** matches Helen, Priya, Marcus; excludes contractors (`rachel.khatri`, `james.nguyen`) and terminated.

### Task 2 — Attach a real OpenLDAP entitlement

Attach a provisioning target: profile / required entitlement for OpenLDAP `groups` / `memberOf` → `MNB-Employees` (or the equivalent `groupOfUniqueNames` from Lesson 204).

- **Why:** turns a matching label into something that moves a live account.
- **Expect:** role editor shows an application entitlement, not selector-only.

### Task 3 — Confirm Wire Initiator is request-only

Open `MNB-Bundle-Wire-Initiator`:

- `requestable=true`
- Maps to `WIRE_INIT` on `MNB-WirePortal` or `MNB-CoreBanking` (same target you used in 208/209)

- **Why:** Wire must never be birthright — you’ll assign it explicitly to Priya later.
- **Expect:** requesting/assigning the role can produce a provisioning plan against that app.

### Task 4 — Refresh with role detection and provisioning

Run **Identity Refresh** with role detection **and** role provisioning enabled, scoped to Helen, Priya, and Marcus.

- **Why:** attribute-only refresh won’t materialize roles or fire provisioning.
- **Expect:** Task Result shows detection/assignment events.

### Task 5 — Prove Helen’s birthright on the cube and in LDAP

On Helen’s cube **Roles** tab:

1. Confirm birthright assigned
2. Confirm OpenLDAP group entitlement present under her account

- **Why:** automatic, no IdentityRequest, no approval — classic birthright proof.
- **Expect:** role + live LDAP group — not metadata alone.

Save a screenshot under `~/iiq-lab-evidence/sandbox/216/`.

### Task 6 — Prove Priya’s different outcome

On Priya’s cube: birthright present; `MNB-Bundle-Wire-Initiator` **absent**.

- **Why:** same refresh, different outcomes — selector vs explicit assignment.
- **Expect:** no Wire role until you assign it.

### Task 7 — Assign Wire Initiator to Priya

Assign `MNB-Bundle-Wire-Initiator` to Priya (direct assign is fine; full request path is Lesson 221). Re-run refresh with provisioning.

- **Why:** proves the requestable role actually provisions `WIRE_INIT` on the live target.
- **Expect:** `WIRE_INIT` correlated on the wire target, attributable to the role.

### Task 8 — Optional IdP contrast

If Keycloak shows Priya in `wire-initiators` and Helen only in `mnb-employees` / `portal-users`, note it under evidence.

- **Why:** same birthright vs requested story on the IdP side.
- **Expect:** evidence note under `216/`.

## If it fails

| Symptom | Fix |
| --- | --- |
| No roles detected | Refresh lacked role assignment/detection flags |
| Birthright assigns, no LDAP group | Selector without profile — Task 2 incomplete |
| Wire role assigns, entitlement unchanged | Role not mapped to `WIRE_INIT` |
| Contractors get birthright | Selector missing `employeeType=Employee`, or identity master type wrong |
| Terminated still birthright | `inactive=false` not evaluated — re-aggregate Workday |

## You are done when

- [ ] Helen has birthright + live OpenLDAP group entitlement
- [ ] Priya has birthright plus role-driven `WIRE_INIT` after assignment
- [ ] Contractors do not match the birthright selector

## Control note

- **Control:** Birthright vs request-only access packaging
- **Owner:** IAM Architecture + app owners (Wire)
- **SLA (lab):** birthright materializes same refresh cycle as joiner
- **Evidence:** `~/iiq-lab-evidence/sandbox/216/` — Helen Roles tab, Priya `WIRE_INIT` link, contractor non-match

## Quick check

1. Who should never get Wire Initiator via birthright? → anyone automatically — Wire is request-only
2. What two selector terms gate employee birthright? → `employeeType=Employee` and `inactive=false`
3. Detection without a profile proves what? → only membership metadata — not live access

## Feedback

Could you explain birthright vs Wire Initiator without opening the role editor? If birthright assigned but LDAP stayed empty, note whether Task 2’s profile was actually saved — selector-only is the usual miss.

## Navigate

- Previous: [Lesson 215](215-attribute-sync-live.md)
- Next: [Lesson 217](217-joiner-lcm-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
