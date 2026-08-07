# Lesson 215 — Attribute Sync on Live Targets

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 214  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 20 / 22

> **Why:** An HR title/department change is worthless if it never reaches the directories people authenticate against. Silent sync also has to prove it stayed silent — no approval, no mail — or you can’t tell it apart from an access-changing event.

## What this is

Attribute sync is provisioning’s mirror of aggregation: IIQ pushes an identity attribute change *out* to a target account.

Here that means an HCM mover event:

```text
PATCH /hcm/v1/workers/{id}  (department / title)
  → Aggregate MNB-Workday → promote on cube
  → Attribute Sync → LDAP MODIFY
  → ldapsearch confirms
```

…should land as a real LDAP change on Helen’s `MNB-OpenLDAP` account. Classic 20/22 taught the mapping; this lesson makes you watch it cross the wire with `ldapsearch`, not trust IIQ’s UI alone.

## Know these

| Step | What moves | Where it’s provable |
| --- | --- | --- |
| Aggregate | HR value → account link | Application Account tab |
| Refresh + promote | Link value → identity cube | Identity attribute |
| Attribute Sync + provision | Cube value → target account | `ldapsearch` on OpenLDAP |

```text
HCM PATCH department/title
  → Aggregate MNB-Workday
  → cube attribute promote
  → Attribute Target (Identity Mapping) → provisioning plan
  → Update policy Field scripts supply values
  → LDAP MODIFY
  → ldapsearch confirms     (Mailpit: silent — no approval)
```

| Direction | Identity Mapping term | Meaning |
| --- | --- | --- |
| **In** | Attribute **Source** | App account attr → cube (promotion) |
| **Out** | Attribute **Target** | Cube attr → app account attr (this lesson) |

- **Wrong way:** Trusting the cube’s own attribute as proof of sync — that’s just promoted HR data. Only the *target* account changing proves provisioning fired.
- **Wrong way:** Pointing Identity Mapping **Sources** at `MNB-OpenLDAP` for `department`/`title`. Refresh will pull LDAP’s *old* values back onto the cube and never push HR outbound. Sources for these attrs belong on **`MNB-Workday`** (or stay empty if Workday already promotes them); **Targets** point at OpenLDAP.

## Intent

- Trigger a live HR attribute change through the HCM mock (not a file edit).
- Wire Identity Mapping **Attribute Targets** (and Update policy Field scripts) from identity `department`/`title` to OpenLDAP.
- Prove the change with raw `ldapsearch`.
- Confirm Mailpit stayed silent for this change.

## Before you start

- [ ] Lesson 214 correlation clean for Helen (`MNB00001`)
- [ ] `ldapsearch` available on your host
- [ ] Mailpit UI: [http://localhost:8025](http://localhost:8025)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/215
```

## Do this

### Task 1 — Trigger a mover in live HCM

```bash
./tools/lab/enterprise/hcm-scenario.sh mover MNB00001 \
  'Technology Platforms' 'VP, Identity Engineering'
```

- **Why:** production movers arrive as HR API events — not hand-edited CSVs.
- **Expect:** script prints updated worker JSON with the new department/title.

### Task 2 — Confirm the source outside IIQ

```bash
curl -s http://localhost:8091/hcm/v1/workers/MNB00001 \
  | python3 -m json.tool | grep -E 'department|title'
```

Save output under `~/iiq-lab-evidence/sandbox/215/`.

- **Why:** ground truth before IIQ touches anything — if HCM is wrong, aggregation can only amplify it.
- **Expect:** new department and title present at the API.

### Task 3 — Aggregate Workday and promote attributes

1. Run **Account Aggregation** on `MNB-Workday`
2. Run **Identity Refresh** with attribute promotion

- **Why:** aggregation updates the account link; promotion moves the value onto the identity cube.
- **Expect:** Helen’s cube `department` / `title` match the new HCM values.

### Task 4 — Wire outbound Attribute Targets (+ Update policy values)

Two pieces work together. The **Target** decides *whether* Refresh builds an OpenLDAP MODIFY; the **Update policy** decides *which values* go on that plan. An Update form alone never “triggers” itself.

#### 4a — Identity Mapping Attribute Targets (required)

1. Open **Global Settings → Identity Mapping** (or ObjectConfig **Identity**).
2. Edit identity attributes `department` and `title` (add them if missing).
3. For each, add an **Attribute Target** (not Source):

   | Identity attr | Target application | Target attribute |
   | --- | --- | --- |
   | `department` | `MNB-OpenLDAP` | `departmentNumber` |
   | `title` | `MNB-OpenLDAP` | `title` |

4. If either attribute already has an Attribute **Source** on `MNB-OpenLDAP`, remove it (or retarget the Source to `MNB-Workday`). LDAP-as-source overwrites the cube with directory values and blocks this lesson.

- **Why:** Refresh “synchronize attributes” compares cube vs account using Targets. Zero Targets → zero OpenLDAP plan → Update policy never runs.
- **Expect:** both attributes show Targets to `MNB-OpenLDAP`; Sources (if any) are Workday / HR — not OpenLDAP.

#### 4b — Update provisioning policy Field scripts (value supply)

1. Application **MNB-OpenLDAP** → **Configuration** → Provisioning Policy → **Update** (account) → **Edit Policy**.
2. Landing on the **policy form** is expected — that form *is* the mapping UI.
3. Ensure fields `departmentNumber` and `title` exist.
4. Open each field → scroll past **Settings** (`Hidden` / `Read Only` / `Hide Nulls` are display flags only) → **Value Settings**.
5. Set **Value** = **Script**:

```java
return identity.getAttribute("department");
```

```java
return identity.getAttribute("title");
```

6. **Apply** each field → **Save** the form → **Save** the application.
7. Delete any empty/broken Update form that has sections named `departmentNumber`/`title` but no Field scripts — keep one clean Update form.

- **Why:** Targets create the plan; Field scripts tell the connector what to write. Blank Value Settings → MODIFY with nothing useful.
- **Expect:** Update form fields bind cube `department`/`title` → LDAP `departmentNumber`/`title`.

### Task 5 — Refresh with sync + provisioning enabled

Re-run Identity Refresh with **synchronize attributes** (or equivalent) **and** provisioning enabled so the Target-driven plan *executes*, not just computes.

- **Why:** preview-only refresh is a common false “it worked” — the cube looks right, LDAP never moved. Targets without provision also leave LDAP stale.
- **Expect:** Task Result shows a provisioning plan / transaction against `MNB-OpenLDAP`.

### Task 6 — Prove LDAP changed with ldapsearch

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b ou=people,dc=meridiannb,dc=com \
  -D cn=admin,dc=meridiannb,dc=com -w admin \
  '(uid=helen.ross)' departmentNumber title
```

- **Why:** IIQ UI showing the right value could be the cube’s promoted attribute with no provisioning behind it.
- **Expect:** output shows the new department/title from Task 1 — the real proof.

Save the `ldapsearch` output under evidence.

### Task 7 — Confirm Mailpit silence

Open [http://localhost:8025](http://localhost:8025) and confirm no new message ties to this department/title change.

- **Why:** attribute sync of non-access attributes has no approval — silence is the correct control behavior.
- **Expect:** no mail for this change.

## If it fails

| Symptom | Fix |
| --- | --- |
| `hcm-scenario.sh mover` usage error | Form is `mover <username\|workerId> <newDepartment> [newTitle]`; quote departments with spaces |
| HCM new, cube old after refresh | Aggregated but skipped promotion — or agg only touched the link |
| Cube snapped back to old LDAP values (`SEC`, old title) | Identity Mapping **Source** points at `MNB-OpenLDAP` — remove it; Source should be Workday (or none). Re-agg Workday + promote (re-run mover only if HCM was overwritten) |
| Cube new, LDAP unchanged; **no** OpenLDAP plan / 0 provisioning txns | Missing **Attribute Targets**, or refresh lacked synchronize attributes + provisioning. Update policy alone does not fire |
| Plan exists but attrs blank / LDAP unchanged | Update form Field **Value Settings** missing scripts; or a second empty Update form is winning |
| Form editor **Settings** has no mapping | Scroll to **Value Settings** → Script (Settings is only Hidden / Read Only / Hide Nulls) |
| `ldapsearch` still shows old values | Stale terminal scrollback — re-run the exact command fresh |
| Unexpected Mailpit mail | An `IdentityTrigger` scoped to `attributeChange` may be matching broader than intended |

## You are done when

- [ ] Live HCM `PATCH` for Helen’s department/title landed in HCM curl output
- [ ] Cube attributes match after aggregate + promote
- [ ] `ldapsearch` shows the new values on OpenLDAP
- [ ] Mailpit silent for that change

## Control note

- **Control:** HR-to-directory attribute sync (data quality, not access)
- **Owner:** HR Ops (source) + IAM Ops (mapping)
- **SLA (lab):** same refresh cycle; production often nightly or near-real-time feed
- **Evidence:** `~/iiq-lab-evidence/sandbox/215/` — HCM curl, `ldapsearch` before/after, Mailpit silence note

## Quick check

1. Why isn’t cube-level attribute value proof enough? → it’s promoted HR data, not confirmation provisioning fired
2. What should Mailpit show for a pure attribute sync? → nothing — silent, no-approval
3. What two refresh options does this lesson depend on? → attribute promotion, then synchronize attributes + provisioning
4. Source vs Target — which one pushes cube → OpenLDAP? → Attribute **Target**
5. Why doesn’t the Update provisioning policy “trigger” by itself? → it only supplies values once Targets + refresh build a MODIFY plan

## Feedback

Could you re-run mover → Workday agg → promote → confirm Targets → refresh with sync+provision → `ldapsearch` from memory? If LDAP stayed stale, note whether the Task Result listed an OpenLDAP plan — missing Targets vs preview-only vs Source-from-LDAP are different failures.

## Navigate

- Previous: [Lesson 214](214-correlation-standard-live.md)
- Next: [Lesson 216](216-birthright-roles-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
