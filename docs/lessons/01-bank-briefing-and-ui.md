# Lesson 01 — Bank Briefing & UI Orientation

**Level:** Absolute beginner  
**Prereq:** Working local IIQ login ([LOCAL_SETUP.md](../LOCAL_SETUP.md))  
**Meridian story:** Day one on the IAM team. Before connecting systems, you learn how IdentityIQ is organized and how MNB will use it.

---

## Story

Meridian National Bank just bought IdentityIQ. Leadership wants:

- Faster employee onboarding
- Fewer orphan accounts after exits
- Evidence for audits (who had access, who approved it)

Your first job is not configuration—it is **orientation**. If you cannot find Identities, Applications, Tasks, and Work Items, every later lesson will feel random.

---

## How it works

IdentityIQ is a web app with:

1. **Configuration objects** (Applications, Roles, Policies, Workflows) stored in the DB  
2. **Operational data** (Identities, Accounts, Certifications, Work Items)  
3. **Tasks** that run jobs (aggregate, refresh, certify)  
4. **Inboxes** where humans approve or review

You mostly wear three hats:

| Hat | Typical actions |
| --- | --- |
| Admin (`spadmin`) | Build apps, roles, tasks, policies |
| Manager | Approve requests, complete certifications |
| End user | Request access (later lessons) |

---

## Lesson goals

- [ ] Log in as `spadmin`
- [ ] Locate Identities, Applications, Tasks, and Work Items areas
- [ ] Open Debug / console awareness (where XML lives)
- [ ] Write a one-paragraph “what IIQ will do for MNB” note for yourself

---

## Tasks

### Task 1 — Login

1. Start Tomcat if needed.  
2. Open `http://localhost:8080/identityiq`.  
3. Login: `spadmin` / `admin`.  
4. Change password if prompted / if the box is shared.

### Task 2 — Tour the home experience

1. Note the Quicklinks / menu items available.  
2. Open **Identities** (or Identity Warehouse / Identity search—label varies).  
3. Search for `spadmin` and open the identity.  
4. Click through tabs that show attributes, detected roles, assigned roles, accounts, work items, risk—whatever is present.

**What you’re learning:** An identity is a *cube* of everything IIQ knows about a person.

### Task 3 — Find Applications & Tasks

1. Open **Applications** (often under Setup / Define). Confirm the list loads (may be empty or mostly defaults).  
2. Open **Tasks**. Note that tasks are how IIQ *does work* in the background.  
3. Do **not** run random tasks yet—just observe names and last run info if any.

### Task 4 — Work items awareness

1. Open your **Work Item Inbox** / Home work items.  
2. It is probably empty. That is normal.  
3. Remember this screen—Lessons 08 and 10 fill it up.

### Task 5 — Admin / Debug awareness

1. Find **Debug** (gear / Administrator console / Debug pages—depends on UI).  
2. Browse object types: `Application`, `Identity`, `TaskDefinition`, `Bundle`, `Workflow`.  
3. Open any object and notice it is XML under the hood.

**Tip:** Debug is powerful and dangerous. In a lab, explore freely. In production, treat it like production SQL.

### Task 6 — Skim lab data (outside IIQ)

Open in an editor:

- `~/iiq-lab-data/HRApplications.txt`
- `~/iiq-lab-data/EmployeeData.txt`
- repo `email.txt`

Answer on paper:

1. Who looks like a top-level manager in HR data (empty `managerId`)?  
2. Which `itAccess` values appear most often?  
3. What kind of email does a manager get during certifications?

---

## Tips & tricks

- Keep a lab notebook (or markdown file) of object names you create (`MNB-HR`, `Aggregate MNB-HR`, etc.). Consistency saves hours.  
- Prefer searching inside IIQ over memorizing every menu path.  
- If the UI feels empty: you have not imported `init-lcm.xml` yet, or Lifecycle features are inactive—see LOCAL_SETUP Step 5 optional.

---

## Checkpoint

You should be able to answer without looking:

1. What URL and user do you use for admin?  
2. What is an Identity Cube in one sentence?  
3. Which file will be the authoritative HR source for Meridian?

---

## Stretch

- Export the `spadmin` identity from Debug as XML and skim it.  
- Read the first 10 pages of `identityiq-8.5/doc/8.5_IdentityIQ_Getting_Started.pdf`.

**Next:** [Lesson 02 — Authoritative HR source](02-authoritative-hr-source.md)
