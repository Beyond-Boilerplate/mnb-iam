# Lesson 216 — Birthright Roles Against Live Apps

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lesson 214  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 23–28

> **Why:** A birthright role that doesn’t provision a real entitlement is just a label. Build the IT + business pair yourself, prove what every employee gets on day one without a request — and keep Wire out of automatic assignment.

## What this is

IdentityIQ stock role types split **who** from **what**:


| Layer         | Type       | Answers                       | This lesson                                     |
| ------------- | ---------- | ----------------------------- | ----------------------------------------------- |
| IT role       | `it`       | *What* entitlements provision | OpenLDAP `all-employees`; Wire `WIRE_INIT`      |
| Business role | `business` | *Who* gets those packs        | Birthright selector; requestable Wire Initiator |


```text
MNB-Bundle-Birthright-Employee  (business)
 ├── Assignment Rule ── employeeType=Employee AND inactive=false
 └── Required Roles ──► MNB-IT-OpenLDAP-Employees  (it)
                              └── Entitlements ──► all-employees on MNB-OpenLDAP

MNB-Bundle-Wire-Initiator  (business, requestable)
 └── Required Roles ──► MNB-IT-WireInit  (it)
                              └── Entitlements ──► WIRE_INIT on Wire/Core
```

> **Watch out:** OpenLDAP’s employee baseline group is **`all-employees`** (`cn=all-employees,ou=groups,…`). **`MNB-Employees`** is a Samba AD group (Lesson 205) — it will not appear under `MNB-OpenLDAP`.

Business roles show *“Entitlements section is not supported”* — that is expected. Put entitlements on the **IT** pack; point the business role at it via **Required Roles**.

Classic 23–28 covered the same two-tier model; this lesson builds it against live `MNB-OpenLDAP` and Wire — nothing is pre-seeded for you.

## Know these

```text
employeeType=Employee + inactive=false
  → birthright detection/assignment
  → Required IT pack → live OpenLDAP group

Wire / CRM / Cloud  → NEVER birthright (request + approval)
```


| Idea                    | Detail                                                          |
| ----------------------- | --------------------------------------------------------------- |
| IT role                 | Holds the entitlement profile — the thing that can provision    |
| Business role           | Holds the selector / requestable flag — who may get the IT pack |
| Required Roles          | Business → IT link; without it, assignment is label-only        |
| Detection vs assignment | Refresh with role flags materializes matches                    |


- **Wrong way:** Putting `WIRE_INIT` on the birthright IT pack “so Treasury isn’t delayed.” Dual-control and SoD (Lesson 224) collapse the moment initiate is automatic.
- **Wrong way:** Creating only a business role and ignoring the Entitlements warning — selector matches, nothing provisions.

## Intent

- Create IT + business birthright roles wired to OpenLDAP `all-employees`.
- Create IT + business Wire Initiator roles (`requestable=true`) wired to `WIRE_INIT`.
- Run role detection/assignment refresh for Helen vs Priya and show different outcomes.
- Confirm contractors do not match the birthright selector.

## Before you start

- [ ] Correlation from Lesson 214 clean for Helen / Priya / Marcus
- [ ] OpenLDAP **Account Group Aggregation** run (Lesson 204) — catalog shows `all-employees` for `MNB-OpenLDAP`
- [ ] `WIRE_INIT` exists on `MNB-WirePortal` or `MNB-CoreBanking` (Lesson 208/209)
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

### Task 3 — Create business role `MNB-Bundle-Birthright-Employee`

This role answers *who*; the IT pack answers *what access*.

1. **Create New → Role** again (manual **Role**).
2. Set:
  - **Name:** `MNB-Bundle-Birthright-Employee`
  - **Type:** **business**
  - **Owner:** `spadmin`
  - **Description:** `Baseline OpenLDAP access for active Meridian employees. No payment or cloud privilege.`
3. Leave **Disabled** unchecked. If **Requestable** appears, leave it **off**.
4. **Ignore** the Entitlements warning — do **not** Add `all-employees` here.
5. **Required Roles → Modify Required Roles** → add **`MNB-IT-OpenLDAP-Employees`** → Save.
6. **Assignment Rule → Match List** (not Filter / Script unless Match List is unavailable):

  | Attribute                       | Operator | Value               |
  | ------------------------------- | -------- | ------------------- |
  | `employeeType`                  | equals   | `Employee`          |
  | `inactive` (or **Is Inactive**) | equals   | `false` / **False** |

7. Do **not** use stock **Type = Employee** — that field is usually blank on Workday-first cubes.
8. **Submit**. In Role Viewer, confirm Required Role + Match List summary.

- **Why:** this gate excludes contractors and terminated workers from day-one access.
- **Expect:** matches Helen, Priya, Marcus; excludes contractors (`rachel.khatri`, `james.nguyen`) and terminated.

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

### Task 7 — Prove Helen’s birthright on the cube and in LDAP

On Helen’s cube **Roles** tab:

1. Confirm `MNB-Bundle-Birthright-Employee` assigned
2. Confirm OpenLDAP `all-employees` entitlement present under her account

- **Why:** automatic, no IdentityRequest, no approval — classic birthright proof.
- **Expect:** business role + live LDAP group — not metadata alone.

Save a screenshot under `~/iiq-lab-evidence/sandbox/216/`.

### Task 8 — Prove Priya’s different outcome

On Priya’s cube: birthright present; `MNB-Bundle-Wire-Initiator` **absent**.

- **Why:** same refresh, different outcomes — selector vs explicit assignment.
- **Expect:** no Wire role until you assign it.

### Task 9 — Assign Wire Initiator to Priya

Assign `MNB-Bundle-Wire-Initiator` to Priya (direct assign is fine; full request path is Lesson 221). Re-run refresh with provisioning.

- **Why:** proves the requestable business role actually provisions `WIRE_INIT` via the Required IT pack.
- **Expect:** `WIRE_INIT` correlated on the wire target, attributable to the role.

### Task 10 — Optional IdP contrast

If Keycloak shows Priya in `wire-initiators` and Helen only in `mnb-employees` / `portal-users`, note it under evidence.

- **Why:** same birthright vs requested story on the IdP side.
- **Expect:** evidence note under `216/`.

## If it fails


| Symptom | Fix |
| --- | --- |
| Entitlements not supported on role | Type is **business** — put ents on the **IT** pack; use Required Roles |
| Landed in mining wizard | Cancel; **Create New → Role** (manual) |
| No roles detected | Refresh lacked role assignment/detection flags |
| Entitlement Catalog empty for LDAP | Run **Account Group Aggregation** on `MNB-OpenLDAP` only (Task 1) |
| Group Aggregation fails on `MNB-WirePortal` | Expected — no Group Aggregation endpoint; use **Account Aggregation** (Task 1b) |
| Searching `MNB-Employees` under OpenLDAP | Wrong directory — use **`all-employees`**; `MNB-Employees` is Samba (Lesson 205) |
| Birthright assigns, no LDAP group | Required Roles empty, or IT pack missing `all-employees` |
| Wire role assigns, entitlement unchanged | IT pack not mapped to `WIRE_INIT`, or Required Roles missing |
| Contractors get birthright | Selector missing `employeeType=Employee`, or identity master type wrong |
| Terminated still birthright | `inactive=false` not evaluated — re-aggregate Workday |
| Cannot find entitlement in Add dialog | OpenLDAP → re-run group agg; Wire → re-run **account** agg with `entitlements` managed=true |


## You are done when

- [ ] `MNB-IT-OpenLDAP-Employees` + `MNB-Bundle-Birthright-Employee` created (IT + business)
- [ ] `MNB-IT-WireInit` + `MNB-Bundle-Wire-Initiator` created (IT + requestable business)
- [ ] Helen has birthright + live OpenLDAP group entitlement
- [ ] Priya has birthright plus role-driven `WIRE_INIT` after assignment
- [ ] Contractors do not match the birthright selector

## Control note

- **Control:** Birthright vs request-only access packaging (IT packs hold privilege; business roles hold assignment)
- **Owner:** IAM Architecture + app owners (Wire)
- **SLA (lab):** birthright materializes same refresh cycle as joiner
- **Evidence:** `~/iiq-lab-evidence/sandbox/216/` — Helen Roles tab, Priya `WIRE_INIT` link, contractor non-match

## Quick check

1. Who should never get Wire Initiator via birthright? → anyone automatically — Wire is request-only
2. What two selector terms gate employee birthright? → `employeeType=Employee` and `inactive=false`
3. Why can’t you put `all-employees` on the business role? → stock **business** type does not support Entitlements — use an **IT** pack + Required Roles
4. Detection without a Required IT pack proves what? → only membership metadata — not live access

## Feedback

Could you explain why birthright needs both an IT and a business role without opening the editor? If birthright assigned but LDAP stayed empty, note whether Required Roles pointed at an IT pack that actually held `all-employees`.

## Navigate

- Previous: [Lesson 215](215-attribute-sync-live.md)
- Next: [Lesson 217](217-joiner-lcm-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)

