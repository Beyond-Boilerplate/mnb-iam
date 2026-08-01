# Mid-capstone — JML track checkpoint (after Lesson 34)

**Level:** Intermediate  
**Track:** Core Path · Mid-capstone  
**Time:** 25–40 minutes  
**Prereq:** Lessons 29–34; scenario runners under `tools/lab/scripts/scenarios/`  
**Path:** Core (01–50)

---

## Learning objectives

You will be able to:

- Prove joiner / mover / leaver / LoA personas are represented in IIQ after HR deltas
- Prefer scenario runners over fragile hand-edits of `HRApplications.txt`
- Run one verify bundle covering birthright + lifecycle populations

---

## Why this matters

JML is the control story Meridian sells to examiners. This checkpoint asks: *Can Nina join, Priya move, Jordan leave, and Sofia freeze — with evidence?*

---

## Before you start

- [ ] Birthright role `MNB-Birthright-Employee` exists (Lesson 24)
- [ ] HR file at `~/iiq-lab-data/HRApplications.txt`
- [ ] Scenario deltas under `lab-data/scenarios/`

---

## Lab procedure

### Task 1 — Apply scenarios with runners (not hand surgery)

```bash
./tools/lab/scripts/scenarios/apply-joiner.sh
./tools/lab/scripts/scenarios/apply-mover.sh
./tools/lab/scripts/scenarios/apply-leaver.sh
./tools/lab/scripts/scenarios/apply-loa.sh   # or apply-on-leave.sh
# Optional stress (stretch):
# ./tools/lab/scripts/scenarios/apply-batch-hire.sh
# ./tools/lab/scripts/scenarios/apply-rehire.sh
# ./tools/lab/scripts/scenarios/apply-contractor-end.sh
```

Then Aggregate **MNB-HR** and run **Refresh MNB Attributes** / Managers / Roles as your lab split tasks require. See [`lab-data/scenarios/README.md`](../../lab-data/scenarios/README.md).

### Task 2 — Persona spot-check

| Persona | Expect |
| --- | --- |
| `nina.joiner` | Cube exists; birthright intent; **no** wire/cloud privileged packs |
| `priya.wire` | Job/dept reflects mover delta (RM01 / Commercial) |
| `jordan.reed` | Inactive / terminated signals |
| `sofia.torres` | `exceptions=LOA`, still Active (not terminated) |

### Task 3 — Live verify bundle

**Verify now** or:

```bash
./tools/iiq-verify/verify-lesson.sh mid-34-jml-capstone
```

---

## Acceptance criteria

- [ ] Mid-34 verify PASS (identity soft-fails only if you intentionally skipped a scenario)
- [ ] Binder screenshots for Nina + Jordan + Sofia contrast

---

## Summary

- Lifecycle track closed with runner-backed HR deltas
- Ready for requests / SoD / certifications

**Previous:** [Lesson 34 — Rapid Offboarding Drill](34-rapid-offboarding-drill.md)  
**Next:** [Lesson 35 — Access Request Catalog](35-access-request-catalog.md)
