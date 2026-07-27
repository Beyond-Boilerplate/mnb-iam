# Lesson 03 — Lab Hygiene, Naming & Evidence Habits

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 45 minutes |
| **Prereq** | Lesson 02 |
| **Lab data** | Full copy of `lab-data/` → `~/iiq-lab-data/` |

## Learning objectives

You will be able to:

- Copy Meridian fixtures into `~/iiq-lab-data` with a reproducible command
- Document absolute file paths Tomcat can read and align `%%MNB_*_FILE%%` SSB tokens
- Apply the `MNB-` naming standard to applications, tasks, roles, and policies — including git paths `config/<Type>/MNB-….xml`
- Import the Meridian academy seed pack (`importdynamic` or verify HelloWorld) so learner setup matches bank-shaped SSB
- Create a dated evidence folder pattern for screenshots and task results
- Maintain a simple change log that an examiner could follow

## Why this matters

Messy labs teach bad production habits. Banks survive exams with reproducible builds: prefixed objects, absolute data paths, **git-owned XML**, and dated evidence of task success—not “it worked on my laptop yesterday.”

**Control / audit:** Change control asks “what did you create, when, and why?” Your naming convention, `config/` path, and evidence folder are the training-ground version of a CAB ticket trail.

## Concepts

| Convention | Rule | Examples |
| --- | --- | --- |
| Application names | `MNB-` + platform | `MNB-HR`, `MNB-IT-Access`, `MNB-CoreBanking` |
| Aggregation tasks | `Aggregate` + app name | `Aggregate MNB-HR` |
| Refresh tasks | Clear purpose in name | `Refresh MNB Attributes`, `Refresh MNB Managers` (Lesson 06) |
| Populations | `MNB-` + audience | `MNB-Active-Employees`, `MNB-Treasury` |
| Roles / policies | `MNB-Role-*`, `MNB-SOD-*` | Later lessons |
| **Git object files** | `config/<Type>/MNB-<Type>-<Business>.xml` | `Application/MNB-Application-HR.xml` |

```text
  repo lab-data/  --copy-->  ~/iiq-lab-data/  --%%TOKENS%%-->  config/ Application XML
                                      |
                                      +--> screenshots --> ~/iiq-lab-evidence/YYYY-MM-DD/
  repo config/  --SSB build/import-->  IIQ DB (same objects Meridian Ops promotes)
```

**Learner setup = scoped bank setup.** This repo is an SSB project. CSV fixtures live in `lab-data/`; IIQ objects live in [`config/`](../../config/PACKS.md). You will still craft some objects in the UI (first principles), but durable controls must survive wipe+import.

**Delimited File ≈ CSV.** In IdentityIQ, the Delimited File connector almost always means a **CSV** feed: comma delimiter, header row, one record per line. Meridian lab files may end in `.txt` (`HRApplications.txt`, `EmployeeData.txt`)—that is only the extension. Treat the content as CSV and configure the app with comma + header. Do not invent pipe/tab formats unless a real feed requires them.

**Why absolute paths:** Tomcat’s working directory is not your shell cwd. Relative paths like `./HRApplications.txt` silently fail or read the wrong file after restart. SSB tokens (`%%MNB_HR_FILE%%`) must resolve to absolute paths.

**Control owner (lab):** You (trainee). In prod, IAM Ops owns task schedules; Application owners own entitlement dictionaries.

## How it works

Delimited File connectors resolve paths on the **application server OS**, not in your laptop shell’s current directory. Naming prefixes and evidence folders are process controls that make objects and screenshots attributable later.

```text
repo lab-data/
      │  cp
      ▼
~/iiq-lab-data/*.txt   ──absolute path──►  MNB-* DelimitedFile Application
      │
      └── screenshots / task results ──► ~/iiq-lab-evidence/YYYY-MM-DD/
```

| Habit | Failure mode if skipped | Exam impact |
| --- | --- | --- |
| Absolute file path | Aggregation reads wrong/empty file | “Control failed last night” |
| `MNB-` prefix | Object collisions in shared lab | Cannot prove ownership |
| Dated evidence | “It worked once” folklore | No reproducible binder |
| CHANGELOG line | Forgotten why object exists | Change-control finding |

**Real-life Meridian example.** Ops restarts Tomcat after a patch; if `MNB-HR` still points at `./HRApplications.txt`, aggregation silently fails and joiner cubes for `nina.joiner` never appear—hygiene prevents that outage story.

## Before you start

- [ ] Lesson 02 complete
- [ ] Terminal access to the Sailpoint repo root
- [ ] Write access to your home directory

## Lab procedure

### Task 1 — Copy lab fixtures

1. From the repo root:

```bash
mkdir -p ~/iiq-lab-data
cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/
cp -R lab-data/apps lab-data/scenarios lab-data/reference ~/iiq-lab-data/
```

2. Verify:

```bash
ls -la ~/iiq-lab-data
ls ~/iiq-lab-data/apps | head
ls ~/iiq-lab-data/reference
ls ~/iiq-lab-data/scenarios
```

**Expected result:** `HRApplications.txt`, `EmployeeData.txt`, plus `apps/`, `scenarios/`, `reference/` directories present.

**If it fails:** Confirm you are in the Sailpoint repo root (`ls lab-data` succeeds).

### Task 2 — Absolute path check

1. Resolve the absolute path:

```bash
realpath ~/iiq-lab-data/HRApplications.txt
# typical: /Users/<you>/iiq-lab-data/HRApplications.txt
```

2. Write that path in your notebook under “MNB-HR file path”.
3. Confirm the OS user that runs Tomcat can read the file (`ls -l`; adjust permissions if needed—do not world-writable secrets).

**Expected result:** Notebook has a full absolute path starting with `/` (macOS/Linux) ready for Lesson 04 application config.

### Task 2b — Align SSB file tokens

Bank-shaped builds substitute `%%MNB_HR_FILE%%` (and siblings) from `sandbox.target.properties`. Point them at **your** absolute lab paths so import matches the UI.

1. Open `sandbox.target.properties` in the repo.
2. Set (use your `realpath` values):

```properties
%%MNB_HR_FILE%%=/Users/<you>/iiq-lab-data/HRApplications.txt
%%MNB_IT_ACCESS_FILE%%=/Users/<you>/iiq-lab-data/EmployeeData.txt
%%MNB_CORE_BANKING_FILE%%=/Users/<you>/iiq-lab-data/apps/MNB-CoreBanking.csv
%%MNB_WIRE_FILE%%=/Users/<you>/iiq-lab-data/apps/MNB-WirePortal.csv
%%MNB_SAP_FILE%%=/Users/<you>/iiq-lab-data/apps/MNB-SAP-Finance.csv
%%MNB_AWS_FILE%%=/Users/<you>/iiq-lab-data/apps/MNB-AWS-Cloud.csv
```

3. Do **not** commit workstation-specific paths if your team shares the repo—use a local override or document the path in CHANGELOG for the academy laptop. Homelab keeps `/opt/iiq-lab-data/…`.
4. Skim [`config/PACKS.md`](../../config/PACKS.md) so you know which objects the academy seeds.

**Expected result:** Tokens match your lab-data absolute paths; PACKS.md skimmed.

### Task 3 — Naming standard card

1. Create a one-page naming card in your notebook:

| Object type | Pattern | First instance | Git path |
| --- | --- | --- | --- |
| HR app | `MNB-HR` | Lesson 04 | `config/Application/MNB-Application-HR.xml` |
| IT dump app | `MNB-IT-Access` | Lesson 09 | `config/Application/MNB-Application-IT-Access.xml` |
| HR aggregate | `Aggregate MNB-HR` | Lesson 04 | `config/TaskDefinition/MNB-TaskDefinition-Aggregate-HR.xml` |
| Attr refresh | `Refresh MNB Attributes` | Lesson 06 | `config/TaskDefinition/MNB-TaskDefinition-Refresh-Attributes.xml` |
| Populations | `MNB-Active-Employees`, … | Lesson 07 | (UI / later export) |

2. Rule: never create Meridian objects without the `MNB-` prefix in a shared lab; durable controls also land under `config/`.

**Expected result:** Card you can glance at for the rest of the curriculum.

### Task 3b — First SSB import (HelloWorld + seed pack)

Learner setup imports the same `config/` Meridian Ops promotes. Prove the pipe works before Lesson 04 UI craft.

1. From repo root (IIQ already running; `SPTARGET=sandbox`):

```bash
export SPTARGET=sandbox
./build.sh importdynamic
# Homelab alternate: rely on CD import after push; then assert:
# ./tools/iiq-verify/assert-mnb-objects.sh k8s
```

2. In IIQ Debug (or Object search), confirm **`MNB-Rule-Hello-World`** exists.
3. Optionally confirm **`MNB-HR`** Application from the seed pack (if import succeeded with your file tokens). If `MNB-HR` is present, Lesson 04 becomes **verify + attribute maps** instead of creating from scratch—still walk the UI so you understand every setting.
4. CHANGELOG: `importdynamic — HelloWorld (+ HR pack if present)`.

**Expected result:** At least HelloWorld visible in Debug; you can explain bake XML → import into DB.

**If it fails:** Read console import errors; confirm `config/Rule/MNB-Rule-HelloWorld.xml` exists; fix tokens; see [docs/SSD.md](../SSD.md).

### Task 4 — Evidence folder

1. Create today’s folder:

```bash
EVIDENCE=~/iiq-lab-evidence/$(date +%Y-%m-%d)
mkdir -p "$EVIDENCE"
cat > "$EVIDENCE/INTENT.txt" <<'EOF'
Lesson 03 — establish hygiene: lab-data copy, naming, evidence pattern.
Control owner (lab): trainee
SLA: keep evidence for duration of Meridian IAM Academy course.
EOF
```

2. Drop a screenshot later from IIQ login (or paste path notes) into the same folder.

**Expected result:** `~/iiq-lab-evidence/YYYY-MM-DD/INTENT.txt` exists with today’s date.

### Task 5 — Change log habit

1. Create a personal changelog (outside git unless you intentionally track private notes):

```bash
mkdir -p ~/iiq-lab-notes
cat >> ~/iiq-lab-notes/CHANGELOG.md <<EOF
## $(date +%Y-%m-%d)
- Copied lab-data to ~/iiq-lab-data
- Adopted MNB- naming standard
- Created evidence folder $(date +%Y-%m-%d)
EOF
```

2. Habit: every new IIQ object → one changelog line (name, why).

**Expected result:** CHANGELOG entry for today; empty template ready for Lesson 04 objects.

### Task 6 — Path failure drill (read-only thinking)

1. Write what happens if `MNB-HR` points at `lab-data/HRApplications.txt` (relative) and Tomcat starts from `$CATALINA_HOME`.
2. Write the fix (absolute path under `~/iiq-lab-data`).

**Expected result:** One-paragraph “path failure postmortem” in the notebook—no need to break the app yet.

## Acceptance criteria

- [ ] `~/iiq-lab-data` contains HR, EmployeeData, apps, scenarios, reference
- [ ] Absolute HR path recorded; `%%MNB_*_FILE%%` tokens aligned
- [ ] Naming card complete (includes git paths)
- [ ] `MNB-Rule-Hello-World` present after import (or failure documented with fix plan)
- [ ] Evidence folder + INTENT.txt created
- [ ] CHANGELOG started
- [ ] Relative-path failure explained

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import finds no objects | Wrong SPTARGET / WAR not built | `./build.sh clean war` then `importdynamic` |
| App file path empty after import | Token not replaced | Fix `sandbox.target.properties`; rebuild |
| Permission denied on lab file | OS user / ACL | Adjust ownership; keep path absolute |
| `cp: No such file` | Wrong cwd | `cd` to Sailpoint repo root |
| Permission denied reading file as Tomcat | File owned by another user | `chmod`/`chown` carefully; keep private |
| Evidence folders multiply chaotically | No date convention | Always `YYYY-MM-DD` |
| Duplicate object names in shared IIQ | Missing `MNB-` prefix | Rename or delete lab clutter; re-create with prefix |
| Paths with `~` in IIQ | Connector may not expand `~` | Prefer fully expanded `/Users/...` path |

## Training binder evidence

- Terminal output of `ls ~/iiq-lab-data`
- Screenshot or paste of absolute HR path
- Naming card photo
- `INTENT.txt` and first CHANGELOG entry

**Examiner question:** “How do you ensure aggregation jobs still find HR files after an application server restart?”

## Knowledge check

1. Why absolute paths for delimited files?
2. Give three object types that should use the `MNB-` prefix.
3. What belongs in evidence folders?
4. What is the correct aggregation task name for the HR app?
5. Why avoid reusing production object names in a shared lab?

### Answers

1. Tomcat’s cwd is not your shell cwd; relative paths break or point at wrong files after restart.
2. Applications, tasks, populations (also roles, policies)—any Meridian-owned config object.
3. Screenshots of task results, object configs, dates, INTENT notes—reproducible proof of work.
4. `Aggregate MNB-HR`.
5. Collision risk, audit confusion, accidental changes to “real” named controls.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “Delimited File connector” for file path, delimiter, and header configuration details.
- [SailPoint Community](https://community.sailpoint.com/) — search “aggregation zero accounts” for path/permission failure write-ups.
- [NIST SP 800-53 CM / AU families](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — configuration management and audit evidence habits mirrored by naming + evidence folders.
- [FFIEC IT Examination Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/it-booklets/architecture-infrastructure-and-operations.aspx) — change-control and operational resilience expectations for bank platforms.
- [CIS Controls v8 — Control 4 (Secure Configuration)](https://www.cisecurity.org/controls/secure-configuration-of-enterprise-assets-and-software) — baseline for consistent, documented configuration of systems that process identities.

## Stretch lab

- Write a small script that copies today’s task-result text exports into `~/iiq-lab-evidence/$(date +%Y-%m-%d)/` with a timestamp suffix.
- Add a `PATHS.md` in `~/iiq-lab-notes` listing absolute paths for every file you will wire in Lessons 04–16.
- Practice redacting passwords from any screenshot before filing evidence.

## Summary

- Lab fixtures live under `~/iiq-lab-data` with absolute paths; SSB `%%MNB_*_FILE%%` tokens must match.
- All Meridian objects use `MNB-` naming in IIQ **and** `config/<Type>/MNB-….xml` in git.
- First `importdynamic` proves learner setup equals scoped bank SSB import; dated evidence + CHANGELOG train exam-ready habits.

---

**Previous:** [Lesson 02 — Meridian Org Model & Risk Language](02-meridian-org-model.md)  
**Next:** [Lesson 04 — Authoritative HR Source](04-authoritative-hr-source.md)
