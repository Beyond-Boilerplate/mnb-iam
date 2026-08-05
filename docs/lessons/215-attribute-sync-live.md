# Lesson 215 — Attribute Sync on Live Targets

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 214  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 20 / 22

> **Why (1–2 lines):** An HR title/department change is worthless if it never reaches the directories people actually authenticate against. Silent sync also has to prove it stayed silent — no approval, no mail — or you can't tell it apart from an access-changing event.

## What this is

Attribute sync is provisioning's mirror of aggregation: instead of pulling data *from* a target into IIQ, IIQ pushes an identity attribute change *out* to a target account. Here that means an HCM mover event (`PATCH /hcm/v1/workers/{id}` on `department`/`title`) should, after aggregate + refresh with attribute sync enabled, land as a real LDAP `MODIFY` on Helen's `MNB-OpenLDAP` account. Classic 20/22 taught the mapping concept; this lesson makes you watch it cross the wire with `ldapsearch`, not trust IIQ's own UI.

## Know these

```text
HCM PATCH department/title → Aggregate MNB-Workday → cube attribute promote
  → Attribute Sync mapping → provisioning plan → LDAP MODIFY
  → ldapsearch confirms                    (Mailpit: silent — no approval)
```

| Step | What moves | Where it's provable |
| --- | --- | --- |
| Aggregate | HR value → account link | Application Account tab |
| Refresh + promote | Link value → identity cube | Identity attribute |
| Attribute Sync + provision | Cube value → target account | `ldapsearch` on `MNB-OpenLDAP` |

**Wrong way:** Trusting the identity cube's own attribute as proof of sync — that's just promoted HR data; only the target account changing proves provisioning fired.

## Intent

- Trigger a live HR attribute change through the HCM mock, not a file edit.
- Confirm (or wire) attribute sync from `MNB-Workday` to `MNB-OpenLDAP` for `department`/`title`.
- Prove the change landed in the directory with a raw `ldapsearch`.
- Confirm attribute sync stayed silent in Mailpit — no approval, no notification.

## Before you start

- [ ] Lesson 214 correlation clean for Helen (`MNB00001`)
- [ ] `ldapsearch` CLI available on your host
- [ ] Mailpit UI reachable: `http://localhost:8025`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/215`

## Do this

1. Trigger a mover for Helen via live HCM: `./tools/lab/enterprise/hcm-scenario.sh mover MNB00001 'Technology Platforms' 'VP, Identity Engineering'`.  
   **Expect:** Script prints updated worker JSON with new department/title.

2. Confirm the source independent of IIQ: `curl -s http://localhost:8091/hcm/v1/workers/MNB00001 | python3 -m json.tool | grep -E 'department|title'`.  
   **Expect:** New values present at HCM, before IIQ touches anything.

3. Run **Account Aggregation** on `MNB-Workday`, then **Identity Refresh** with attribute promotion.  
   **Why:** Aggregation only updates the account link; promotion is what moves the value onto the identity cube.  
   **Expect:** Helen's cube `department`/`title` match the new HCM values.

4. Confirm (or configure) attribute sync from the identity's `department`/`title` to `MNB-OpenLDAP`'s `departmentNumber`/`title` — an Application provisioning policy or global Attribute Sync mapping depending on your build's menu layout.  
   **Expect:** A mapping exists linking identity attribute → target account attribute.

5. Re-run Identity Refresh with provisioning enabled so the sync plan executes, not just computes.  
   **Expect:** Task Result shows a provisioning plan against `MNB-OpenLDAP`.

6. Confirm the directory itself changed: `ldapsearch -x -H ldap://localhost:389 -b ou=people,dc=meridiannb,dc=com -D cn=admin,dc=meridiannb,dc=com -w admin '(uid=helen.ross)' departmentNumber title`.  
   **Why:** IIQ's UI showing the right value could just be the cube's own promoted attribute with no provisioning behind it.  
   **Expect:** Output shows the new department/title from step 1 — the real proof.

7. Check Mailpit (`http://localhost:8025/`) and confirm no new message ties to this change.  
   **Expect:** Silence — attribute sync of department/title has no approval, so it shouldn't notify.

## If it fails

- **`hcm-scenario.sh mover` errors** — usage is `mover <username|workerId> <newDepartment> [newTitle]`; quote department strings with spaces.
- **HCM shows new value, cube doesn't after refresh** — you aggregated but skipped promotion, or aggregation alone touched only the link, not the cube.
- **Cube shows new value, LDAP never changes** — sync mapping isn't wired, or refresh ran preview-only (no provisioning).
- **LDAP changed but `ldapsearch` still shows old values** — stale terminal history; re-run the exact command fresh.
- **Mailpit shows unexpected mail** — an `IdentityTrigger` scoped to `attributeChange` (like Lesson 219's leaver trigger) is likely matching broader than intended.

## You are done when

A live HCM `PATCH` for Helen's department/title round-trips through aggregate → refresh → attribute sync into an `ldapsearch`-visible change on `MNB-OpenLDAP`, with Mailpit silent for that change.

## Control note

- **Control:** HR-to-directory attribute sync (data quality, not access).  
- **Owner:** HR Ops (source) + IAM Ops (mapping).  
- **SLA (lab):** Same refresh cycle; production often nightly or near-real-time feed.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/215/` — HCM curl output, `ldapsearch` before/after, Mailpit silence note.

## Quick check

1. Why isn't cube-level attribute value proof enough? → It's promoted HR data, not confirmation provisioning fired.  
2. What should Mailpit show for a pure attribute sync? → Nothing — it's silent, no-approval.  
3. What two refresh options does this lesson depend on? → Attribute promotion, then provisioning.

## Navigate

- Previous: Lesson 214  
- Next: Lesson 216  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
