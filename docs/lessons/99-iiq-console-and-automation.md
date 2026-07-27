# Lesson 99 — IIQ Console & Automation

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Plugins, APIs & SSD |
| **Time** | 60–75 minutes |
| **Prereq** | [Lesson 98 — Build Meridian Toolkit Plugin](98-build-meridian-toolkit-plugin.md) |
| **Lab data** | `lab-data/` XML under `config/` patterns; [LOCAL_SETUP.md](../LOCAL_SETUP.md); [docs/SSD.md](../SSD.md) |

## Learning objectives

You will be able to:

- Launch `iiq console` against the lab IIQ home and authenticate safely
- Run read-only commands: object list/get, task list, rule list
- Import a small Meridian XML object with `import` / explain `importdynamic`
- Script a repeatable console session file for lab hygiene (no passwords in git)
- State when console is appropriate vs UI vs REST/SCIM

## Why this matters

Console is the operator crowbar for imports, bulk fixes, and CI `importdynamic`. Misused, it bypasses approvals and leaves no human work-item trail. Used well, it makes Meridian labs and promotions reproducible.

**Control / audit:** Production console access is break-glass. Every import must map to a change ticket; credentials never land in committed scripts.

## Concepts

| Mechanism | Best for | Audit note |
| --- | --- | --- |
| UI | Day-2 ops, certifications, approvals | Human decisions |
| `iiq console` | Import XML, run tasks, debug objects | Log commands + ticket |
| REST / SCIM (Lesson 100) | External integrations | API accounts + scopes |
| SSB `./build.sh importdynamic` | Env promotion of `config/` | Pipeline evidence |

```text
  ./iiq console
       |
       +-- authenticate (prompt / env—never commit password)
       |
       +-- list Identity
       +-- get Identity helen.ross
       +-- import /path/to/MNB-Object.xml
       +-- run Task "Refresh MNB Identities"
       +-- quit
```

**Common commands** (names vary slightly by version—use `help` in console):

| Command | Purpose |
| --- | --- |
| `help` | List commands |
| `list <Type>` | List objects |
| `get <Type> <name>` | Dump object |
| `import <file>` | Import XML |
| `run <TaskName>` | Launch task |
| `rule <name>` … | Rule utilities (version-specific) |

**Meridian rule:** Console scripts live under `tools/lab/` or operator home with `chmod 600`; passwords via env vars or secret store—not argv history if avoidable.

## Before you start

- [ ] IIQ installed; know `IIQ_HOME` / Tomcat webapp path from LOCAL_SETUP
- [ ] `spadmin` password available in local vault
- [ ] Shell access to the host/container running IIQ
- [ ] A harmless XML ready (export of a workgroup or rule stub)
- [ ] [docs/SSD.md](../SSD.md) everyday commands skimmed

## Lab procedure

### Task 1 — Open console

1. `cd` to the IdentityIQ installation `WEB-INF/bin` (or project wrapper documented in LOCAL_SETUP).
2. Run `./iiq console` (Windows: `iiq.bat console`).
3. Authenticate when prompted as `spadmin`.
4. Run `help` and capture the command list to your binder (screenshot or paste).

**Expected result:** Console prompt ready; `help` output saved.

**If it fails:** Check `IIQ_HOME`, Java, and that the DB is reachable; read catalina/iiq logs.

### Task 2 — Read-only object inspection

1. `list Workgroup` (or `list Identity`) and find `MNB-WG-IAM-Ops` if present.
2. `get Identity helen.ross` (or `get Workgroup MNB-WG-IAM-Ops`).
3. Confirm attributes match UI without changing anything.
4. `list Task` and identify aggregation/refresh tasks for Meridian apps.

**Expected result:** Read-only dumps proving console sees the same objects as UI.

**If it fails:** Object name case-sensitive—copy exact name from UI.

### Task 3 — Export then re-import hygiene object

1. From UI Debug, export a low-risk object (e.g., Population or Workgroup) to `~/iiq-lab-data/console/MNB-Console-Roundtrip.xml`.
2. Make a trivial description change in the XML (comment in binder what you changed).
3. In console: `import ~/iiq-lab-data/console/MNB-Console-Roundtrip.xml`.
4. Re-`get` the object and confirm the change.

**Expected result:** Successful round-trip import with before/after note.

**If it fails:** XML doctype/DTD issues—export again from Debug; ensure single root `<sailpoint>` wrapper if required.

### Task 4 — Run a known task

1. From console, `run` a short Meridian task (e.g., identity refresh or a small aggregation)—prefer off-peak lab.
2. In UI, open **Task Results** and confirm success counters.
3. Record task name, start time, result ID.

**Expected result:** Task Result success tied to console kickoff.

**If it fails:** Use UI Run once to confirm task health, then retry console with exact task name.

### Task 5 — Script file without secrets

1. Create `~/iiq-lab-data/console/mnb-smoke.console` with only safe commands:

```text
list Application
list Task
quit
```

2. Document how your IIQ version accepts scripted input (redirect / `-c` / source)—run if supported.
3. Add README note: “Password via operator prompt or CI secret—never in this file.”

**Expected result:** Script file + execution notes; zero passwords in file.

### Task 6 — Map to SSB importdynamic

1. Read SSD.md section on `./build.sh importdynamic`.
2. Write the Meridian promotion rule: developers commit XML to `config/`; CI/console importdynamic applies; humans do not “click import” in prod without ticket.
3. Note difference: console ad-hoc vs pipeline-controlled import.

**Expected result:** One paragraph in binder linking console to SSB discipline (Lesson 101).

## Acceptance criteria

- [ ] Console `help` captured
- [ ] Read-only `get`/`list` for at least one Meridian object
- [ ] XML import round-trip succeeded
- [ ] One task run from console with Task Result evidence
- [ ] Script file exists with no secrets
- [ ] importdynamic relationship documented

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Auth fail | Wrong password / locked | Reset via documented lab procedure |
| import error | Malformed XML | Re-export; validate wrapper |
| run unknown task | Name mismatch | `list Task`; copy exact name |
| Console hangs | DB lock / long task | Check Task Results; avoid dual runs |
| History leaked password | Typed in shell wrapper | Rotate password; use prompt-only |

## Training binder evidence

- `help` output  
- `get` excerpt (PII-minimized)  
- Import before/after note  
- Task Result screenshot  
- `mnb-smoke.console` path  

## Knowledge check

1. When should console be used instead of UI?
2. Why are passwords forbidden in committed console scripts?
3. What SSB target command imports `config/` XML in bulk?
4. Name two safe read-only console commands.
5. Who is the break-glass console identity in lab?

### Answers

1. Bulk import, automation, CI, recovery—not routine approvals/certs.  
2. Git and CI logs leak; rotation fails; violates bank secret standards.  
3. `./build.sh importdynamic` (with SPTARGET).  
4. `list`, `get`, `help` (and similar inspect commands).  
5. `spadmin` (lab); production should use named break-glass with logging (Lesson 109).

## Stretch lab

Write a console checklist that exports all `MNB-WG-*` workgroups to dated files under `~/iiq-lab-data/console/exports/YYYY-MM-DD/`.

## Summary

- Console is powerful: inspect, import, run tasks—with ticket discipline.
- Never commit secrets; prefer SSB importdynamic for promotions.
- Prove every console change with Task Results or object `get` evidence.

## Operator safety rules

1. Prefer read-only (`list`/`get`) until change ticket exists.
2. Never paste production passwords into shared terminal recordings.
3. For bulk identity updates, prefer governed workflows over console attribute hacks.
4. After import, run a targeted Identity Refresh only when required—avoid fleet-wide refresh “just in case.”
5. Capture command transcript (redacted) into the change ticket.

### Task 7 — Compare console import vs UI Debug import

1. Import the same small object once via UI Debug import and once via console (use a disposable description toggle).
2. Note differences in logging, error messages, and speed.
3. Decide Meridian standard: CI/`importdynamic` for promotions; console for break-glass recovery; UI for prototypes only.

**Expected result:** Decision note in binder with preferred path per scenario.

### Sample smoke transcript (redacted)

```text
> list Application
... MNB-HR ...
> get Application MNB-HR
... type=...
> quit
```

Store under `~/iiq-lab-data/console/transcripts/YYYY-MM-DD-smoke.txt` with mode `600`.

---

**Previous:** [Lesson 98 — Build Meridian Toolkit Plugin](98-build-meridian-toolkit-plugin.md)  
**Next:** [Lesson 100 — IIQ REST & SCIM APIs](100-iiq-rest-scim-apis.md)
