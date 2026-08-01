# Core Path — implementation roadmap (remaining work)

This plan covers everything **after** the Academy packaging shipped in this iteration (naming drift fixes, Core Path filter, mid-capstones, scenario runners, Core verify asserts, First 90 Days map).

Owner posture: ship **Core Path (01–50)** as the entry-level product; specialist tracks (51–110) are opt-in.

---

## Already shipped (this iteration)

| Item | Location |
| --- | --- |
| HR naming drift (`userId` / Active-Terminated / `exceptions=LOA`) | `docs/lessons/*`, `lab-data/connectors/ad/iqservice-checklist.md` |
| Core Path TOC filter | `learn/build.py`, `learn/assets/academy.js` |
| Mid-capstones 16 / 34 / 46 | `docs/lessons/mid-*-capstone.md` + `tools/iiq-verify/lesson-specs/mid-*.json` |
| Scenario runners | `tools/lab/scripts/scenarios/apply-*.sh` |
| Core persona verifies (incl. Lesson 29 / mid-34) | `tools/iiq-verify/lesson-specs/` + `generate_lesson_specs.py` |
| First 90 Days map | `docs/lessons/first-90-days.md` |

---

## Iteration N+1 — Core realism (highest ROI)

**Goal:** One continuous Meridian story; ticket-shaped labs; fewer fragile file edits.

| ID | Work item | Acceptance |
| --- | --- | --- |
| C1 | Expand scenarios: rehire, bad HR row, batch hire day, contractor end-date | New CSVs under `lab-data/scenarios/` + runner aliases |
| C2 | Teach runners inside Lessons 29–34 (replace hand-append prose) | Each JML lesson Task 2 calls `apply-*.sh` |
| C3 | New early lesson: **Day in the life / ticket triage** (~08b) | Unlock, failed agg, “no access” diagnosis; verify soft checks |
| C4 | New lesson: **Dirty data war room** (~19b) | Uncorrelated + orphan as one incident narrative |
| C5 | New lesson: **Be the approver** (~36b) | Login as manager / workgroup; approve/reject/escalate |
| C6 | Optional Rapid Setup / Lifecycle Event joiner (~29b) | File-insert remains primary; LCM as stretch with clear license note |
| C7 | Move “read Task Result / ProvisioningPlan” skill earlier (slice of 47) | Short Core lesson or Lesson 16/17 appendix |
| C8 | Mid-capstone UX: show checkpoints in Core TOC with badge | Already linked; polish card copy + progress counting |

**Exit:** New hire can demo Nina→Priya→Jordan→Sofia with runners + mid-34 PASS without editing CSV by hand.

---

## Iteration N+2 — Live credibility

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

**Goal:** Depth over catalog breadth.

| ID | Work item | Acceptance |
| --- | --- | --- |
| S1 | Pick top 5 SaaS lessons (e.g. SFDC, SNOW, Okta, M365, AWS) for Lesson-71-grade depth | Real-world setup primary; fallback clearly secondary |
| S2 | Do **not** expand niche industry connectors | README already routes Epic/etc. to WS/SCIM/JDBC/Logical |
| S3 | Rules/workflows track only after Core grads exist | 89–96 prerequisites call out Capstone 50 |
| S4 | Hardening 104–110 marked “production engineer,” not entry path | TOC specialist grouping |

---

## Verify / product hardening (parallel)

| ID | Work item | Notes |
| --- | --- | --- |
| V1 | `identity.hasBundle` / entitlement absence checks | Needed for hard “Nina has birthright, no wire” (today: exists + soft notes) |
| V2 | Progress chip counts Core-only when filter=Core | `progress.js` |
| V3 | Public academy deploy picks up mid-* + first-90-days | `learn/build.py` already emits; CD rebuild |
| V4 | Homelab shared-lab collision policy for scenarios | Document: runners + restore from `.bak-*` |

---

## Explicit non-goals (near term)

- Inflating past 110 lessons without Core Path UX
- Making Salesforce/Workday/SAP live-tenant mandatory for entry-level completion
- Treating “finished 01–110” as the junior success metric

---

## Suggested sequencing board

```text
Now (done)     → packaging + drift + runners + mid-caps + 90-day map
N+1 (next)     → C1–C8 Core realism / missing Core lessons
N+2            → L1–L4 live Directory/JDBC/API mocks + Capstone bridge
N+3            → S1–S4 selective specialist depth
Parallel       → V1–V4 verify/product
```

---

## References

- Style: [`_STYLE.md`](_STYLE.md)
- Column map: [`../../lab-data/reference/hr-column-map.md`](../../lab-data/reference/hr-column-map.md)
- Verify: [`../LESSON_VERIFY.md`](../LESSON_VERIFY.md)
- Curriculum index: [`README.md`](README.md)
