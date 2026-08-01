# Mid-capstone — Apps track checkpoint (after Lesson 16)

**Level:** Intermediate  
**Track:** Core Path · Mid-capstone  
**Time:** 20–30 minutes  
**Prereq:** Lessons 01–16  
**Path:** Core (01–50)

---

## Learning objectives

You will be able to:

- Prove Meridian’s file-app inventory exists end-to-end (HR + IT + banking apps)
- Confirm the workforce cube floor is populated (≥50 identities)
- Run a single **Verify now** bundle instead of re-checking each app lesson by hand

---

## Why this matters

After Lesson 16 you have the bank’s *inventory layer*. Before correlation and roles, pause and prove the foundation — examiners and hiring managers ask “what apps are governed?” not “did you finish a tutorial.”

---

## Before you start

- [ ] Lessons 09–16 objects built in IIQ (`MNB-HR`, `MNB-IT-Access`, core/SAP/AWS/wire/directory/CRM family as taught)
- [ ] `~/iiq-lab-data/` seeded from `lab-data/`
- [ ] Academy up (`./tools/lab/docker/up.sh` or `./tools/lab/up.sh`)

---

## Lab procedure

### Task 1 — Spot-check the inventory

1. In IIQ, confirm Applications exist: `MNB-HR`, `MNB-IT-Access`, `MNB-CoreBanking` (plus any Lesson 12–15 apps you completed).
2. Confirm Identity Warehouse shows a populated workforce (dozens of cubes).
3. Confirm `Refresh MNB Attributes` (or your Lesson 06/16 refresh task) exists.

### Task 2 — Live verify bundle

1. On this page, click **Verify now** (or CLI: `./tools/iiq-verify/verify-lesson.sh mid-16-apps-capstone`).
2. Capture PASS evidence in your binder.

**Expected result:** All hard checks PASS. Soft fails (optional apps) may WARN — document equivalents.

---

## Acceptance criteria

- [ ] Mid-16 verify PASS (or gaps explained with remediation tickets)
- [ ] Binder note: “Apps track closed — ready for correlation (Lesson 17)”

---

## Summary

- Checkpoint after multi-app aggregation strategy
- Unlocks Core Path progression into correlation / roles / JML with confidence

**Previous:** [Lesson 16 — Multi-App Aggregation Strategy](16-multi-app-aggregation-strategy.md)  
**Next:** [Lesson 16b — Reading Task Results](16b-reading-task-results.md) · [Lesson 17 — Account Correlation Basics](17-correlation-basics.md)
