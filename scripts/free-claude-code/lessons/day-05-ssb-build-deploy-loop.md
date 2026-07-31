# Day 05 — SSB Build–Deploy–Import Loop

| Field | Value |
| --- | --- |
| **Week** | 1 — Fluency |
| **Time** | 2.5–3 hours |
| **Prereq** | Day 04; lab up |
| **Artifacts** | `artifacts/playbooks/ssb-loop-runbook.md` |

## Learning objectives

You will be able to:

- Narrate and execute `clean war` → `deploy` → `importdynamic` with Claude as co-pilot
- Keep `SPTARGET=sandbox` consistent across a session
- Capture timing and failure modes for each stage
- Produce a runbook a junior can follow under change freeze stress

## IAM pain (today’s tax)

Enterprises re-learn the SSB loop every time someone new joins. Mis-ordered steps (import before deploy of classes; wrong target properties) cause “works on my machine” tickets. Automating the **sequence and checks** removes tribal knowledge.

## Claude concept

Teach Claude a **state machine**, not a pile of commands:

```text
[edit config/src] → build war → deploy to IIQHome → importdynamic → verify
         ↑                                                      |
         └──────────── fix ← evidence on failure ←──────────────┘
```

Refuse to skip verify after mutate.

## Before you start

- [ ] `export SPTARGET=sandbox`
- [ ] Understand CD ships HelloWorld only (`config/PACKS.md`)
- [ ] Optional: have one harmless config touch prepared (comment in a Rule you own, or dry-run without import)

## Lab procedure

### Task 1 — Let Claude teach the loop from repo docs

> Using CLAUDE.md, docs/SSD.md, and config/README.md, write a Meridian SSB loop runbook with preflight checks and verify steps.

Save to artifact; correct any inventiveness.

### Task 2 — Dry-run narration

Ask Claude to walk you through commands **without executing** first. Approve sequence only when ordering is correct.

### Task 3 — Execute with instrumentation

Have Claude run (with your approvals):

```bash
export SPTARGET=sandbox
./build.sh clean war
./build.sh deploy
# importdynamic when you intend to refresh XML objects
./tools/iiq-verify/assert-mnb-objects.sh local
```

Record wall-clock per stage in the runbook.

### Task 4 — Failure table

Add a troubleshooting matrix: missing `base/ga` zip, wrong SPTARGET, Tomcat locked files, token not replaced, ignorefiles excluding your XML.

## Deliverable

`artifacts/playbooks/ssb-loop-runbook.md`

## Acceptance criteria

- [ ] Runbook lists preflight → build → deploy → import → verify in order
- [ ] At least one successful build in this lab
- [ ] Smoke verify run documented (pass or explained fail)
- [ ] Claude did not suggest system `ant` as primary

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Missing GA zip | Follow GHCR/LFS docs in SSD/LOCAL_SETUP |
| Deploy file locks | Stop Tomcat, retry deploy, start |
| Import no-op | Check ignorefiles + naming under `config/` |

## Stretch

- Compare Docker deploy path vs Tomcat `IIQHome`
- Note what CI runs in `.github/workflows/ssb-ci.yml`

## Knowledge check

1. What does `importdynamic` consume?  
2. Why export tokens as `%%NAME%%`?  
3. What gets committed — `build/` or `config/`?

### Answers

1. Token-replaced XML from `config/` (per SSB).  
2. Environment substitution via target properties.  
3. `config/` (+ properties), not `build/` artifacts.

## Navigation

[← Day 04](day-04-lab-health-orchestration.md) · [Day 06 →](day-06-config-xml-hygiene.md)
