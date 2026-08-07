# Day 04 — Lab Health Orchestration

| Field | Value |
| --- | --- |
| **Week** | 1 — Fluency |
| **Time** | 2–3 hours |
| **Prereq** | Day 03; Tomcat or Docker lab |
| **Artifacts** | `artifacts/playbooks/lab-health-checklist.md` |

## Learning objectives

You will be able to:

- Drive a multi-step “is the lab healthy?” prompt without babysitting every click
- Use Claude to triage up/down signals (ports, login page, HelloWorld smoke)
- Encode a reusable health checklist you will later skill-ify (Day 09)
- Distinguish academy vs Docker vs connectors compose stacks

## IAM pain (today’s tax)

Before diagnosis (“why did Aggregate MNB-HR fail?”), engineers lose 20 minutes confirming Tomcat is up, DB accepts connections, and they’re looking at the right environment. Morning stack check is pure friction — perfect automation bait.

## Claude concept

**Orchestrated multi-step prompts** beat fragmentary chat. Give Claude a **definition of healthy** and require a pass/fail table.

```text
Definition of healthy (lab)
  ├─ IIQ login HTTP reachable
  ├─ HelloWorld smoke (CD) OR known lesson objects
  ├─ SPTARGET known (sandbox)
  └─ lab-data paths exist on disk
```

## Before you start

- [ ] Prefer `./tools/lab/up.sh` today (or Docker equivalent)
- [ ] Evidence folder: `mkdir -p ~/iiq-lab-evidence/$(date +%F)`

## Lab procedure

### Task 1 — Write definition of healthy

Draft in the artifact file **before** Claude edits it. Then ask Claude to tighten wording.

### Task 2 — Guided health run

Prompt:

> Run a Meridian lab health check. Use tools. Output a markdown table: Check | Command/Probe | Result | Remediation if fail. Do not run destructive resets unless I approve.

Approve only read/health commands first.

**Expected:** Touches lab scripts, curl/login probe, maybe `assert-mnb-objects.sh`, checks `~/iiq-lab-data`.

### Task 3 — Inject a fault deliberately

Stop Tomcat/containers, re-run the same prompt. Confirm Claude’s remediation is sensible (`./tools/lab/up.sh`, wait, re-probe) — not “reinstall IIQ from scratch.”

Bring lab back up.

### Task 4 — Capture golden checklist

Finalize `artifacts/playbooks/lab-health-checklist.md` so Day 09 can wrap it as a skill verbatim.

Include: Academy URL if used (`localhost:4173`), IIQ URL, verify CLI, connectors compose note (`docker-compose.connectors.yml`).

## Deliverable

`artifacts/playbooks/lab-health-checklist.md`

## Acceptance criteria

- [ ] Healthy run produces a pass table while IIQ is up
- [ ] Fault injection produces actionable remediation (not panic)
- [ ] Checklist is reusable without today’s chat history
- [ ] No High-risk commands executed without explicit approval

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Docker vs Tomcat confusion | Read `docs/LOCAL_SETUP.md`; stick to one stack per week |
| Smoke fails but UI up | HelloWorld not imported — `importdynamic` / CD path |
| Claude wants DB drop | Deny; stick to documented lab up/down |

## Stretch

- Add optional OpenLDAP/Postgres connector health probes
- Time the checklist — target <5 minutes wall clock

## Knowledge check

1. Why separate “UI up” from “objects imported”?  
2. What env var must be consistent across build commands?  
3. Where do screenshots/evidence go?

### Answers

1. Tomcat can serve login with empty/partial config.  
2. `SPTARGET`.  
3. `~/iiq-lab-evidence/YYYY-MM-DD/`.

## Navigation

[← Day 03](day-03-permissions-and-safe-ops.md) · [Day 05 →](day-05-ssb-build-deploy-loop.md)
