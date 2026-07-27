# Lesson 01 — Bank Briefing & UI Orientation

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 60–75 minutes |
| **Prereq** | Working IIQ login per [LOCAL_SETUP.md](../LOCAL_SETUP.md) |
| **Lab data** | `~/iiq-lab-data/HRApplications.txt`, `~/iiq-lab-data/EmployeeData.txt`, `~/iiq-lab-data/reference/entitlement-dictionary.csv` |

## Learning objectives

You will be able to:

- Log in to IdentityIQ as `spadmin` and recognize lab vs production cues
- Navigate Identities, Applications, Tasks, Work Items, and Debug without guessing
- Explain what an **identity cube** is and which tabs matter for Meridian controls
- Locate Meridian HR and IT dump files and name key scripted personas
- Write a one-paragraph value statement tying IIQ to bank exam evidence

## Why this matters

Meridian National Bank (MNB) bought IdentityIQ so joiners get access faster, leavers lose residual entitlements, and examiners see reproducible control evidence. Random UI wandering wastes that investment.

**Control / audit:** When an examiner asks “who owns the governance console and how do operators find identities, apps, and job results?”, your answer must be muscle memory—not a Slack search. Orientation is the first control hygiene step.

## Concepts

IdentityIQ separates four surfaces you will use every day:

| Surface | What it holds | Meridian use |
| --- | --- | --- |
| **Configuration** | Applications, roles, policies, workflows | `MNB-HR`, SoD policies, birthright roles |
| **Operational data** | Identities, accounts (links), certifications | Cubes for `helen.ross`, `priya.wire`, … |
| **Tasks** | Aggregation, refresh, certification jobs | `Aggregate MNB-HR`, `Refresh MNB Identities` |
| **Work items** | Human decisions (approvals, certs) | Manager certs, access request approvals |

```text
  [Admin configures apps/roles]
            |
            v
  [Tasks aggregate & refresh] ---> [Identity cubes]
            |                            |
            v                            v
  [Task results / counters]      [Work items for humans]
```

**Identity cube:** The person-centric record that joins HR attributes, application accounts, roles, risk, and work items. You govern *people*, not rows in a spreadsheet.

**Corporate context:** Domain `@meridiannb.com`. Lab URL `http://localhost:8080/identityiq` (homelab URL only if your site documents an alternate). Default admin: `spadmin` / `admin`.

## Before you start

- [ ] Tomcat is running and IIQ responds at `http://localhost:8080/identityiq`
- [ ] You can log in as `spadmin` / `admin`
- [ ] Repo `lab-data/` exists (copy to `~/iiq-lab-data` if not already done in Lesson 03—skimming repo files is OK for this lesson)
- [ ] Browser bookmarks folder ready for IIQ screens

## Lab procedure

### Task 1 — Login and environment hygiene

1. Start Tomcat if needed (see LOCAL_SETUP).
2. Open `http://localhost:8080/identityiq`.
3. Sign in: **User** `spadmin`, **Password** `admin`.
4. If this is a shared lab, change the password under your user preferences (or equivalent) and record the new secret in your local vault—not in git.
5. Note any environment banner, hostname, or database name visible in the UI footer/header.

**Expected result:** Home/dashboard loads without error. You see navigation to Identities / Applications / Tasks (labels vary slightly by IIQ skin).

**If it fails:** Confirm Tomcat logs and that `/identityiq` is the context path; re-check LOCAL_SETUP LCM init import if menus look empty.

### Task 2 — Tour the identity cube

1. Open **Identities** → **Identity Warehouse** (or equivalent search).
2. Search for `spadmin` and open the identity.
3. Click through tabs: attributes, accounts/applications, roles/bundles, work items, risk (or equivalent).
4. In your notebook, complete: “An identity cube is …”

**Expected result:** You can describe at least three tabs and see that a cube aggregates person + access + workflow state.

### Task 3 — Applications and Tasks map

1. Open **Applications** (often under Setup / Define Applications).
2. List stock applications present on a fresh install (do not delete any).
3. Open **Tasks** (Monitor / Setup Tasks or equivalent).
4. Scan task types: Account Aggregation, Identity Refresh, Certification—**do not** run random jobs.

**Expected result:** Notebook lists where Applications live and at least three task type names. Zero destructive runs.

### Task 4 — Work Item Inbox

1. Open your **Work Item Inbox** (Home → Work Items or equivalent).
2. Confirm it may be empty on day one.
3. Bookmark the URL.

**Expected result:** Inbox opens. You note that Lessons 35–46 will populate real approval/cert decisions here.

### Task 5 — Debug awareness

1. Open **Debug** / Administrator console (gear or Debug menu—path varies by install).
2. Browse object types: `Application`, `Identity`, `TaskDefinition`, `Bundle`, `Workflow`.
3. Open one object and confirm the body is XML.

**Expected result:** You can say “IIQ objects are XML under the hood” and name five object types used later in Meridian labs.

**If it fails:** Ensure `spadmin` retains Debug capability; some locked-down installs hide Debug—use Monitor → Advanced Analytics as a fallback awareness step and note the gap.

### Task 6 — Skim Meridian lab data

1. From a terminal:

```bash
mkdir -p ~/iiq-lab-data
# If not already copied:
cp -n lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/ 2>/dev/null || true
ls ~/iiq-lab-data/
```

2. Open `HRApplications.txt`. Find leadership `MNB00001`–`MNB00008` (`helen.ross`, `christopher.hayes`, `deepa.nair`, …).
3. Find scripted personas `MNB00090`–`MNB00097` (`priya.wire`, `marcus.approve`, `jordan.reed`, `raj.external`, `samir.hassan`, `sofia.torres`, `kai.nguyen`, `amelia.brooks`).
4. Skim `lab-data/reference/entitlement-dictionary.csv` and `sod-matrix.csv`.

**Expected result:** You can name HR as authoritative people source, IT dump as entitlement inventory, and at least four scripted usernames without looking them up again.

### Task 7 — Meridian value statement

1. Write one paragraph (4–6 sentences) answering: Why does Meridian run IdentityIQ?
2. Include: joiner/leaver speed, orphan access, dual-control wire risk, exam evidence.

**Expected result:** Paragraph references bank controls, not product marketing slogans.

### Task 8 — Persona cheat sheet (binder)

Copy this starter table into your notebook and keep it for Lessons 04–40:

| Persona | employeeId | Why it matters |
| --- | --- | --- |
| helen.ross | MNB00001 | IAM / security leadership |
| christopher.hayes | MNB00002 | Technology / AWS owner |
| deepa.nair | MNB00003 | Finance / SAP owner |
| rachel.evans | MNB00005 | Payments / wire owner |
| priya.wire | MNB00090 | WIRE_INIT only |
| marcus.approve | MNB00091 | WIRE_APPR only |
| jordan.reed | MNB00092 | SAP_FI + AWS_ADMIN (SoD) |
| raj.external | MNB00093 | Contractor + bad email |
| samir.hassan | MNB00094 | Terminated + residual IT |
| sofia.torres | MNB00095 | onLeave=true |
| kai.nguyen | MNB00096 | IBSI + ECOM (SoD) |
| amelia.brooks | MNB00097 | New teller / joiner patterns |
| nina.joiner | MNB00120 | Scenario joiner (later) |

**Expected result:** Cheat sheet filed; you can recall wire and SoD personas without reopening CSV files.

## Acceptance criteria

- [ ] Logged in as `spadmin` at localhost IIQ
- [ ] Cube tour notes completed for `spadmin`
- [ ] Applications and Tasks locations recorded
- [ ] Work Item Inbox bookmarked
- [ ] Debug XML observed (or gap documented)
- [ ] Lab personas `MNB00090`–`MNB00097` recognized
- [ ] Persona cheat sheet filed in binder
- [ ] Value statement written in notebook

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 404 on `/identityiq` | Wrong context or Tomcat down | Check Tomcat webapps and LOCAL_SETUP |
| Empty menus | Incomplete init/LCM import | Re-run init imports from LOCAL_SETUP |
| Cannot open Debug | Capability missing | Confirm `spadmin` SystemAdministrator capability |
| Lab files missing | Not copied | Copy from repo `lab-data/` to `~/iiq-lab-data/` |
| Login rejected | Password changed / locked | Reset per install docs; do not commit secrets |

## Training binder evidence

- Screenshot: successful login / home
- Screenshot: identity cube for `spadmin` (attributes + accounts tabs)
- Screenshot: Tasks list showing Aggregation / Refresh types
- Screenshot: Debug object list or opened XML snippet (redact secrets)
- Notebook: value statement + persona cheat sheet

**Examiner question to rehearse:** “Show me how an operator finds an identity and a task result in this system.”

## Knowledge check

1. What is the default lab URL and admin user?
2. In one sentence, what is an identity cube?
3. Which file is authoritative for who works at Meridian?
4. Name two scripted personas used later for wire dual control.
5. Why bookmark Work Items on day one?

### Answers

1. `http://localhost:8080/identityiq`; user `spadmin` (password `admin` unless changed).
2. The person-centric IIQ record joining attributes, accounts, roles, risk, and work items.
3. `HRApplications.txt` (HR delimited file)—not the IT entitlement dump.
4. `priya.wire` (`WIRE_INIT`) and `marcus.approve` (`WIRE_APPR`).
5. Later lessons fill it with approvals and certification decisions; it is the human-control surface.

## Stretch lab

- From Debug, export/view `spadmin` Identity XML and skim attribute and link sections.
- Read the first 10 pages of the IdentityIQ Getting Started PDF under `identityiq-8.5/doc/`.
- Draw a one-page Meridian “control surface map”: Config → Tasks → Cubes → Work Items.

## Summary

- You oriented on IIQ’s four surfaces and Meridian’s lab URL/credentials.
- You inspected an identity cube and confirmed objects are XML-backed.
- You located HR/IT lab files and scripted personas used across the curriculum.

---

**Previous:** —  
**Next:** [Lesson 02 — Meridian Org Model & Risk Language](02-meridian-org-model.md)
