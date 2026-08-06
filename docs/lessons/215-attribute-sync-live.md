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
  → Attribute Sync mapping → provisioning plan
  → LDAP MODIFY
  → ldapsearch confirms     (Mailpit: silent — no approval)
```

- **Wrong way:** Trusting the cube’s own attribute as proof of sync — that’s just promoted HR data. Only the *target* account changing proves provisioning fired.

## Intent

- Trigger a live HR attribute change through the HCM mock (not a file edit).
- Confirm (or wire) attribute sync from identity `department`/`title` to OpenLDAP.
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

### Task 4 — Confirm attribute sync mapping

Confirm (or configure) attribute sync from the identity’s `department` / `title` to `MNB-OpenLDAP`’s `departmentNumber` / `title` — Application provisioning policy or global Attribute Sync mapping, depending on your build’s menu layout.

- **Why:** without a mapping, refresh can compute a plan that never touches LDAP.
- **Expect:** a mapping exists linking identity attribute → target account attribute.

### Task 5 — Refresh with provisioning enabled

Re-run Identity Refresh with provisioning enabled so the sync plan *executes*, not just computes.

- **Why:** preview-only refresh is a common false “it worked” — the cube looks right, LDAP never moved.
- **Expect:** Task Result shows a provisioning plan against `MNB-OpenLDAP`.

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
| Cube new, LDAP unchanged | Sync mapping missing, or refresh ran preview-only (no provisioning) |
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
3. What two refresh options does this lesson depend on? → attribute promotion, then provisioning

## Feedback

Could you re-run mover → agg → promote → provision → `ldapsearch` from memory? If LDAP stayed stale, note whether the refresh Task Result actually listed an OpenLDAP plan — missing mapping vs preview-only are different failures.

## Navigate

- Previous: [Lesson 214](214-correlation-standard-live.md)
- Next: [Lesson 216](216-birthright-roles-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
