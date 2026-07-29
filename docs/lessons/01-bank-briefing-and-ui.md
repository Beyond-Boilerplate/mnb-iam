# Lesson 01 — Bank Briefing & UI Orientation

| Field | Value |
| --- | --- |
| **Level** | Beginner |
| **Track** | Foundations |
| **Time** | 75–90 minutes |
| **Prereq** | Working IIQ login per [LOCAL_SETUP.md](../LOCAL_SETUP.md) |
| **Lab data** | `~/iiq-lab-data/HRApplications.txt`, `~/iiq-lab-data/EmployeeData.txt`, `~/iiq-lab-data/reference/entitlement-dictionary.csv` |

## Learning objectives

You will be able to:

- Describe what Identity and Access Management (IAM) does at a bank and where you sit on Meridian’s team
- Define the core IAM building blocks in plain English (identity, account, entitlement, application, role, policy)
- Log in to IdentityIQ as `spadmin` and recognize lab vs production cues
- Navigate Identities, Applications, Tasks, Work Items, and Debug without guessing
- Explain what an **identity cube** is and which tabs matter day to day
- Locate Meridian HR and IT dump files and name key scripted personas

## Why this matters

You just joined Meridian National Bank’s Identity & Access team. Your manager will not start you on “joiner workflows” or SoD policies on day one. They will walk you through who owns what, what problem IIQ is solving, and how to find things in the console without breaking anything.

That is this lesson. Orientation first. Lifecycle automation comes later (Lesson 29+), after you understand people, apps, and access language.

**Control / audit:** When an examiner asks “who operates the governance console and how do you find an identity or a job result?”, your answer should be muscle memory—not a Slack search. Day-one navigation is the first control hygiene step.

## Concepts

### 1. What IAM is (and is not)

**Identity and Access Management (IAM)** is the practice of making sure the right people have the right access to the right systems—for the right reason—and can prove it later.

At a bank that means:

| Question examiners ask | What IAM must show |
| --- | --- |
| Who works here? | A reliable list of people from HR |
| What can they do in systems? | Accounts and entitlements tied to those people |
| Who approved that access? | Approvals, certifications, or documented exceptions |
| What happens when someone leaves? | Access removed or disabled on a known timeline |

IAM is **not** the help desk resetting passwords all day, and it is **not** network firewalls. Those teams partner with you. Your focus is **identity governance**: knowing who someone is, what they have, and whether that access is still appropriate.

Meridian bought **SailPoint IdentityIQ (IIQ)** as the governance platform. IIQ does not replace Active Directory, SAP, or the wire portal. It connects to those systems, builds a picture of each person’s access, and runs the processes (approvals, reviews, policies) that Risk and Audit expect.

### 2. Your team and who you work with

You are an **IAM Engineer** on the Identity Governance squad under Information Security (`SEC`). You will hear “IAM Ops,” “IGA,” and “Identity” used interchangeably for the same group.

```text
Helen Ross (helen.ross) — Head of Identity & Access
        │
        ├── IAM Engineering  ← you (design roles, apps, policies, workflows in IIQ)
        ├── IAM Operations   (run scheduled jobs, triage failures, handle tickets)
        └── IAM Governance   (cert campaigns, policy exceptions, exam evidence)

Partners outside the squad:
  HR Operations     — people data quality (hires, transfers, terminations)
  App / system owners — own entitlements on their platform (wire, SAP, cloud, core)
  Risk & Compliance — SoD design, exam readiness
  Technology        — directories, connectors, infrastructure
```

| Person | userId | Role you will hear | Why it matters to you |
| --- | --- | --- | --- |
| helen.ross | MNB00001 | Head of Identity & Access | Your leadership; IAM platform owner |
| christopher.hayes | MNB00002 | Director of Technology | Owns cloud / directory platforms |
| deepa.nair | MNB00003 | Director of Finance | Owns SAP finance entitlements |
| anthony.powell | MNB00004 | Risk leadership | Partner on toxic-access (SoD) design |
| rachel.evans | MNB00005 | Payments / wire owner | Owns wire initiate vs approve entitlements |
| daniel.griffin | MNB00008 | Operations | Owns core banking access |

You will not configure those platforms yourself on day one. You **govern** access to them in IIQ, with those people as control owners.

### 3. Core constructs — learn these words first

Ignore product buzzwords until these six ideas are solid. Everything else in the curriculum hangs on them.

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Identity** | A person (or sometimes a service) that Meridian tracks as “one worker” | `priya.wire` — Priya in Treasury |
| **Account** | A login on one system | Priya’s Wire Portal username |
| **Entitlement** | A permission or group on that system (“what the account can do”) | `WIRE_INIT` — can create a wire |
| **Application** | An IIQ definition of a connected system (how we read/write accounts) | Later: `MNB-Wire-Portal` |
| **Role** | A package of entitlements (or nested roles) assigned for a job | “Wire Specialist birthright” (Lesson 24+) |
| **Policy** | A rule that flags bad access combinations or states | “Nobody holds both wire initiate and approve” (Lesson 39+) |

Two more terms you will see in the UI today:

| Term | Plain English |
| --- | --- |
| **Identity cube** | IIQ’s person-centric record: HR attributes + accounts + roles + risk + open work. You govern *people*, not spreadsheet rows. |
| **Work item** | A human decision waiting in someone’s Inbox (approve access, certify access, remediate a violation). |

```text
  Identity (the person)
       │
       ├── Attributes from HR (dept, job, manager, status…)
       ├── Accounts ──► each account has Entitlements on an Application
       ├── Roles (packages of access)
       └── Work items / certifications / policy findings
```

**Wrong way beginners think:** “IIQ is the directory where people log in.”  
**Right way:** Active Directory (and peers) are where people often authenticate. IIQ is where Meridian **governs and proves** access across many systems.

### 4. Terms you will hear later (do not panic)

Managers and staff engineers talk in shorthand. You only need **recognition** today—not configuration.

| Shorthand | Meaning | When you build it |
| --- | --- | --- |
| **Joiner** | Someone new starts; they need starting access | Lesson 29 |
| **Mover** | Someone changes job/dept; access must follow | Lesson 30 |
| **Leaver** | Someone leaves; access must be removed/disabled | Lesson 31 |
| **Birthright** | Access every active person of a class gets automatically | Lesson 24 |
| **SoD** (segregation of duties) | Toxic combination of entitlements one person should not hold together | Lesson 39 |
| **Population** | A saved search/filter of identities (e.g. “all contractors”) | Lesson 07 |
| **Aggregation** | A job that pulls accounts/entitlements from an application into IIQ | Lesson 04+ |
| **Certification** | A campaign where managers or owners attest that access is still needed | Lesson 43+ |

If someone says “fix the joiner for Nina,” they mean: make sure the new hire’s cube exists and starting access is correct. You will practice that after HR, apps, and roles are in place.

### 5. The four surfaces you use every day

IdentityIQ separates work into four places. Bookmark them mentally:

| Surface | What it holds | Meridian habit |
| --- | --- | --- |
| **Configuration** | Applications, roles, policies, workflows | Names start with `MNB-` |
| **Operational data** | Identities, accounts (links), certifications | Search people by name like `helen.ross` |
| **Tasks** | Aggregation, refresh, certification jobs | Prefer named tasks (`Aggregate MNB-HR`) later |
| **Work items** | Human decisions | Inbox on day one—even if empty |

```text
  [You configure apps / roles / policies]
            |
            v
  [Tasks pull accounts & refresh cubes] ---> [Identity cubes]
            |                                      |
            v                                      v
  [Task results / counters]              [Work items for humans]
```

**Corporate context:** Email domain `@meridiannb.com`. Lab URL `http://localhost:8080/identityiq`. Default admin: `spadmin` / `admin`. Homelab sites may publish a different URL—use what your LOCAL_SETUP documents.

## How it works

IdentityIQ is configuration-driven: engineers define applications and policies; scheduled **tasks** pull accounts and compile **identity cubes**; **work items** capture human decisions.

```text
Browser (spadmin)
      │
      ▼
IIQ UI / REST  ──►  Object model (Application, Identity, TaskDefinition, Bundle, …)
      │                      │
      │                      ▼
      │              Database persistence (objects often edited/exported as XML)
      │
      ├── Tasks run aggregations & refreshes
      └── Work Item Inbox holds approvals / cert decisions
```

| Surface | IIQ objects you touch | Lab habit |
| --- | --- | --- |
| Config | Application, Bundle (role), Policy | Always `MNB-` prefix when you create objects |
| People | Identity (+ Links to accounts) | Search by Identity **name**; HR key will be `userId` |
| Jobs | TaskDefinition / TaskResult | Do not run random jobs on day one |
| Human control | WorkItem, Certification | Bookmark Inbox |

**Day-one Meridian picture.** Helen Ross (`helen.ross`) already exists as a person Meridian cares about. Later, when Rachel Evans certifies wire access for Priya, that decision lands as a work item on Priya’s cube—orientation today is how you find those objects under pressure.

## Before you start

- [ ] Tomcat is running and IIQ responds at `http://localhost:8080/identityiq` (or your documented lab URL)
- [ ] You can log in as `spadmin` / `admin`
- [ ] Repo `lab-data/` exists (copy to `~/iiq-lab-data` if not already done—skimming repo files is OK for this lesson)
- [ ] Browser bookmarks folder ready for IIQ screens
- [ ] Notebook ready for glossary + persona cheat sheet

## Lab procedure

### Task 1 — Login and environment hygiene

Treat first login as environment hygiene: confirm you are on the **lab**, not a shared or mislabeled URL, before exploring cubes. In production, wrong-environment mistakes are incident tickets.

1. Start Tomcat if needed (see LOCAL_SETUP).
2. Open `http://localhost:8080/identityiq`.
3. Sign in: **User** `spadmin`, **Password** `admin`.
4. If this is a shared lab, change the password under your user preferences (or equivalent) and record the new secret in your local vault—not in git.
5. Note any environment banner, hostname, or database name visible in the UI footer/header.

**Expected result:** Home/dashboard loads without error. You see navigation to Identities / Applications / Tasks (labels vary slightly by IIQ skin).

**If it fails:** Confirm Tomcat logs and that `/identityiq` is the context path; re-check LOCAL_SETUP LCM init import if menus look empty.

### Task 2 — Tour the identity cube

Your staff engineer will say: “Open a cube and click every tab once. You are learning the shape of a person in IIQ.”

1. Open **Identities** → **Identity Warehouse** (or equivalent search).
2. Search for `spadmin` and open the identity.
3. Click through tabs: attributes, accounts/applications, roles/bundles, work items, risk (or equivalent).
4. In your notebook, complete in your own words: “An identity cube is …”
5. Optional: search for `helen.ross` if she already exists in your lab; if not, that is fine—HR aggregation comes in Lesson 04.

**Expected result:** You can describe at least three tabs and see that a cube aggregates person + access + workflow state.

### Task 3 — Applications and Tasks map

Applications are “systems IIQ knows about.” Tasks are “jobs that move data or run campaigns.” Today you only **look**.

1. Open **Applications** (often under Setup / Define Applications).
2. List stock applications present on a fresh install (do not delete any).
3. Open **Tasks** (Monitor / Setup Tasks or equivalent).
4. Scan task types: Account Aggregation, Identity Refresh, Certification—**do not** run random jobs.

**Expected result:** Notebook lists where Applications live and at least three task type names. Zero destructive runs.

### Task 4 — Work Item Inbox

Approvals and certifications land here. Empty on day one is normal.

1. Open your **Work Item Inbox** (Home → Work Items or equivalent).
2. Confirm it may be empty.
3. Bookmark the URL.

**Expected result:** Inbox opens. You note that Lessons 35–46 will populate real approval/cert decisions here.

### Task 5 — Debug awareness

Debug is the engineer’s X-ray: objects are often XML under the hood. Look, do not edit randomly.

1. Open **Debug** / Administrator console (gear or Debug menu—path varies by install).
2. Browse object types: `Application`, `Identity`, `TaskDefinition`, `Bundle`, `Workflow`.
3. Open one object and confirm the body is XML.

**Expected result:** You can say “IIQ objects are XML under the hood” and name five object types used later in Meridian labs.

**If it fails:** Ensure `spadmin` retains Debug capability; some locked-down installs hide Debug—use Monitor → Advanced Analytics as a fallback awareness step and note the gap.

### Task 6 — Skim Meridian lab data (people files, not IIQ yet)

Before IIQ “knows” Meridian workers, the truth lives in files. Your pairing partner will open these with you so names stick.

1. From a terminal at the repo root:

```bash
mkdir -p ~/iiq-lab-data
# If not already copied:
cp -n lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/ 2>/dev/null || true
ls ~/iiq-lab-data/
```

2. Open `HRApplications.txt`. Find leadership `MNB00001`–`MNB00008` (`helen.ross`, `christopher.hayes`, `deepa.nair`, …).
3. Find scripted personas `MNB00090`–`MNB00097` (`priya.wire`, `marcus.approve`, `jordan.reed`, `raj.external`, `samir.hassan`, `sofia.torres`, `kai.nguyen`, `amelia.brooks`).
4. Skim `lab-data/reference/entitlement-dictionary.csv`—notice codes like `WIRE_INIT` and a **risk** column. You will classify risk properly in Lesson 02.
5. Glance at `sod-matrix.csv` only to see that Meridian already listed “bad pairs.” Do **not** memorize SoD policy design yet—Lesson 02 and Lesson 39 teach that.

**Expected result:** You can name HR as the people source of truth, the IT dump as entitlement inventory, and at least four scripted usernames without looking them up again.

### Task 7 — One-paragraph “why Meridian runs IIQ”

Write for your manager, not for marketing.

1. Write one paragraph (4–6 sentences) answering: Why does Meridian run IdentityIQ?
2. Cover in plain language: knowing who works here, knowing what access they hold, proving reviews/approvals to examiners, and reducing leftover access when people change jobs or leave.
3. Avoid unexplained jargon. If you use “joiner” or “SoD,” define it in the same sentence.

**Expected result:** Paragraph a non-IAM colleague could understand; bank controls, not product slogans.

### Task 8 — Persona cheat sheet (binder)

Copy this starter table into your notebook and keep it for Lessons 04–40:

| Persona | userId (HR) | Why it matters |
| --- | --- | --- |
| helen.ross | MNB00001 | IAM / security leadership |
| christopher.hayes | MNB00002 | Technology / AWS owner |
| deepa.nair | MNB00003 | Finance / SAP owner |
| rachel.evans | MNB00005 | Payments / wire owner |
| priya.wire | MNB00090 | Holds wire initiate only (`WIRE_INIT`) |
| marcus.approve | MNB00091 | Holds wire approve only (`WIRE_APPR`) |
| jordan.reed | MNB00092 | Holds finance + cloud admin (intentional bad combo for later labs) |
| raj.external | MNB00093 | Contractor + bad email (data-quality story) |
| samir.hassan | MNB00094 | Terminated + leftover IT access |
| sofia.torres | MNB00095 | On leave (`exceptions=LOA`) |
| kai.nguyen | MNB00096 | Digital support + channel promo (another intentional bad combo) |
| amelia.brooks | MNB00097 | New teller patterns |
| nina.joiner | MNB00120 | New-hire scenario file (Lesson 29) |

> **ID map:** HR key = `userId`. IT dump column `employeeId` uses the **same** `MNB#####` values so accounts can be tied to people later (Lesson 09+).

**Expected result:** Cheat sheet filed; you can recall wire pair and leadership names without reopening CSV files.

## Acceptance criteria

- [ ] Can explain IAM vs directories in one or two sentences
- [ ] Can name your team lead and at least three partner owners
- [ ] Can define identity, account, entitlement, application, role, policy without looking them up
- [ ] Logged in as `spadmin` at lab IIQ
- [ ] Cube tour notes completed for `spadmin`
- [ ] Applications and Tasks locations recorded
- [ ] Work Item Inbox bookmarked
- [ ] Debug XML observed (or gap documented)
- [ ] Lab personas `MNB00090`–`MNB00097` recognized
- [ ] Persona cheat sheet filed in binder
- [ ] Value statement written in notebook (plain language)

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 404 on `/identityiq` | Wrong context or Tomcat down | Check Tomcat webapps and LOCAL_SETUP |
| Empty menus | Incomplete init/LCM import | Re-run init imports from LOCAL_SETUP |
| Cannot open Debug | Capability missing | Confirm `spadmin` SystemAdministrator capability |
| Lab files missing | Not copied | Copy from repo `lab-data/` to `~/iiq-lab-data/` |
| Login rejected | Password changed / locked | Reset per install docs; do not commit secrets |
| Overwhelmed by jargon | Normal on day one | Stick to the six core constructs; park joiner/SoD terms for later lessons |

## Training binder evidence

- Screenshot: successful login / home
- Screenshot: identity cube for `spadmin` (attributes + accounts tabs)
- Screenshot: Tasks list showing Aggregation / Refresh types
- Screenshot: Debug object list or opened XML snippet (redact secrets)
- Notebook: team sketch + core-construct glossary + value statement + persona cheat sheet

**Examiner question to rehearse:** “Show me how an operator finds an identity and a task result in this system.”

## Knowledge check

1. What is the default lab URL and admin user?
2. In one sentence, what is an identity cube?
3. What is the difference between an **account** and an **entitlement**?
4. Who is Meridian’s Head of Identity & Access (persona name)?
5. Which file is authoritative for who works at Meridian?
6. Name the two personas used later to show healthy wire dual control (initiate vs approve on different people).

### Answers

1. `http://localhost:8080/identityiq`; user `spadmin` (password `admin` unless changed).
2. The person-centric IIQ record joining attributes, accounts, roles, risk, and work items.
3. An account is a login on one system; an entitlement is a permission/group that login holds on that system.
4. `helen.ross` (MNB00001).
5. `HRApplications.txt` (HR delimited file)—not the IT entitlement dump.
6. `priya.wire` (`WIRE_INIT`) and `marcus.approve` (`WIRE_APPR`).

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “IdentityIQ getting started” and “identity warehouse” for your version’s UI map and cube concepts.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “IdentityIQ navigation” / “Debug page” for practitioner tips on finding objects and task results.
- [NIST SP 800-53 Rev. 5 — AC family](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — account management and access enforcement controls examiners map to “who operates the IAM console.”
- [FFIEC IT Examination Handbook — Information Security](https://ithandbook.ffiec.gov/it-booklets/information-security.aspx) — how banking exams expect attributable, repeatable access governance processes.
- [OWASP Identity Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Identity_and_Access_Management_Cheat_Sheet.html) — industry primer on identity lifecycle hygiene that IIQ operationalizes.

## Stretch lab

- From Debug, export/view `spadmin` Identity XML and skim attribute and link sections.
- Read the first 10 pages of the IdentityIQ Getting Started PDF under `identityiq-8.5/doc/`.
- Draw a one-page Meridian map: Team → Core constructs → Four IIQ surfaces (Config → Tasks → Cubes → Work Items).

## Summary

- You know what IAM governs at Meridian, who leads the team, and the six core constructs before lifecycle jargon.
- You oriented on IIQ’s four surfaces and Meridian’s lab URL/credentials.
- You inspected an identity cube, confirmed objects are XML-backed, and filed HR personas for later labs.

---

**Previous:** —  
**Next:** [Lesson 02 — Meridian Org Model & Risk Language](02-meridian-org-model.md)
