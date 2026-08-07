# Lesson 216 — Birthright Roles Against Live Apps

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~95 minutes  
**Prereq:** Lessons 211, 214  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 23–28

> **Why:** A birthright role that doesn’t provision a real entitlement is just a label. Day-one access must include directory **and** IdP Portal groups — or Employee Portal SSO stays a manual Keycloak chore.

## What this is

IdentityIQ stock role types split **who** from **what**:

| Layer | Type | Answers | This lesson |
| --- | --- | --- | --- |
| IT role | `it` | *What* entitlements provision | OpenLDAP `all-employees`; Keycloak `mnb-employees` + `portal-users`; Wire `WIRE_INIT` |
| Business role | `business` | *Who* gets those packs | Birthright selector; requestable Wire Initiator |

```text
MNB-Bundle-Birthright-Employee  (business)
 ├── Assignment Rule ── employeeType=Employee AND inactive=false
 ├── Required Roles ──► MNB-IT-OpenLDAP-Employees  (it)
 │                            └── all-employees on MNB-OpenLDAP
 └── Required Roles ──► MNB-IT-IdP-Portal  (it)
                              └── mnb-employees + portal-users on MNB-Keycloak-IdP

MNB-Bundle-Wire-Initiator  (business, requestable)
 └── Required Roles ──► MNB-IT-WireInit  (it)
                              └── WIRE_INIT on Wire/Core
```

> **Watch out:** OpenLDAP’s employee baseline group is **`all-employees`**. Keycloak’s Portal gate is **`portal-users`** (plus workforce `mnb-employees`). Samba’s `MNB-Employees` is a different directory (Lesson 205).

`MNB-Keycloak-IdP` is a SCIM 2.0 Application aimed at connector-mock’s **live Keycloak facade** (`http://connector-mock:8091/idp/scim/v2`) — not the Okta-shaped mock used in Lesson 238. Birthright owns Portal groups through this app.

Business roles show *“Entitlements section is not supported”* — that is expected. Put entitlements on the **IT** packs; point the business role at them via **Required Roles**.


## Know these

```text
employeeType=Employee + inactive=false
  → birthright detection/assignment
  → OpenLDAP all-employees
  → Keycloak mnb-employees + portal-users   ← Portal SSO ready

Wire / CRM / Cloud  → NEVER birthright (request + approval)
```

| Idea | Detail |
| --- | --- |
| IT role | Holds the entitlement profile — the thing that can provision |
| Business role | Holds the selector / requestable flag — who may get the IT packs |
| Required Roles | Business → one or more IT packs; without them, assignment is label-only |
| `MNB-Keycloak-IdP` | Live Keycloak via `/idp/scim` facade (not manual Admin console) |

- **Wrong way:** Putting `WIRE_INIT` on the birthright IT pack “so Treasury isn’t delayed.”
- **Wrong way:** Birthright with only OpenLDAP — Portal still needs Keycloak groups.
- **Wrong way:** Hand-creating Keycloak users in Lesson 217 when birthright already owns IdP packs.

## Intent

- Bring up the IdP provisioner (`MNB-Keycloak-IdP` + Keycloak `iiq-scim` roles).
- Create IT + business birthright roles wired to OpenLDAP **and** Keycloak Portal groups.
- Create IT + business Wire Initiator roles (`requestable=true`) wired to `WIRE_INIT`.
- Prove Helen gets LDAP + IdP from birthright; Wire stays off until assigned.
- Confirm contractors do not match the birthright selector.

## Before you start

- [ ] Correlation from Lesson 214 clean for Helen / Priya / Marcus
- [ ] Keycloak `meridian` up (Lesson 211)
- [ ] OpenLDAP **Account Group Aggregation** run — catalog shows `all-employees`
- [ ] `WIRE_INIT` exists on `MNB-WirePortal` or `MNB-CoreBanking`
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/216
```

### Where to create roles


| Step   | Path / choice                                    |
| ------ | ------------------------------------------------ |
| Open   | **Setup → Roles** → **Role Viewer**              |
| Create | **Add** / **Create New** → **Role** (manual)     |
| Skip   | Business/IT Role Mining and Entitlement Analysis |


Wrong click lands you in a mining wizard — cancel and choose **Role**.

## Do this

### Task 1 — Promote OpenLDAP groups into Entitlement Catalog

Account aggregation alone does **not** fill the catalog for **directory groups**. OpenLDAP needs a separate **Account Group Aggregation**.

1. **Setup → Tasks**, search `MNB`.
2. If `MNB-OpenLDAP-Group-Aggregation` is missing:
   - **New Task → Account Group Aggregation**
   - Name: `MNB-OpenLDAP-Group-Aggregation`
   - Application: **`MNB-OpenLDAP` only**
   - **Save**
3. Open that task → **Run Now** → wait for Task Result success.
4. **Applications → Entitlement Catalog** → filter Application = `MNB-OpenLDAP`.
5. Confirm **`all-employees`** (and peers like `dept-technology`, `wire-initiators`) appear.

- **Why:** Role Editor can only attach entitlements that aggregation already promoted.
- **Expect:** Catalog lists OpenLDAP groups; `all-employees` is searchable.

> **Watch out:** Do **not** add `MNB-WirePortal` to this (or any) Account Group Aggregation task. Wire is a Web Services app with account-level `entitlements[]` — it has no Group Aggregation operation, so the task fails with *No configuration found for 'Group Aggregation'*.

### Task 1b — Confirm `WIRE_INIT` from Wire **Account** Aggregation

`WIRE_INIT` is promoted when **Account Aggregation** reads the managed multi-valued `entitlements` attribute (Lesson 209) — not via group aggregation.

1. **Setup → Tasks** → run **Account Aggregation** that includes `MNB-WirePortal` (or create one scoped to that app).
2. Entitlement Catalog → filter Application = `MNB-WirePortal` → find **`WIRE_INIT`**.
3. Or open **priya.wire** → Application Accounts → `MNB-WirePortal` → confirm `WIRE_INIT` on the link.

- **Why:** same catalog, different promotion path — groups vs account entitlement attribute.
- **Expect:** `WIRE_INIT` findable without ever running Group Aggregation on Wire.

### Task 1c — Bring up Keycloak IdP provisioning

Birthright will create real Keycloak users through **`MNB-Keycloak-IdP`**. That app talks to connector-mock’s `/idp/scim/v2` facade, which calls Keycloak Admin API as client `iiq-scim`.

1. Enable the service-account roles (safe to re-run):

```bash
./tools/lab/enterprise/keycloak-enable-iiq-provisioner.sh
```

2. Rebuild/restart connector-mock if `/idp/health` is missing:

```bash
docker compose -f docker-compose.iiq.yml -f docker-compose.connectors.yml build connector-mock
docker compose -f docker-compose.iiq.yml -f docker-compose.connectors.yml up -d connector-mock
curl -s http://localhost:8091/idp/health | python3 -m json.tool
```

- **Expect:** `"ok": true` and groups list includes `portal-users`, `mnb-employees`.

3. Confirm Application **`MNB-Keycloak-IdP`** exists (enterprise seed). If missing, Debug → Import `config/Application/MNB-Application-Keycloak-IdP.xml`.
4. Run **Account Aggregation** and **Account Group Aggregation** for `MNB-Keycloak-IdP` (create tasks if needed; app = that name only).
5. Entitlement Catalog → Application `MNB-Keycloak-IdP` → confirm **`portal-users`** and **`mnb-employees`**.
6. Open one entitlement in Debug (`ManagedAttribute`) and confirm **`attribute=groups`** (not blank). If blank, the account schema is missing `schemaObjectType="group"` on `groups` — re-import `config/Application/MNB-Application-Keycloak-IdP.xml`, delete the bad catalog rows, and re-run group aggregation.

- **Why:** without managed group entitlements linked to account attribute `groups`, the IdP IT pack cannot provision memberships.
- **Expect:** both groups searchable; `attribute=groups`; values are names (`portal-users`), not UUIDs.

> **Watch out:** `MNB-Okta` is a different Application (Lesson 238 mock SCIM). Do **not** attach birthright IdP groups there.

### Task 2 — Create IT pack `MNB-IT-OpenLDAP-Employees`

Entitlements live here. One extra critical entitlement in this pack is a design defect.

1. **Setup → Roles** → **Create New → Role**.
2. Set:
  - **Name:** `MNB-IT-OpenLDAP-Employees`
  - **Type:** **it**
  - **Owner:** `spadmin`
  - **Description:** `IT pack: OpenLDAP all-employees group only. Required by employee birthright.`
3. Leave **Disabled** unchecked. Leave Assignment Rule empty.
4. **Entitlements → Add** → prefer **Simple View**:
  - **Application:** `MNB-OpenLDAP`
  - Select **`all-employees`** only
  - Submit / OK the profile
5. Confirm the list shows **only** that group — no `WIRE_INIT`, CRM, or cloud.
6. **Submit** the IT role.

- **Why:** stock IIQ supports Entitlements on type **it**, not on **business**.
- **Expect:** `MNB-IT-OpenLDAP-Employees` exists; no Entitlements warning.

> **Watch out:** If you still see *Entitlements section is not supported*, Type is still **business** — change to **it** and re-add.

### Task 2b — Create IT pack `MNB-IT-IdP-Portal`

Portal SSO (Lesson 212) checks Keycloak group **`portal-users`**. Workforce baseline is **`mnb-employees`**. Put both on an IT pack — not on the business role.

1. **Create New → Role** → Name `MNB-IT-IdP-Portal`, Type **it**, Owner `spadmin`.
2. Description: `IT pack: Keycloak mnb-employees + portal-users. Required by employee birthright for Portal SSO.`
3. **Entitlements → Add** → Application **`MNB-Keycloak-IdP`** → select **`mnb-employees`** and **`portal-users`** only.
4. **Submit**.

- **Why:** one joiner refresh should create the IdP account and group memberships — no Admin console click in Lesson 217.
- **Expect:** IT pack lists exactly those two groups.

### Task 3 — Create business role `MNB-Bundle-Birthright-Employee`

This role answers *who*; the IT packs answer *what access*.

1. **Create New → Role** again (manual **Role**).
2. Set:
   - **Name:** `MNB-Bundle-Birthright-Employee`
   - **Type:** **business**
   - **Owner:** `spadmin`
   - **Description:** `Baseline OpenLDAP + Keycloak Portal access for active Meridian employees. No payment or cloud privilege.`
3. Leave **Disabled** unchecked. If **Requestable** appears, leave it **off**.
4. **Ignore** the Entitlements warning.
5. **Required Roles → Modify Required Roles** → add **both**:
   - `MNB-IT-OpenLDAP-Employees`
   - `MNB-IT-IdP-Portal`
6. **Assignment Rule → Match List**:

   | Attribute | Operator | Value |
   | --- | --- | --- |
   | `employeeType` | equals | `Employee` |
   | `inactive` (or **Is Inactive**) | equals | `false` / **False** |

7. Do **not** use stock **Type = Employee**.
8. **Submit**. Confirm both Required Roles + Match List.

- **Why:** contractors and terminated workers stay out of day-one LDAP **and** Portal.
- **Expect:** matches Helen, Priya, Marcus; excludes contractors and terminated.

### Task 4 — Create IT pack `MNB-IT-WireInit`

1. **Create New → Role** → Name `MNB-IT-WireInit`, Type **it**, Owner `spadmin`.
2. Description: `IT pack: WIRE_INIT only. Never WIRE_APPR. Required by Wire Initiator business role.`
3. **Entitlements → Add** → application = your Wire/Core target → **`WIRE_INIT` only** — never `WIRE_APPR`.
4. **Submit**.

- **Why:** dual control stays intact only if initiate and approve never share a pack.
- **Expect:** IT pack lists `WIRE_INIT` alone.

### Task 5 — Create business role `MNB-Bundle-Wire-Initiator`

1. **Create New → Role** → Name `MNB-Bundle-Wire-Initiator`, Type **business**, Owner `spadmin`.
2. Description: `Wire Portal initiate only. Requestable — never birthright.`
3. Ignore Entitlements warning. **Required Roles** → add **`MNB-IT-WireInit`**.
4. Leave **Assignment Rule empty** — nobody gets this automatically.
5. Set **Requestable** / **Available in Access Request** to **on** (`requestable=true`).
6. **Submit**.

- **Why:** Wire must never be birthright — you’ll assign it explicitly to Priya later.
- **Expect:** requesting/assigning the role can produce a provisioning plan against the Wire/Core app.

### Task 6 — Refresh with role detection and provisioning

Run **Identity Refresh** with role detection **and** role provisioning enabled, scoped to Helen, Priya, and Marcus.

- **Why:** attribute-only refresh won’t materialize roles or fire provisioning.
- **Expect:** Task Result shows detection/assignment events for birthright; Wire Initiator still absent until assigned.

### Task 7 — Prove Helen’s birthright on LDAP **and** Keycloak

On Helen’s cube **Roles** tab:

1. Confirm `MNB-Bundle-Birthright-Employee` assigned
2. Confirm OpenLDAP `all-employees` under her account
3. Confirm **`MNB-Keycloak-IdP`** link with groups `mnb-employees` and `portal-users`

Or prove IdP from the facade:

```bash
curl -s 'http://localhost:8091/idp/scim/v2/Users?filter=userName%20eq%20%22helen.ross%22' \
  | python3 -m json.tool
```

- **Why:** automatic, no IdentityRequest — directory **and** Portal groups from birthright.
- **Expect:** business role + LDAP group + Keycloak groups — not metadata alone.

Save a screenshot under `~/iiq-lab-evidence/sandbox/216/`.

### Task 8 — Prove Priya’s different outcome

On Priya’s cube: birthright present (LDAP + IdP); `MNB-Bundle-Wire-Initiator` **absent**.

- **Why:** same refresh, different outcomes — selector vs explicit assignment.
- **Expect:** no Wire role until you assign it; Portal groups still present from birthright.

### Task 9 — Assign Wire Initiator to Priya

Assign `MNB-Bundle-Wire-Initiator` to Priya (direct assign is fine; full request path is Lesson 221). Re-run refresh with provisioning.

- **Why:** proves the requestable business role actually provisions `WIRE_INIT` via the Required IT pack.
- **Expect:** `WIRE_INIT` correlated on the wire target, attributable to the role.

### Task 10 — IdP contrast (Wire groups stay request-driven)

In Keycloak Admin (`meridian`) or via `/idp/scim`, confirm Helen is **not** in `wire-initiators` unless you put that group on a requestable pack. Birthright only owns `mnb-employees` + `portal-users`.

- **Why:** same birthright vs requested story on the IdP side.
- **Expect:** evidence note under `216/`.

## If it fails

| Symptom | Fix |
| --- | --- |
| Entitlements not supported on role | Type is **business** — put ents on the **IT** pack; use Required Roles |
| `/idp/health` missing or ok:false | Rebuild connector-mock; run `keycloak-enable-iiq-provisioner.sh` |
| IdP groups missing from catalog | Account **Group** Aggregation on `MNB-Keycloak-IdP` |
| IdP entitlements have blank `attribute` / UUID values | Re-import `MNB-Application-Keycloak-IdP.xml` (`groups` must have `schemaObjectType="group"`; group identity=`displayName`); delete old MAs; re-agg groups |
| Attached groups to `MNB-Okta` | Wrong app — use `MNB-Keycloak-IdP` |
| Birthright assigns, no Keycloak user | Required Roles missing `MNB-IT-IdP-Portal`, or refresh lacked provisioning |
| Group Aggregation fails on `MNB-WirePortal` | Expected — use Account Aggregation (Task 1b) |
| Searching `MNB-Employees` under OpenLDAP | Use **`all-employees`**; Samba name is different |
| Birthright assigns, no LDAP group | Required Roles / IT pack missing `all-employees` |
| Contractors get birthright | Selector missing `employeeType=Employee` |

## You are done when

- [ ] `MNB-IT-OpenLDAP-Employees` + `MNB-IT-IdP-Portal` + `MNB-Bundle-Birthright-Employee` (two IT packs on business)
- [ ] `MNB-IT-WireInit` + `MNB-Bundle-Wire-Initiator` created (requestable)
- [ ] Helen has birthright → OpenLDAP `all-employees` **and** Keycloak `portal-users` / `mnb-employees`
- [ ] Priya has birthright plus role-driven `WIRE_INIT` after assignment
- [ ] Contractors do not match the birthright selector

## Control note

- **Control:** Birthright vs request-only packaging (directory + IdP Portal on birthright; Wire request-only)
- **Owner:** IAM Architecture + app owners (Wire) + IdP
- **SLA (lab):** birthright materializes same refresh cycle as joiner
- **Evidence:** `~/iiq-lab-evidence/sandbox/216/` — Helen Roles + IdP groups, Priya `WIRE_INIT`, contractor non-match

## Quick check

1. Who should never get Wire Initiator via birthright? → anyone automatically — Wire is request-only
2. What two selector terms gate employee birthright? → `employeeType=Employee` and `inactive=false`
3. Which two Keycloak groups must birthright own for Portal SSO? → `mnb-employees` and `portal-users`
4. Why can’t you put those groups on the business role? → stock **business** type does not support Entitlements — use **IT** packs + Required Roles
5. `MNB-Okta` vs `MNB-Keycloak-IdP` — which one provisions live Keycloak for birthright? → **`MNB-Keycloak-IdP`**

## Feedback

Could you explain why Portal SSO needs an IdP IT pack on birthright without opening Keycloak Admin? If Helen got LDAP but not `portal-users`, note whether Required Roles included `MNB-IT-IdP-Portal` and whether `/idp/health` was ok.

## Navigate

- Previous: [Lesson 215](215-attribute-sync-live.md)
- Next: [Lesson 217](217-joiner-lcm-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)

