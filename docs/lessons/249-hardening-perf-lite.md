# Lesson 249 — Hardening & Perf Lite

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lessons 206, 233  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 105–109

> **Why:** Sandbox still teaches production muscles: least privilege and task hygiene. Capability sprawl and unpartitioned heavy tasks are exactly what a pre-production review would flag before sign-off.

## What this is

A capstone-ready estate accumulates cruft across 48 lessons: test capabilities you granted yourself and forgot to remove (245), heavy aggregation tasks running unpartitioned (233's runbook), and demo habits like logging in as `spadmin` for things a scoped persona should do. This lesson is a deliberate cleanup pass checking capability sprawl, task performance settings, and credential hygiene across everything you've built.

## Know these

| Check | What "clean" looks like |
| --- | --- |
| Capability sprawl | Every capability on a persona traces to a specific lesson requirement |
| Task partitioning | Enabled where dataset size justifies it, or a written reason why not |
| Schedule contention | No two heavy tasks firing at the same cron time |
| Credential hygiene | No demo relied on `spadmin` where a scoped persona should have been used |

**Wrong way:** Leaving a capability granted "just for debugging one time" — direct grants stack silently and don't get cleaned up by workgroup removal (245).

## Intent

- Audit and strip any capability granted to a persona beyond what their role actually needs.
- Turn on partitioning for the heaviest aggregation task, or write down why not.
- Review Task Results for long-running jobs and adjust schedules to avoid overlap/contention.
- Confirm no lesson demo relied on `spadmin`'s credentials where a scoped persona should have been used.

## Before you start

- [ ] Lesson 245 workgroup/capability model in place
- [ ] Lesson 233 aggregation runbook and heaviest-task identified
- [ ] Access to Task Results history across Lessons 201–248
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/249`

## Do this

1. **Identities → helen.ross → Capabilities**, and every other persona used (`priya.wire`, `marcus.approve`, `christopher.hayes`). List every capability each holds, direct or via workgroup (245).  
   **Expect:** A full inventory per persona.
2. For each capability, ask: did an earlier lesson actually require this? Remove anything you can't justify — e.g. if Priya has `SystemAdministrator` from a debugging session instead of just her `MNB-WG-Wire-Owners` right, strip it.  
   **Expect:** Only lesson-justified capabilities remain.
3. Re-verify Lesson 245's proof still holds: Priya can still certify, still cannot open **Global Settings**.  
   **Expect:** No regression from cleanup.
4. Identify the heaviest aggregation task from 233's runbook (usually `MNB-Workday` or the app with the most accounts). Open its Task Definition, check **Partitioning**.  
   **Expect:** Enable it if supported, or write one sentence why not (e.g. dataset too small to matter, but would past a few thousand accounts).
5. **Monitor → Tasks → Task Results**, sort by duration, find any task that ran unexpectedly long or overlaps another's schedule.  
   **Expect:** Adjust at least one schedule to remove an overlap.
6. Review your evidence notes and screenshots across Lessons 201–248 for any place `spadmin`/`admin` was used in a portal demo, Gitea login, or context where a real persona should have been used. Fix any found by redoing that check as the correct persona.  
   **Expect:** No unjustified `spadmin` usage remains documented.
7. Confirm `spadmin`'s password is still the lab default (`admin`) only inside this local Docker stack.  
   **Expect:** Note in evidence that this must never be true outside a throwaway lab.
8. Write a short least-privilege + task-hygiene note summarizing what you stripped, rescheduled, and fixed.  
   **Expect:** Note saved under evidence.

## If it fails

- **Stripping a capability breaks a persona's expected access** — you found a real dependency; re-add only the minimal capability that lesson needs, and note the correction.
- **Partitioning option greyed out** — some connector types don't support partitioned aggregation; confirm connector docs before assuming misconfiguration.
- **Schedule change causes a task to never run** — double-check cron syntax; an unreachable day/hour combination is the usual mistake.

## You are done when

Every persona's capabilities are traceable to a real lesson requirement, one task's partitioning/schedule decision is made and justified, and your least-privilege/task-hygiene note is saved.

## Control note

- **Control:** Pre-production hardening pass (least privilege + task hygiene).  
- **Owner:** IAM Engineering.  
- **SLA (lab):** Zero unjustified capabilities; heaviest task's partitioning decision documented.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/249/` — capability audit, partitioning note, hygiene note.

## Quick check

1. What must every capability on a persona trace back to? → A specific lesson requirement.  
2. Why check for `spadmin` usage in past demos? → A scoped persona should have been used where one exists — hygiene, not shortcuts.  
3. What's an acceptable reason to skip partitioning? → Dataset too small in this lab to justify the overhead, documented explicitly.

## Navigate

- Previous: Lesson 248
- Next: Lesson 250
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
