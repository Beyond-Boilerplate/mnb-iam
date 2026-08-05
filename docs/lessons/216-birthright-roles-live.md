# Lesson 216 — Birthright Roles Against Live Apps

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~65 minutes  
**Prereq:** Lesson 214  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 23–28

> **Why (1–2 lines):** A birthright role that doesn’t provision a real entitlement is just a label — examiners ask what every employee gets on day one without a request. Birthright vs request-only is how you keep Wire/CRM out of automatic assignment.

## What this is

`MNB-Bundle-Birthright-Employee` is a `business`-type Bundle whose `IdentitySelector` matches active `employeeType=Employee` — automatic day-one access, no request. `MNB-Bundle-Wire-Initiator` is an `it`-type Bundle with `requestable=true` — nobody gets it automatically. Classic 23–28 covered role types, detection vs assignment, and privileged packaging; this lesson closes the live gap: roles in `config/Bundle/` must attach real profiles/entitlements on `MNB-OpenLDAP`, Keycloak/`MNB-Okta`, or `MNB-WirePortal` before they count.

## Know these

| Pattern | Bundle | How you get it | Example entitlement |
| --- | --- | --- | --- |
| Birthright | `MNB-Bundle-Birthright-Employee` | Selector match + refresh | OpenLDAP `MNB-Employees` group |
| Request / IT | `MNB-Bundle-Wire-Initiator` | Access request or direct assign | `WIRE_INIT` on Wire/Core |
| Privileged (later) | BreakGlass / CloudAdmin | Approval + sunset | PAM safe membership (255) |

```text
employeeType=Employee + inactive=false
  → birthright detection/assignment
  → provision profile → live group/entitlement
Wire / CRM / Cloud  → NEVER birthright (request + approval)
```

**Wrong way:** Marking Wire Initiator as birthright “so Treasury isn’t delayed.” Dual-control and SoD (224) collapse the moment initiate is automatic.

## Intent

- Wire birthright to a checkable OpenLDAP (or directory) entitlement.
- Confirm Wire Initiator is requestable and provisions `WIRE_INIT` when assigned.
- Run role detection/assignment refresh for Helen vs Priya and show different outcomes.
- Exclude contractors from birthright via selector.

## Before you start

- [ ] Correlation from Lesson 214 is clean for Helen / Priya / Marcus
- [ ] `MNB-Bundle-Birthright-Employee` and `MNB-Bundle-Wire-Initiator` imported (seed)
- [ ] OpenLDAP groups aggregated (Lesson 204)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/216`

## Do this

1. Open **Setup → Roles → Bundles → MNB-Bundle-Birthright-Employee**. Confirm MatchExpression (`employeeType=Employee` AND `inactive=false`).  
   **Expect:** Matches Helen, Priya, Marcus; excludes contractors (`rachel.khatri`, `james.nguyen`) and terminated.

2. Attach a real provisioning target: profile / required entitlement for OpenLDAP `groups`/`memberOf` → `MNB-Employees` (or equivalent `groupOfUniqueNames` from Lesson 204).  
   **Why:** Turns a matching label into something that moves a live account.  
   **Expect:** Role editor shows an application entitlement, not selector-only.

3. Confirm `MNB-Bundle-Wire-Initiator` is `requestable=true` and maps to `WIRE_INIT` on `MNB-WirePortal` or `MNB-CoreBanking` (same target you use in 208/209).  
   **Expect:** Requesting/assigning the role can produce a provisioning plan against that app.

4. Run **Identity Refresh** with role detection **and** role provisioning enabled, scoped to Helen, Priya, Marcus.  
   **Expect:** Task Result shows detection/assignment events (not a bare attribute-only refresh).

5. On Helen’s cube **Roles** tab: birthright assigned; OpenLDAP group entitlement present under her account.  
   **Expect:** Automatic, no IdentityRequest, no approval — classic birthright proof.

6. On Priya: birthright present; `MNB-Bundle-Wire-Initiator` **absent** until you assign it.  
   **Expect:** Same refresh, different outcomes — selector vs explicit assignment.

7. Assign `MNB-Bundle-Wire-Initiator` to Priya (direct assign is fine; full request path is Lesson 221). Re-run refresh with provisioning.  
   **Expect:** `WIRE_INIT` correlated on the live wire target, attributable to the role.

8. Optional IdP contrast: if Keycloak shows Priya in `wire-initiators` and Helen only in `mnb-employees` / `portal-users`, note it — same birthright vs requested story on the IdP.  
   **Expect:** Evidence note under `216/`.

## If it fails

- **No roles detected** — refresh lacked role assignment/detection flags.
- **Birthright assigns, no LDAP group** — selector without profile (step 2 incomplete).
- **Wire role assigns, entitlement unchanged** — role not mapped to `WIRE_INIT`.
- **Contractors get birthright** — selector missing `employeeType=Employee` or identity master type wrong.
- **Terminated still birthright** — `inactive=false` not evaluated; re-aggregate HCM.

## You are done when

Helen has birthright + live OpenLDAP group entitlement; Priya has birthright plus role-driven `WIRE_INIT` after assignment; contractors do not match the birthright selector.

## Control note

- **Control:** Birthright vs request-only access packaging.  
- **Owner:** IAM Architecture + app owners (Wire).  
- **SLA (lab):** Birthright materializes same refresh cycle as joiner; production often same-day hire.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/216/` — Helen Roles tab, Priya WIRE_INIT link, contractor non-match.

## Quick check

1. Who should never get Wire Initiator via birthright? → Anyone automatically — Wire is request-only.  
2. What two selector terms gate employee birthright? → `employeeType=Employee` and `inactive=false`.  
3. Detection without a profile proves what? → Only membership metadata — not live access.

## Navigate

- Previous: Lesson 215  
- Next: Lesson 217  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
