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

- Copy Meridian fixtures into `~/iiq-lab-data` with a reproducible command and confirm the absolute path Tomcat needs
- Explain why relative paths break Delimited File applications after a restart
- Apply the `MNB-` naming standard to applications, tasks, roles, and policies — and know the optional git export path `config/<Type>/MNB-<Type>-<Business>.xml`
- Confirm CD / `importdynamic` smoke (`MNB-Rule-Hello-World`) and explain that Meridian apps like `MNB-HR` do not exist yet — you build them starting Lesson 04
- Create a dated evidence folder pattern and start a change log

## Why this matters

Messy labs teach bad production habits. Banks survive audits with reproducible builds: prefixed objects, absolute data paths, evidence of task success, and — once you promote — git-owned XML. Not "it worked on my laptop yesterday." Change control asks "what did you create, when, and why?" Your naming convention, CHANGELOG, and evidence folder are the training-ground version of that ticket trail.

## Concepts

**UI-first academy.** This repo is an SSB project. CSV fixtures live in `lab-data/`. Homelab CD ships **HelloWorld only** ([`config/PACKS.md`](../../config/PACKS.md)) — you **create** `MNB-HR` and other Meridian objects yourself in the lessons; optional export to `config/` comes later when you practice promotion.

**Delimited File ≈ CSV.** In IdentityIQ, the Delimited File connector almost always means a **CSV** feed: comma delimiter, header row, one record per line. Meridian lab files may end in `.txt` (`HRApplications.txt`, `EmployeeData.txt`) — that is only the file extension. Treat the content as CSV and configure the app with comma + header. Do not invent pipe/tab formats unless a real feed requires them.

**Why absolute paths.** Tomcat's working directory is not your shell's current directory. Relative paths like `./HRApplications.txt` silently fail, or read the wrong file, after a restart. SSB tokens (`%%MNB_HR_FILE%%`) must resolve to absolute paths, and IIQ file-path fields should hold the fully expanded path — not `~`, which connectors may not expand.

| Naming convention | Rule | Examples |
| --- | --- | --- |
| Application names | `MNB-` + platform | `MNB-HR`, `MNB-IT-Access`, `MNB-CoreBanking` |
| Aggregation tasks | `Aggregate` + app name | `Aggregate MNB-HR` |
| Refresh tasks | Clear purpose in name | `Refresh MNB Attributes`, `Refresh MNB Managers` (Lesson 06) |
| Populations | `MNB-` + audience | `MNB-Active-Employees`, `MNB-Treasury` |
| Roles / policies | `MNB-Role-*`, `MNB-SOD-*` | Later lessons |
| **Git object files** | `config/<Type>/MNB-<Type>-<Business>.xml` | `config/Application/MNB-Application-HR.xml` |

```text
repo lab-data/  --copy-->  ~/iiq-lab-data/  --absolute path-->  apps you build in Lessons 04+
                                   |
                                   +--> screenshots --> ~/iiq-lab-evidence/YYYY-MM-DD/
CD / config/  --imports-->  HelloWorld smoke only
(optional later) export your MNB-* objects --> config/ --> importdynamic (Lesson 101+)
```

> **Watch out:** Ops restarts Tomcat after a patch; if `MNB-HR` still points at `./HRApplications.txt`, aggregation silently fails and joiner cubes for `nina.joiner` never appear. Absolute-path hygiene prevents that exact outage story.

## How it works

Delimited File connectors resolve paths on the **application server OS**, not in your laptop shell's current directory. Naming prefixes and evidence folders are process controls that make objects and screenshots attributable later.

| Habit | Failure mode if skipped |
| --- | --- |
| Absolute file path | Aggregation reads wrong/empty file |
| `MNB-` prefix | Object collisions in a shared lab |
| Dated evidence | "It worked once" folklore, no reproducible binder |
| CHANGELOG line | Forgotten why an object exists |

## Before you start

- [ ] Lesson 02 complete
- [ ] Terminal access to the Sailpoint repo root
- [ ] Write access to your home directory

## Lab procedure

### Task 1 — Copy lab fixtures

Everything downstream (Lesson 04's `MNB-HR` app) reads from `~/iiq-lab-data`, never from the repo checkout directly.

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

The path you record here is exactly what you will paste into the Delimited File app's file-path field in Lesson 04.

1. Resolve the absolute path:

```bash
realpath ~/iiq-lab-data/HRApplications.txt
# typical: /Users/<you>/iiq-lab-data/HRApplications.txt
```

2. Write that path in your notebook under "MNB-HR file path."
3. Confirm the OS user that runs Tomcat can read the file (`ls -l`; adjust permissions if needed — do not make secrets world-writable).

**Expected result:** Notebook has a full absolute path starting with `/` (macOS/Linux), ready for Lesson 04.

### Task 3 — Know SSB tokens (used when you export later)

When you eventually export Applications to git, SSB substitutes `%%MNB_HR_FILE%%` (and siblings) from `sandbox.target.properties`. For now you only need the absolute path for **UI** config in Lesson 04 — tokens matter when you export (Lesson 101) or if your facilitator asks.

1. Skim `sandbox.target.properties` and [`config/PACKS.md`](../../config/PACKS.md).
2. Note that CD ships **HelloWorld only** — no pre-built `MNB-HR`.

**Expected result:** You know tokens exist for promotion; Lesson 04 pastes the absolute path directly into the UI.

### Task 4 — Naming standard card

1. Build a one-page naming card in your notebook:

| Object type | Pattern | First instance | Git path |
| --- | --- | --- | --- |
| HR app | `MNB-HR` | Lesson 04 | `config/Application/MNB-Application-HR.xml` |
| IT dump app | `MNB-IT-Access` | Lesson 09 | `config/Application/MNB-Application-IT-Access.xml` |
| HR aggregate | `Aggregate MNB-HR` | Lesson 04 | `config/TaskDefinition/MNB-TaskDefinition-Aggregate-HR.xml` |
| Attr refresh | `Refresh MNB Attributes` | Lesson 06 | `config/TaskDefinition/MNB-TaskDefinition-Refresh-Attributes.xml` |
| Populations | `MNB-Active-Employees`, … | Lesson 07 | (UI / later export) |

2. Rule: never create a Meridian object without the `MNB-` prefix in a shared lab.

**Expected result:** Card you can glance at for the rest of the curriculum.

### Task 5 — Confirm CD / SSB smoke (HelloWorld only)

Prove bake-to-import works before you assume any Meridian app already exists.

1. From repo root (if using a local WAR):

```bash
export SPTARGET=sandbox
./build.sh importdynamic
# Homelab: CD already imported; optional assert:
# ./tools/iiq-verify/assert-mnb-objects.sh k8s
```

2. In IIQ Debug (or Object search), confirm **`MNB-Rule-Hello-World`** exists.
3. Confirm **`MNB-HR` does not** exist yet — you create it in Lesson 04.
4. Add to CHANGELOG: `Confirmed HelloWorld smoke; academy apps are learner-built`.

**Expected result:** HelloWorld visible; you can explain bake XML → import into DB, with no expectation of pre-seeded apps.

**If it fails:** Read console import errors; confirm `config/Rule/MNB-Rule-Hello-World.xml` exists; see [docs/SSD.md](../SSD.md).

### Task 6 — Evidence folder and change log

1. Create today's evidence folder:

```bash
EVIDENCE=~/iiq-lab-evidence/$(date +%Y-%m-%d)
mkdir -p "$EVIDENCE"
cat > "$EVIDENCE/INTENT.txt" <<'EOF'
Lesson 03 — establish hygiene: lab-data copy, naming, evidence pattern.
Control owner (lab): trainee
SLA: keep evidence for duration of Meridian IAM Academy course.
EOF
```

2. Start your personal changelog (outside git unless you intentionally track private notes):

```bash
mkdir -p ~/iiq-lab-notes
cat >> ~/iiq-lab-notes/CHANGELOG.md <<EOF
## $(date +%Y-%m-%d)
- Copied lab-data to ~/iiq-lab-data
- Adopted MNB- naming standard
- Created evidence folder $(date +%Y-%m-%d)
EOF
```

3. Habit going forward: every new IIQ object gets one changelog line (name, why).

**Expected result:** `~/iiq-lab-evidence/YYYY-MM-DD/INTENT.txt` and a CHANGELOG entry both exist with today's date.

### Task 7 — Path failure drill (read-only thinking)

1. Write what happens if `MNB-HR` points at `lab-data/HRApplications.txt` (relative) while Tomcat starts from `$CATALINA_HOME`.
2. Write the fix (absolute path under `~/iiq-lab-data`, fully expanded).

**Expected result:** One-paragraph "path failure postmortem" in the notebook — no need to actually break the app yet.

## Acceptance criteria

- [ ] `~/iiq-lab-data` contains HR, EmployeeData, apps, scenarios, reference
- [ ] Absolute HR path recorded for Lesson 04's UI config
- [ ] Naming card complete (includes optional git export paths)
- [ ] `MNB-Rule-Hello-World` present (CD or `importdynamic`); `MNB-HR` not expected yet
- [ ] Evidence folder + `INTENT.txt` created; CHANGELOG started
- [ ] Relative-path failure explained in your own words

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import finds no objects | Wrong `SPTARGET` / WAR not built | `./build.sh clean war` then `importdynamic` |
| App file path empty after import | Token not replaced | Fix `sandbox.target.properties`; rebuild |
| `cp: No such file` | Wrong working directory | `cd` to the Sailpoint repo root |
| Permission denied reading file as Tomcat | File owned by another user | `chmod`/`chown` carefully; keep private |
| Duplicate object names in shared IIQ | Missing `MNB-` prefix | Rename or delete lab clutter; re-create with the prefix |
| Paths with `~` in IIQ | Connector may not expand `~` | Use the fully expanded `/Users/...` path |

## Training binder evidence

- Terminal output of `ls ~/iiq-lab-data`
- Screenshot or paste of the absolute HR path
- Naming card photo
- `INTENT.txt` and first CHANGELOG entry

## Knowledge check

1. Why do absolute paths matter for Delimited File apps?
2. Give three object types that should use the `MNB-` prefix.
3. What belongs in an evidence folder?
4. What is the correct aggregation task name for the HR app?
5. Why avoid reusing production object names in a shared lab?

### Answers

1. Tomcat's working directory is not your shell's current directory; relative paths break or point at the wrong file after a restart.
2. Applications, tasks, populations (also roles, policies) — any Meridian-owned config object.
3. Screenshots of task results, object configs, dates, `INTENT.txt` notes — reproducible proof of work.
4. `Aggregate MNB-HR`.
5. Collision risk, confusion during review, accidental changes to "real" named controls.

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Delimited File connector" for file path, delimiter, and header configuration details.
- [SailPoint Community](https://community.sailpoint.com/) — search "aggregation zero accounts" for path/permission failure write-ups.

## Stretch lab

- Write a small script that copies today's task-result text exports into `~/iiq-lab-evidence/$(date +%Y-%m-%d)/` with a timestamp suffix.
- Add a `PATHS.md` in `~/iiq-lab-notes` listing absolute paths for every file you will wire in Lessons 04–16.

## Summary

- Lab fixtures live under `~/iiq-lab-data` with absolute paths; SSB `%%MNB_*_FILE%%` tokens must match once you export.
- All Meridian objects use `MNB-` naming in IIQ and `config/<Type>/MNB-<Type>-<Business>.xml` in git.
- HelloWorld smoke proves bake-to-import works; dated evidence + CHANGELOG start your audit trail from day one.

## Feedback

Did the `realpath` output actually match what you pasted into your notebook, or did you guess? If the HelloWorld check failed, note the exact console error — path/token failures here are the most common early-lesson blocker and the most useful signal for revising this lesson.

## Navigate

- Previous: [Lesson 02 — Meridian Org Model & Risk Language](02-meridian-org-model.md)
- Next: [Lesson 04 — Authoritative HR Source](04-authoritative-hr-source.md)
