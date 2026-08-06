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

- Explain what Identity and Access Management (IAM) does at a bank and where you sit on Meridian's team
- Define six core IAM building blocks in plain English: identity, account, entitlement, application, role, policy
- Log in to IdentityIQ as `spadmin` and recognize lab-vs-production cues
- Navigate Identities, Applications, Tasks, Work Items, and Debug without guessing
- Explain what an **identity cube** and a **work item** are
- Locate Meridian's HR and IT files and name at least six scripted personas by heart

## Why this matters

You just joined Meridian National Bank's Identity & Access team. Your manager will not start you on joiner workflows or SoD policy on day one — they will walk you through who owns what, what problem IIQ solves, and how to find things in the console without breaking anything. That is this lesson. Orientation first; lifecycle automation comes later (Lesson 29+), once you understand people, apps, and access language.

When an internal reviewer asks "who operates the governance console, and how do you find an identity or a job result?", your answer should be muscle memory, not a Slack search. Day-one navigation is the first control-hygiene habit Meridian expects from every new IAM engineer.

## Concepts

### 1. What IAM is — and is not

**Identity and Access Management (IAM)** makes sure the right people have the right access to the right systems, for the right reason, and can prove it later. Meridian bought **SailPoint IdentityIQ (IIQ)** as the governance platform. IIQ does **not** replace Active Directory, SAP, or the wire portal — it connects to those systems, builds a picture of each person's access, and runs the processes (approvals, reviews, policies) that Risk and internal audit expect.

| Question a reviewer asks | What IAM must show |
| --- | --- |
| Who works here? | A reliable list of people from HR |
| What can they do in systems? | Accounts and entitlements tied to those people |
| Who approved that access? | Approvals, certifications, or documented exceptions |
| What happens when someone leaves? | Access removed or disabled on a known timeline |

IAM is **not** the help desk resetting passwords, and it is **not** the firewall team. Those teams partner with you; your job is **identity governance** — knowing who someone is, what they have, and whether that access is still appropriate.

### 2. Your team and who you work with

You are an **IAM Engineer** on the Identity Governance squad under Information Security (`SEC`). "IAM Ops," "IGA," and "Identity" all refer to the same group in hallway talk.

```text
Helen Ross (helen.ross) — Head of Identity & Access
        │
        ├── IAM Engineering  ← you (design roles, apps, policies, workflows)
        ├── IAM Operations   (run scheduled jobs, triage failures, handle tickets)
        └── IAM Governance   (cert campaigns, policy exceptions, evidence)

Partners: HR Operations (people data) · App/system owners (entitlements)
          Risk & Compliance (SoD, exam readiness) · Technology (directories, infra)
```

| Person | userId | Owns | Why it matters to you |
| --- | --- | --- | --- |
| helen.ross | MNB00001 | Head of Identity & Access | Your leadership; IAM platform owner |
| christopher.hayes | MNB00002 | Director of Technology | Cloud / directory platforms |
| deepa.nair | MNB00003 | Director of Finance | SAP finance entitlements |
| anthony.powell | MNB00004 | Risk leadership | Partner on toxic-access (SoD) design |
| rachel.evans | MNB00005 | Payments / wire owner | Wire initiate vs approve entitlements |
| daniel.griffin | MNB00008 | Operations | Core banking access |

You will not configure those platforms yourself on day one — you **govern** access to them in IIQ, with those people as control owners.

### 3. Core constructs — learn these six words first

Ignore product buzzwords until these are solid. Everything else hangs on them.

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Identity** | A person (or service) Meridian tracks as "one worker" | `priya.wire` — Priya in Treasury |
| **Account** | A login on one system | Priya's Wire Portal username |
| **Entitlement** | A permission or group on that system | `WIRE_INIT` — can create a wire |
| **Application** | An IIQ definition of a connected system | Later: `MNB-Wire-Portal` |
| **Role** | A package of entitlements assigned for a job | "Wire Specialist birthright" (Lesson 24+) |
| **Policy** | A rule that flags bad access combinations | "Nobody holds both initiate and approve" (Lesson 39+) |

Two more terms in the UI today: an **identity cube** is IIQ's person-centric record — HR attributes + accounts + roles + risk + open work, all in one place; you govern *people*, not spreadsheet rows. A **work item** is a human decision waiting in someone's Inbox (approve access, certify access, remediate a violation).

> **Watch out:** Beginners assume "IIQ is the directory where people log in." Wrong — Active Directory (and peers) is where people authenticate. IIQ is where Meridian **governs and proves** access across many systems.

### 4. The four surfaces you use every day

| Surface | What it holds | Meridian habit |
| --- | --- | --- |
| **Configuration** | Applications, roles, policies, workflows | Names start with `MNB-` |
| **Operational data** | Identities, accounts (links), certifications | Search people by name, e.g. `helen.ross` |
| **Tasks** | Aggregation, refresh, certification jobs | Prefer named tasks (`Aggregate MNB-HR`) later |
| **Work items** | Human decisions | Bookmark your Inbox on day one, even empty |

```text
[Configure apps/roles/policies] -> [Tasks pull accounts & refresh cubes] -> [Identity cubes]
                                                    |                              |
                                                    v                              v
                                        [Task results / counters]        [Work items for humans]
```

**Corporate context:** email domain `@meridiannb.com`. Lab URL `http://localhost:8080/identityiq`. Default admin `spadmin` / `admin`. Homelab sites may publish a different URL — use what your LOCAL_SETUP documents.

## Before you start

- [ ] Tomcat is running and IIQ responds at `http://localhost:8080/identityiq` (or your documented lab URL)
- [ ] You can log in as `spadmin` / `admin`
- [ ] Repo `lab-data/` exists (copy to `~/iiq-lab-data` if not already done — skimming repo files is fine for this lesson)
- [ ] Notebook ready for glossary + persona cheat sheet

## Lab procedure

### Task 1 — Login and environment hygiene

Treat first login as environment hygiene: confirm you are on the **lab**, not a shared or mislabeled URL, before exploring cubes. In production, wrong-environment logins are incident tickets.

1. Start Tomcat if needed (see LOCAL_SETUP).
2. Open `http://localhost:8080/identityiq` and sign in: **User** `spadmin`, **Password** `admin`.
3. If this is a shared lab, change the password under your user preferences and record the new secret in your local vault — not in git.
4. Note any environment banner, hostname, or database name visible in the UI footer/header.

**Expected result:** Home/dashboard loads without error; you see navigation to Identities / Applications / Tasks (labels vary slightly by IIQ skin).

**If it fails:** Confirm Tomcat logs and that `/identityiq` is the context path; re-check LOCAL_SETUP LCM init import if menus look empty.

### Task 2 — Tour the identity cube

Your staff engineer will say: "Open a cube and click every tab once. You are learning the shape of a person in IIQ."

1. Open **Identities → Identity Warehouse** (or equivalent search) and open `spadmin`.
2. Click through tabs: attributes, accounts/applications, roles/bundles, work items, risk (or equivalent).
3. Complete in your own words: "An identity cube is …"
4. Optional: search for `helen.ross` if she already exists; if not, that is fine — HR aggregation comes in Lesson 04.

**Expected result:** You can describe at least three tabs and see that a cube aggregates person + access + workflow state.

### Task 3 — Applications and Tasks map (look only)

Applications are "systems IIQ knows about." Tasks are "jobs that move data or run campaigns." Today you only look.

1. Open **Applications** (often under Setup / Define Applications) and list stock applications on a fresh install — do not delete any.
2. Open **Tasks** (Monitor / Setup Tasks or equivalent) and scan task types: Account Aggregation, Identity Refresh, Certification. **Do not** run random jobs.

**Expected result:** Notebook lists where Applications live and at least three task type names, with zero destructive runs.

### Task 4 — Work Item Inbox

Approvals and certifications land here. Empty on day one is normal.

1. Open your **Work Item Inbox** (Home → Work Items or equivalent) and confirm it may be empty.
2. Bookmark the URL.

**Expected result:** Inbox opens; you note that Lessons 35–46 will populate real approval/cert decisions here.

### Task 5 — Debug awareness

Debug is the engineer's X-ray: objects are XML under the hood. Look, do not edit randomly.

1. Open **Debug** / Administrator console (gear or Debug menu — path varies by install).
2. Browse object types: `Application`, `Identity`, `TaskDefinition`, `Bundle`, `Workflow`. Open one and confirm the body is XML.

**Expected result:** You can say "IIQ objects are XML under the hood" and name five object types used in later Meridian labs.

**If it fails:** Confirm `spadmin` retains the Debug/SystemAdministrator capability; some locked-down installs hide Debug — use Monitor → Advanced Analytics as a fallback and note the gap.

### Task 6 — Skim Meridian lab data (people files, not IIQ yet)

Before IIQ "knows" Meridian workers, the truth lives in files.

1. From the repo root:

```bash
mkdir -p ~/iiq-lab-data
cp -n lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/ 2>/dev/null || true
ls ~/iiq-lab-data/
```

2. Open `HRApplications.txt`. Find leadership `MNB00001`–`MNB00008` (`helen.ross`, `christopher.hayes`, `deepa.nair`, …).
3. Find scripted personas `MNB00090`–`MNB00097` (`priya.wire`, `marcus.approve`, `jordan.reed`, `raj.external`, `samir.hassan`, `sofia.torres`, `kai.nguyen`, `amelia.brooks`) and `nina.joiner` (`MNB00120`).
4. Skim `lab-data/reference/entitlement-dictionary.csv` — notice codes like `WIRE_INIT` and a **risk** column; you classify risk properly in Lesson 02.

**Expected result:** You can name HR as the people source of truth, the IT dump as entitlement inventory, and at least four scripted usernames without looking them up again.

> **ID map:** HR key = `userId`. The IT dump column `employeeId` uses the **same** `MNB#####` values, so accounts tie back to people later (Lesson 09+).

### Task 7 — One-paragraph "why Meridian runs IIQ"

Write for your manager, not for marketing. In 4–6 sentences, explain why Meridian runs IdentityIQ: knowing who works here, knowing what access they hold, proving reviews/approvals happened, and reducing leftover access when people change jobs or leave. If you use "joiner" or "SoD," define it in the same sentence.

**Expected result:** A paragraph a non-IAM colleague could understand — bank controls, not product slogans.

### Task 8 — Persona cheat sheet (binder)

Copy this starter table into your notebook and keep it for Lessons 04–40:

| Persona | userId (HR) | Why it matters |
| --- | --- | --- |
| helen.ross | MNB00001 | IAM / security leadership |
| christopher.hayes | MNB00002 | Technology / cloud owner |
| deepa.nair | MNB00003 | Finance / SAP owner |
| rachel.evans | MNB00005 | Payments / wire owner |
| daniel.griffin | MNB00008 | Operations |
| priya.wire | MNB00090 | Wire initiate only (`WIRE_INIT`) |
| marcus.approve | MNB00091 | Wire approve only (`WIRE_APPR`) |
| jordan.reed | MNB00092 | Finance + cloud admin (intentional bad combo) |
| raj.external | MNB00093 | Contractor with a bad vendor email |
| samir.hassan | MNB00094 | Terminated + leftover IT access |
| sofia.torres | MNB00095 | On leave (`exceptions=LOA`) |
| kai.nguyen | MNB00096 | Digital support + channel promo (another bad combo) |
| amelia.brooks | MNB00097 | New teller pattern |
| nina.joiner | MNB00120 | New-hire scenario file (Lesson 29) |

**Expected result:** Cheat sheet filed; you can recall the wire pair and leadership names without reopening CSV files.

## Acceptance criteria

- [ ] Can explain IAM vs directories in one or two sentences
- [ ] Can name your team lead and at least three partner owners
- [ ] Can define identity, account, entitlement, application, role, policy without looking them up
- [ ] Logged in as `spadmin` at lab IIQ; cube tour notes completed
- [ ] Applications and Tasks locations recorded; Work Item Inbox bookmarked
- [ ] Debug XML observed (or gap documented)
- [ ] Lab personas `MNB00090`–`MNB00097` recognized; persona cheat sheet filed
- [ ] Value statement written in notebook

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 404 on `/identityiq` | Wrong context or Tomcat down | Check Tomcat webapps and LOCAL_SETUP |
| Empty menus | Incomplete init/LCM import | Re-run init imports from LOCAL_SETUP |
| Cannot open Debug | Capability missing | Confirm `spadmin` has SystemAdministrator |
| Lab files missing | Not copied | Copy from repo `lab-data/` to `~/iiq-lab-data/` |
| Overwhelmed by jargon | Normal on day one | Stick to the six core constructs; park joiner/SoD terms for later lessons |

## Training binder evidence

- Screenshot: successful login / home
- Screenshot: identity cube for `spadmin` (attributes + accounts tabs)
- Screenshot: Tasks list showing Aggregation / Refresh types
- Notebook: team sketch + core-construct glossary + value statement + persona cheat sheet

## Knowledge check

1. What is the default lab URL and admin user?
2. In one sentence, what is an identity cube?
3. What is the difference between an **account** and an **entitlement**?
4. Who is Meridian's Head of Identity & Access?
5. Which file is authoritative for who works at Meridian?
6. Name the two personas used later to show healthy wire dual control.

### Answers

1. `http://localhost:8080/identityiq`; user `spadmin` (password `admin` unless changed).
2. The person-centric IIQ record joining attributes, accounts, roles, risk, and work items.
3. An account is a login on one system; an entitlement is a permission/group that login holds on that system.
4. `helen.ross` (MNB00001).
5. `HRApplications.txt` — not the IT entitlement dump.
6. `priya.wire` (`WIRE_INIT`) and `marcus.approve` (`WIRE_APPR`).

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "identity warehouse" for the UI map and cube concepts.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search "IdentityIQ navigation" for practitioner tips on finding objects and task results.

## Stretch lab

- From Debug, view `spadmin` Identity XML and skim attribute and link sections.
- Draw a one-page Meridian map: Team → Core constructs → Four IIQ surfaces.

## Summary

- You know what IAM governs at Meridian, who leads the team, and the six core constructs before lifecycle jargon.
- You oriented on IIQ's four surfaces and Meridian's lab URL/credentials, and inspected an identity cube.
- You confirmed objects are XML-backed and filed HR personas for later labs.

## Feedback

Could you redo Task 1–5 from memory without this doc open? Note the task number where you got stuck, what you expected the screen to show, and what you actually saw — that gap is exactly what the next revision of this lesson should close.

## Navigate

- Previous: —
- Next: [Lesson 02 — Meridian Org Model & Risk Language](02-meridian-org-model.md)
