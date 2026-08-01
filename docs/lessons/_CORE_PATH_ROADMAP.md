# Core Path — implementation roadmap

Owner posture: ship **Core Path (01–50)** as the entry-level product; specialist tracks (51–110) are opt-in.

---

## Shipped

### Packaging iteration

| Item | Location |
| --- | --- |
| HR naming drift (`userId` / Active-Terminated / `exceptions=LOA`) | `docs/lessons/*`, column map |
| Core Path TOC filter | `learn/build.py`, `academy.js` |
| Mid-capstones 16 / 34 / 46 | `docs/lessons/mid-*-capstone.md` + specs |
| First 90 Days map | `docs/lessons/first-90-days.md` |

### N+1 — Core realism (**done**)

| ID | Work item | Location |
| --- | --- | --- |
| C1 | Scenarios: rehire, bad-row, batch-hire, contractor-end | `lab-data/scenarios/*` + `apply-*.sh` |
| C2 | Runners taught in JML lessons 29–34 | Joiner/mover/leaver/loa/contractor-end callouts |
| C3 | Day in the life / ticket triage | `08b-day-in-the-life-ticket-triage.md` |
| C4 | Dirty data war room | `19b-dirty-data-war-room.md` |
| C5 | Be the approver | `36b-be-the-approver.md` |
| C6 | Optional Rapid Setup / LCM joiner | `29b-lifecycle-events-rapid-setup.md` |
| C7 | Early Task Result literacy | `16b-reading-task-results.md` |
| C8 | Checkpoint badges + Core TOC polish | `learn/assets/*`, README tracks |

**Exit met:** Nina→Priya→Jordan→Sofia via runners + mid-34; bad-row diagnose refuses upsert; letter-suffix lessons in Academy Core Path.

---

## Iteration N+2 — Live credibility (**next**)

**Goal:** Match Lesson 58 (OpenLDAP) quality for the connectors juniors actually touch first.

| ID | Work item | Acceptance |
| --- | --- | --- |
| L1 | JDBC 63–64 mandatory against `jdbc-pg` / main-stack seed | Live Test Connection + aggregate in lab procedure |
| L2 | LDAP provisioning stretch (group add/remove / disable pattern) | Uses compose provision ACL; evidence in binder |
| L3 | Thin mock SCIM or Web Services container for 68–69 | Primary path not “no tenant”; fallback remains labeled |
| L4 | Bridge page after Capstone 50 (“choose your stack”) | Academy page + README link; TOC default still Core |

**Exit:** Core graduate can complete Directory + JDBC live tracks without a SaaS tenant.

---

## Iteration N+3 — Specialist polish (selective)

| ID | Work item | Acceptance |
| --- | --- | --- |
| S1 | Top 5 SaaS lessons to Lesson-71-grade depth | Real-world setup primary |
| S2 | No niche industry connector expansion | Keep WS/SCIM/JDBC/Logical routing |
| S3 | Rules/workflows after Core grads | 89–96 prereq Capstone 50 |
| S4 | Hardening marked production-engineer | TOC specialist grouping |

---

## Verify / product hardening (parallel)

| ID | Work item | Notes |
| --- | --- | --- |
| V1 | `identity.hasBundle` / entitlement absence checks | Hard “Nina has birthright, no wire” |
| V2 | Progress chip Core-only | Shipped with path filter |
| V3 | Public academy deploy rebuild | CD / `learn/build.py` |
| V4 | Homelab collision policy | Documented in `lab-data/scenarios/README.md` |

---

## Sequencing board

```text
Packaging  → done
N+1        → done (Core realism / ticket-shaped labs)
N+2 (next) → L1–L4 live Directory/JDBC/API mocks + Capstone bridge
N+3        → S1–S4 selective specialist depth
Parallel   → V1, V3–V4
```

---

## References

- Style: [`_STYLE.md`](_STYLE.md)
- Column map: [`../../lab-data/reference/hr-column-map.md`](../../lab-data/reference/hr-column-map.md)
- Scenarios: [`../../lab-data/scenarios/README.md`](../../lab-data/scenarios/README.md)
- Verify: [`../LESSON_VERIFY.md`](../LESSON_VERIFY.md)
- Curriculum: [`README.md`](README.md)
