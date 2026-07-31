# Day 02 — CLAUDE.md & Repo Memory

| Field | Value |
| --- | --- |
| **Week** | 1 — Fluency |
| **Time** | 2–2.5 hours |
| **Prereq** | Day 01 |
| **Artifacts** | `artifacts/playbooks/claude-md-diff-notes.md` |

## Learning objectives

You will be able to:

- Explain what `CLAUDE.md` is (and is not) relative to chat history
- Run `/init` consciously and compare against this repo’s existing file
- Add **IAM-ops-specific** guidance without bloating every turn
- Use memory / reminders for sticky personal facts (lab paths, evidence folder)
- Measure whether Claude stops inventing wrong workflows

## IAM pain (today’s tax)

Without repo memory, every session Claude invents Maven, Docker-only deploy, or relative CSV paths. Ops waste cycles correcting basics instead of diagnosing correlation or SoD. Banks need **stable operating doctrine** in-repo.

## Claude concept

**Project instructions (`CLAUDE.md`)** load into context for this workspace. Keep them:

- Command-centric (copy-pasteable)
- Explicit about forbidden paths
- Short: link out to `docs/` for depth

**Anti-pattern:** Pasting entire SSD manuals into `CLAUDE.md` — burns context and invites contradiction.

```text
CLAUDE.md (always-on doctrine)
    │
    ├─ docs/* (deep tutorials — load when needed)
    ├─ config/README.md (how to add features)
    └─ your memory (personal lab paths, preferred editor habits)
```

## Before you start

- [ ] Day 01 complete
- [ ] Read root [`CLAUDE.md`](../../../CLAUDE.md) once end-to-end

## Lab procedure

### Task 1 — Baseline probe (before editing)

New Claude session:

> Without opening files: how do I import config XML after changing Application MNB-HR?

Note wrong answers (Maven, `iiq console` only, guessing tokens). Save under “baseline” in your notes.

### Task 2 — Consciousness pass on existing CLAUDE.md

Ask:

> Critique CLAUDE.md for an IAM engineer who lives in aggregation failures and CAB exports. What 5 bullets are missing?

Compare against real gaps: evidence path, `iiq-verify`, naming `MNB-`, never commit `build/`, lab-data absolute paths.

### Task 3 — Propose a minimal additive section

Have Claude draft a **short** section titled `## IAM Ops Daily` covering:

1. Evidence folder convention  
2. Verify commands  
3. Export → tokenize → importdynamic loop  
4. Forbidden: secrets, `base/ga`

**Do not paste novels.** Cap at ~25–40 lines. Save the proposed section to `artifacts/playbooks/claude-md-diff-notes.md`. You may apply it to root `CLAUDE.md` if you own the doc — otherwise keep as artifact only.

### Task 4 — Memory for personal constants

Tell Claude (and/or save memory if your build supports it):

> My lab data lives at ~/iiq-lab-data. Evidence at ~/iiq-lab-evidence/YYYY-MM-DD. I use SPTARGET=sandbox unless I say otherwise.

Re-open a session and ask: “Where should CSV paths point for Delimited File apps?” Expect absolute `~/iiq-lab-data/...` guidance.

### Task 5 — Regression probe

Repeat Task 1. Confirm answers cite `./build.sh importdynamic` and tokens from `*.target.properties`.

## Deliverable

`artifacts/playbooks/claude-md-diff-notes.md` — baseline errors, proposed `IAM Ops Daily` section, before/after probe notes.

## Acceptance criteria

- [ ] Baseline vs after probe shows fewer invented build tools
- [ ] Proposed section is short and operational
- [ ] Personal lab paths recalled correctly in a fresh session
- [ ] You can explain why long paste dumps hurt agents

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `/init` wants to overwrite good CLAUDE.md | Diff only; keep SailPoint SSB truth |
| Claude still suggests relative paths | Strengthen CLAUDE.md + memory; cite Lesson 03 |
| Context feels huge | Move depth to docs links |

## Stretch

- Add a `## When verifying lessons` pointer to `docs/LESSON_VERIFY.md`
- Compare Cursor user rules vs `CLAUDE.md` — write 5 lines on overlap

## Knowledge check

1. What belongs in CLAUDE.md vs docs/lessons?  
2. Why absolute paths for Delimited File?  
3. Name three forbidden behaviors for the agent.

### Answers

1. Always-on commands/guards vs long tutorials.  
2. Tomcat cwd ≠ shell cwd.  
3. Edit `base/ga`, commit secrets, skip verify for “looks fine.”

## Navigation

[← Day 01](day-01-bootstrap-and-mental-model.md) · [Day 03 →](day-03-permissions-and-safe-ops.md)
