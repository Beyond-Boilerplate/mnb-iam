# Lesson 99 — IIQ Console & Automation

**Level:** Intermediate  
**Track:** Plugins, APIs & SSD  
**Time:** 75–90 min  
**Prereq:** Lesson 98 — Build Meridian Toolkit Plugin  

**Lab data:**
- Repo: `config/` XML patterns; [docs/LOCAL_SETUP.md](../LOCAL_SETUP.md); [docs/SSD.md](../SSD.md)
- Lab scripts home: `~/iiq-lab-data/console/`

---

## Learning objectives

You will be able to:

- Launch `iiq console` against lab IIQ home and authenticate safely (no passwords in git)
- Run read-only commands: object `list`/`get`, task list, and interpret `help`
- Import a small Meridian XML object and explain how console relates to SSB `importdynamic`
- Script a repeatable console session file for lab hygiene
- Decide when console is appropriate vs UI vs REST/SCIM — and when it is break-glass only

---

## Why this matters

**Business.** When `helen.ross` needs to re-import `MNB-WG-IAM-Ops` after a bad edit, or CI needs to apply `config/` XML to a fresh sandbox, the **iiq console** is the operator crowbar. Used well, Meridian labs and promotions are reproducible. Used casually, console bypasses approvals and leaves no human work-item trail — the opposite of governance.

**Control / audit.** Production console access is break-glass. Every import must map to a change ticket; credentials never land in committed scripts. Examiners ask *"how do configuration objects enter production?"* The bank answer is SSB/`importdynamic` with a git SHA — console is for recovery and lab automation, not day-2 SoD edits.

---

## Concepts

### Four ways to change IIQ — pick deliberately

| Mechanism | Best for | Audit note |
| --- | --- | --- |
| UI | Day-2 ops, certifications, approvals | Human decisions, work items |
| `iiq console` | Import XML, run tasks, debug objects | Log commands + ticket |
| REST / SCIM (Lesson 100) | External integrations | API accounts + scopes |
| SSB `./build.sh importdynamic` | Env promotion of `config/` | Pipeline evidence + SHA |

The naive approach: “console is faster, so we do everything there.” Under exam, that becomes unreproducible snowflake config and no PR trail. Meridian rule: **prototype in UI → export to `config/` → promote via SSB**; console for import drills, break-glass recovery, and CI wrappers.

### What the console is

`iiq console` is a command-line shell bound to the same IdentityIQ runtime and database as the UI. It authenticates as an IIQ identity (lab: `spadmin`). It can list/get objects, import XML, and launch tasks by exact name. It does **not** replace workflows, certifications, or least-privilege day-2 admin (Lesson 109).

### Operator safety rules

1. Prefer read-only (`list`/`get`) until a change ticket exists.
2. Never paste production passwords into shared terminal recordings.
3. For bulk identity updates, prefer governed workflows over console attribute hacks.
4. After import, run a targeted Identity Refresh only when required — avoid fleet-wide refresh “just in case.”
5. Capture a redacted command transcript into the change ticket.

---

## How it works

```text
  ./iiq console
       │
       ├── authenticate (prompt / env — never commit password)
       │
       ├── list Identity | Workgroup | Application | Task
       ├── get Identity helen.ross
       ├── import /path/to/MNB-Object.xml
       ├── run Task "Refresh MNB Identities"
       └── quit
```

| Command | Purpose | Meridian use |
| --- | --- | --- |
| `help` | List commands | Capture for binder |
| `list <Type>` | List objects | Find `MNB-WG-IAM-Ops` |
| `get <Type> <name>` | Dump object | Verify after import |
| `import <file>` | Import XML | Round-trip drills |
| `run <TaskName>` | Launch task | Controlled lab runs |
| `quit` | Exit | Always end cleanly |

Names vary slightly by version — use `help` in your build. Object names are case-sensitive.

```text
  Ad-hoc console import          SSB importdynamic
  (break-glass / lab)            (promotion standard)
         │                              │
         ▼                              ▼
  ticket + transcript            git SHA + CI log + SPTARGET
```

---

## Real-world setup (automation hygiene)

### Step 1 — Locate IIQ home

1. From [LOCAL_SETUP.md](../LOCAL_SETUP.md), note `IIQ_HOME` / Tomcat webapp path.
2. Console binary lives under `WEB-INF/bin` (`./iiq console` or `iiq.bat console`).
3. Confirm DB is reachable before blaming the console binary.

### Step 2 — Credential handling

1. Lab: `spadmin` password in a local vault / password manager — not in shell history wrappers if avoidable.
2. CI: `console_pass` from the secret store, injected into `*.iiq.properties` at build time ([docs/SSD.md](../SSD.md)).
3. Scripts under `tools/lab/` or `~/iiq-lab-data/console/` with `chmod 600`; **zero passwords in files**.

### Step 3 — Transcript discipline

1. Store transcripts as `~/iiq-lab-data/console/transcripts/YYYY-MM-DD-smoke.txt` mode `600`.
2. Redact any accidental secrets; rotate if leaked.
3. Production: attach redacted transcript to the change/incident ticket.

---

## Before you start

- [ ] IIQ installed; know `IIQ_HOME` from LOCAL_SETUP
- [ ] `spadmin` password available in local vault
- [ ] Shell access to the host/container running IIQ
- [ ] A harmless XML ready (export of a workgroup or rule stub)
- [ ] [docs/SSD.md](../SSD.md) everyday commands skimmed

---

## Lab procedure

### Task 1 — Open console and capture help

You need a known-good prompt before any import. Capturing `help` also proves which command dialect your version speaks.

1. `cd` to IdentityIQ `WEB-INF/bin` (or project wrapper in LOCAL_SETUP).
2. Run `./iiq console` (Windows: `iiq.bat console`).
3. Authenticate when prompted as `spadmin`.
4. Run `help` and capture the command list to your binder.

**Expected result:** Console prompt ready; `help` output saved.

**If it fails:** Check `IIQ_HOME`, Java, and DB connectivity; read catalina/iiq logs.

### Task 2 — Read-only object inspection

Prove console sees the same objects as the UI before you trust it to write.

1. `list Workgroup` (or `list Identity`) and find `MNB-WG-IAM-Ops` if present.
2. `get Identity helen.ross` (or `get Workgroup MNB-WG-IAM-Ops`).
3. Confirm attributes match UI without changing anything.
4. `list Task` and identify aggregation/refresh tasks for Meridian apps.

**Expected result:** Read-only dumps proving console/UI parity.

**If it fails:** Object names are case-sensitive — copy exact name from UI.

### Task 3 — Export then re-import hygiene object

Round-trip is the recovery drill you will need in Lesson 107.

1. From UI Debug, export a low-risk object (Population or Workgroup) to `~/iiq-lab-data/console/MNB-Console-Roundtrip.xml`.
2. Make a trivial description change; note what you changed in the binder.
3. In console: `import ~/iiq-lab-data/console/MNB-Console-Roundtrip.xml`.
4. Re-`get` the object and confirm the change.

**Expected result:** Successful round-trip import with before/after note.

**If it fails:** Re-export from Debug; ensure single root `<sailpoint>` wrapper if required.

### Task 4 — Run a known task

Console can kick off the same tasks as the UI — Task Results remain the audit evidence.

1. From console, `run` a short Meridian task (identity refresh or small aggregation) — prefer off-peak lab.
2. In UI, open **Task Results** and confirm success counters.
3. Record task name, start time, result ID.

**Expected result:** Task Result success tied to console kickoff.

**If it fails:** Use UI Run once to confirm task health, then retry console with exact task name.

### Task 5 — Script file without secrets

Automation without secret hygiene is how passwords land in git.

1. Create `~/iiq-lab-data/console/mnb-smoke.console`:

```text
list Application
list Task
quit
```

2. Document how your IIQ version accepts scripted input (redirect / `-c` / source) and run if supported.
3. Add a README note: “Password via operator prompt or CI secret — never in this file.”

**Expected result:** Script file + execution notes; zero passwords in file.

### Task 6 — Map to SSB importdynamic

1. Read SSD.md section on `./build.sh importdynamic`.
2. Write the Meridian promotion rule: developers commit XML to `config/`; CI/console importdynamic applies; humans do not “click import” in prod without ticket.
3. Note difference: console ad-hoc vs pipeline-controlled import.

**Expected result:** One paragraph linking console to SSB discipline (Lesson 101).

### Task 7 — Compare console import vs UI Debug import

1. Import the same small object once via UI Debug and once via console (disposable description toggle).
2. Note differences in logging, error messages, and speed.
3. Decide Meridian standard: CI/`importdynamic` for promotions; console for break-glass recovery; UI for prototypes only.

**Expected result:** Decision note in binder with preferred path per scenario.

**Sample smoke transcript (redacted):**

```text
> list Application
... MNB-HR ...
> get Application MNB-HR
... type=...
> quit
```

---

## Acceptance criteria

- [ ] Console `help` captured
- [ ] Read-only `get`/`list` for at least one Meridian object
- [ ] XML import round-trip succeeded
- [ ] One task run from console with Task Result evidence
- [ ] Script file exists with no secrets
- [ ] importdynamic relationship and path-preference decision documented

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Auth fail | Wrong password / locked | Reset via documented lab procedure |
| import error | Malformed XML | Re-export; validate wrapper |
| run unknown task | Name mismatch | `list Task`; copy exact name |
| Console hangs | DB lock / long task | Check Task Results; avoid dual runs |
| History leaked password | Typed in shell wrapper | Rotate password; use prompt-only / netrc mode 600 |

---

## Training binder evidence

- `help` output
- `get` excerpt (PII-minimized)
- Import before/after note
- Task Result screenshot
- `mnb-smoke.console` path + path-preference decision

---

## Knowledge check

1. When should console be used instead of UI?
2. Why are passwords forbidden in committed console scripts?
3. What SSB target command imports `config/` XML in bulk?
4. Name two safe read-only console commands.
5. Who is the break-glass console identity in lab — and what changes in production (Lesson 109)?
6. After a console import, what evidence should land in the change ticket?

### Answers

1. Bulk import, automation, CI, recovery — not routine approvals/certs.
2. Git and CI logs leak; rotation fails; violates bank secret standards.
3. `./build.sh importdynamic` (with SPTARGET).
4. `list`, `get`, `help` (and similar inspect commands).
5. Lab: `spadmin`; production: named break-glass with logging and dual control.
6. Redacted command transcript, object `get` or Task Result ID, ticket reference.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “iiq console” for version-specific command reference.
- [Get Started with the SSD](https://community.sailpoint.com/t5/Services-Standard-Deployment/Get-Started-with-the-SSD/ta-p/73449) — how importdynamic fits Services Standard Deployment (Compass login).
- [Services Standard Build User Guide](https://community.sailpoint.com/t5/Services-Standard-Deployment/Services-Standard-Build-User-Guide-SSB/ta-p/73434) — SSB targets including war/deploy/importdynamic.
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) — why console passwords never belong in scripts or git.
- [NIST SP 800-53 Rev. 5 — AU-2 / AU-12](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — audit events for privileged configuration changes (console imports).

---

## Stretch lab

Write a console checklist that exports all `MNB-WG-*` workgroups to dated files under `~/iiq-lab-data/console/exports/YYYY-MM-DD/`, then verify one with `get`.

---

## Summary

- Console is powerful for inspect, import, and task launch — with ticket discipline and redacted transcripts.
- Never commit secrets; prefer SSB `importdynamic` for promotions.
- Prove every console change with Task Results or object `get` evidence.

---

**Previous:** [Lesson 98 — Build Meridian Toolkit Plugin](98-build-meridian-toolkit-plugin.md)  
**Next:** [Lesson 100 — IIQ REST & SCIM APIs](100-iiq-rest-scim-apis.md)
