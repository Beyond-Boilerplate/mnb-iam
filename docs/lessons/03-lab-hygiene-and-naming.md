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
- Document absolute file paths Tomcat can read
- Apply the `MNB-` naming standard to applications, tasks, roles, and policies
- Create a dated evidence folder pattern for screenshots and task results
- Maintain a simple change log that an examiner could follow

## Why this matters

Messy labs teach bad production habits. Banks survive exams with reproducible builds: prefixed objects, absolute data paths, and dated evidence of task success—not “it worked on my laptop yesterday.”

**Control / audit:** Change control asks “what did you create, when, and why?” Your naming convention and evidence folder are the training-ground version of a CAB ticket trail.

## Concepts

| Convention | Rule | Examples |
| --- | --- | --- |
| Application names | `MNB-` + platform | `MNB-HR`, `MNB-IT-Access`, `MNB-CoreBanking` |
| Aggregation tasks | `Aggregate` + app name | `Aggregate MNB-HR` |
| Refresh tasks | Clear scope in name | `Refresh MNB Identities` |
| Populations | `MNB-` + audience | `MNB-Active-Employees`, `MNB-Treasury` |
| Roles / policies | `MNB-Role-*`, `MNB-SOD-*` | Later lessons |

```text
  repo lab-data/  --copy-->  ~/iiq-lab-data/  --absolute path-->  IIQ DelimitedFile apps
                                      |
                                      +--> screenshots --> ~/iiq-lab-evidence/YYYY-MM-DD/
```

**Why absolute paths:** Tomcat’s working directory is not your shell cwd. Relative paths like `./HRApplications.txt` silently fail or read the wrong file after restart.

**Control owner (lab):** You (trainee). In prod, IAM Ops owns task schedules; Application owners own entitlement dictionaries.

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

### Task 3 — Naming standard card

1. Create a one-page naming card in your notebook:

| Object type | Pattern | First instance |
| --- | --- | --- |
| HR app | `MNB-HR` | Lesson 04 |
| IT dump app | `MNB-IT-Access` | Lesson 09 |
| HR aggregate | `Aggregate MNB-HR` | Lesson 04 |
| IT aggregate | `Aggregate MNB-IT-Access` | Lesson 09 |
| Refresh | `Refresh MNB Identities` | Lesson 06 |
| Populations | `MNB-Active-Employees`, … | Lesson 07 |

2. Rule: never create Meridian objects without the `MNB-` prefix in a shared lab.

**Expected result:** Card you can glance at for the rest of the curriculum.

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
- [ ] Absolute HR path recorded
- [ ] Naming card complete
- [ ] Evidence folder + INTENT.txt created
- [ ] CHANGELOG started
- [ ] Relative-path failure explained

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
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

## Stretch lab

- Write a small script that copies today’s task-result text exports into `~/iiq-lab-evidence/$(date +%Y-%m-%d)/` with a timestamp suffix.
- Add a `PATHS.md` in `~/iiq-lab-notes` listing absolute paths for every file you will wire in Lessons 04–16.
- Practice redacting passwords from any screenshot before filing evidence.

## Summary

- Lab fixtures live under `~/iiq-lab-data` with absolute paths for IIQ.
- All Meridian objects use `MNB-` naming; tasks follow `Aggregate` / `Refresh` patterns.
- Dated evidence folders and a changelog train exam-ready habits.

---

**Previous:** [Lesson 02 — Meridian Org Model & Risk Language](02-meridian-org-model.md)  
**Next:** [Lesson 04 — Authoritative HR Source](04-authoritative-hr-source.md)
