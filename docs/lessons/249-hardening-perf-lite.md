# Lesson 249 — Hardening & Perf Lite

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lessons 206, 233, 245, 248  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 105–109

> **Why:** Sandbox still teaches production muscles: least privilege and task hygiene. Capability sprawl and unpartitioned heavy jobs are exactly what a pre-production review flags before sign-off.

## What this is

Across Lessons 201–248 the estate accumulates cruft: debug capabilities, overlapping schedules, demo logins as `spadmin`, and aggregations never reviewed for partitioning. This lesson is a **hardening checklist with concrete IIQ settings to open and verify** — not a essay about security culture.

You will:

1. Audit persona capabilities (tie back to Lesson 245)  
2. Verify login / session / password / audit settings in Global Settings  
3. Decide partitioning on the heaviest aggregation (classic 105 light)  
4. Stagger schedules and read Task Result durations  
5. Confirm `spadmin` is break-glass only in notes  
6. Leave a least-privilege + perf hygiene pack for Capstone 250  

| Check | “Clean” looks like |
| --- | --- |
| Capability sprawl | Every right traces to a lesson / workgroup |
| Session / login | Timeout and lockout values recorded (not left unknown) |
| Password policy | Policy object exists; min length / history noted |
| Audit | Login and privilege-relevant events on |
| Partitioning | On for heavy agg **or** one written sentence why not |
| Schedules | Heavy jobs not identical cron start |

- **Wrong way:** Leaving `SystemAdministrator` on Priya “from debugging.”  
- **Wrong way:** Claiming partitioning is fine without opening the Task Definition.  
- **Wrong way:** Paper policy with no IIQ screenshot/path.  

## Know these

```text
Inventory capabilities on helen / priya / marcus / christopher (+ workgroups)
  → Strip unjustified direct grants; re-prove 245 deny Global Settings
  → Verify Global Settings: login lockout, session timeout, SMTP still Mailpit
  → Verify Password Policy + AuditConfig (login / capability changes)
  → Heaviest aggregation → Partitioning decision + Task Result sample
  → Stagger overlapping schedules
  → spadmin hygiene note (lab default password NEVER outside Docker)
  → hardening-summary.txt for Capstone 250
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Partitioning** | Split aggregation work across threads/hosts | Account Aggregation option on large app |
| **Schedule contention** | Two heavy jobs start together | Workday agg + full Refresh same minute |
| **Break-glass admin** | `spadmin` only for emergency/bootstrap | Day-2 ops as Helen / workgroup personas |
| **AuditConfig** | What IIQ writes to audit search | Login, capability assign |
| **Session timeout** | Idle logout window | Global Settings login/session |

## Intent

- Strip unjustified capabilities without breaking Lesson 245 certifier proof.  
- Record concrete values for login, session, password, and audit settings.  
- Make and justify one partitioning decision on a real Task Definition.  
- Remove at least one schedule collision (or document none found).  
- Hand Capstone 250 a hardening summary that cites IIQ paths.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] Lesson 245 workgroup `MNB-WG-Wire-Owners` exists **or** recreate it before auditing Priya
- [ ] Lesson 233 aggregation runbook idea remembered (which app is heaviest)
- [ ] You can open **Monitor → Tasks → Task Results** and **Gear → Global Settings**
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/249
```

## Do this

### Task 1 — Capability inventory (personas + workgroups)

As `spadmin`, for each identity below open **Identities → Identity Warehouse → {name} → Capabilities** (and note workgroup memberships):

| Identity | Role in lab | Expected pattern |
| --- | --- | --- |
| `helen.ross` | IAM / day-2 ops | Elevated but **not** casual SystemAdministrator unless justified |
| `priya.wire` | Wire certifier | Certifier via **`MNB-WG-Wire-Owners`**, no direct SystemAdministrator |
| `marcus.approve` | Approver persona | Approval-related only |
| `christopher.hayes` | Manager / certifier as used | No leftover full admin |
| `spadmin` | Break-glass | SystemAdministrator **expected** — document as break-glass only |

Also open **Setup → Workgroups → MNB-WG-Wire-Owners** and list capabilities on the **workgroup** (not only the identity).

Write `capability-inventory.txt`:

```text
identity | direct capabilities | workgroups | keep? (lesson ref) | strip?
---------|---------------------|------------|--------------------|-------
priya.wire | … | MNB-WG-Wire-Owners | 245 certifier | …
```

- **Why:** you cannot harden what you have not listed.  
- **Expect:** a filled table before any strip.

### Task 2 — Strip unjustified grants + re-prove Lesson 245

1. For each **strip?** row, remove the direct capability on the identity  
2. Prefer fixing membership (add/remove workgroup) over stacking new direct grants  
3. Re-login as `priya.wire`:
   - Certifications **still** opens  
   - Global Settings **still** denied (same URL as Lesson 245)  
4. Screenshot deny → `priya-still-denied.png`

- **Why:** cleanup that breaks the certifier model is not hardening.  
- **Expect:** 245 proof still holds after strips.

### Task 3 — Login & session settings (concrete IIQ paths)

As `spadmin` open **Gear → Global Settings** (IdentityIQ Configuration / Login Configuration — labels vary).

Find and record **actual values** (screenshot each pane you touch):

| Setting to find | Where to look | Record |
| --- | --- | --- |
| **Session timeout** / idle timeout | Global Settings → Login / Misc / IdentityIQ Configuration | minutes = ___ |
| **Failed login lockout** / max failures | Login Configuration | threshold = ___ ; lock duration = ___ |
| **Remember me / persistent login** | Login Configuration | on/off = ___ |
| **SSO / SAML/OIDC** still pointing at lab IdP if used | SSO / Login | IdP = ___ |

Write under `login-session-settings.txt`. If a control is missing on this build, write `NOT FOUND IN UI — residual risk RR-MNB-SESSION-UI`.

Lab guidance (not automatic prod values):

- Prefer a **finite** session timeout (know the number; do not leave “unknown”).  
- Lockout should be **on** with a recorded threshold for the lab story.  
- Do **not** weaken lockout to “make demos easier” without noting it as temporary.

- **Why:** examiners ask for the number, not “we hardened sessions.”  
- **Expect:** file with concrete numbers or explicit NOT FOUND.

### Task 4 — Password policy verify

1. **Setup → Password Policies** (or Gear → Global Settings → Passwords)  
2. Open the policy applied to IIQ users / pass-through (name varies — often Default or Meridian lab policy)  
3. Record:

| Field | Value |
| --- | --- |
| Policy name | ___ |
| Min length | ___ |
| History / reuse | ___ |
| Complexity (upper/lower/digit/special) | ___ |
| Check passwords against identity attributes | on/off |

4. Screenshot → `password-policy.png`  
5. Confirm personas still use lab password `LabUser1!` **only** inside this Docker estate — note that production would forbid shared demo passwords

- **Why:** capability hardening with `Password1` everywhere is unfinished.  
- **Expect:** policy object opened and values written — create a minimal policy if none exists:

If **no** policy exists: **Setup → Password Policies → Create**, name `MNB-PasswordPolicy-Lab`, set min length ≥ 8 with mixed character classes, assign to the IIQ application / identity type your UI requires, save, then record values.

### Task 5 — AuditConfig: login & privilege events

1. **Gear → Global Settings → Audit** / **Debug → AuditConfig** (path varies)  
2. Confirm auditing is enabled for at least:
   - **Login** / authentication success & failure (names vary)  
   - **Capability** or **Workgroup** membership changes if listed  
3. Generate one proof event: log out → log in as `spadmin` once  
4. **Intelligence → Advanced Analytics → Audit** (or **Monitor → Audit**) → search recent Login for `spadmin`  
5. Save result id / screenshot → `audit-login-spadmin.png`

If audit classes are off: enable the login-related class, save AuditConfig, retry login, re-search.

- **Why:** least privilege without audit is unverifiable.  
- **Expect:** one visible login audit row for this session.

### Task 6 — SMTP / Mailpit still the lab relay (hygiene)

1. **Gear → Global Settings → Mail Settings** (SMTP)  
2. Confirm host/port still lab Mailpit (`mailpit` / `localhost` style host, port **1025** inside Docker — Lesson 203 pattern)  
3. Record host, port, from-address in `mail-settings.txt`  
4. Open [http://localhost:8025](http://localhost:8025) — prove catcher still up  

- **Why:** a “hardened” lab that emails the public internet is a different incident class.  
- **Expect:** Mail settings point at the lab catcher, not an external ISP.

### Task 7 — Heaviest aggregation: partitioning decision

1. From Lesson 233 notes (or Task Results durations), pick the heaviest aggregation — usually **`MNB-Workday`** or the app with the most accounts  
2. **Setup → Tasks** → open that **Account Aggregation** (or app-specific) **Task Definition**  
3. Locate **Partitioning** / concurrent / thread options (connector-specific)  
4. Do **one**:
   - **Enable** partitioning / raise threads modestly and **Save**, **or**  
   - Leave off and write why (dataset too small; connector lacks support; single-node lab)  
5. Run the task once → open **Task Result** → record duration, accounts scanned, errors, result id  

Write `partitioning-decision.txt`:

```text
Task: ________
Application: ________
Partitioning before: ________
Partitioning after / decision: ________
Justification: ________
Task Result id: ________
Duration: ________
```

- **Why:** classic 105 — throughput decisions belong on the Task Definition, not in chat.  
- **Expect:** decision file + result id (even if “leave off — N accounts”).

> **Watch out:** Greyed-out partitioning usually means the connector does not support it — document filter/OU split as the prod alternative; do not force a nonexistent checkbox.

### Task 8 — Schedule contention review

1. **Setup → Tasks → Scheduled Tasks** (or Schedules)  
2. List heavy jobs: Workday aggregation, directory aggregation, Refresh Identity Cube, cert scans if scheduled  
3. Find any two with the **same** start minute  
4. Edit **one** schedule to stagger (e.g. +15 minutes) **or** write `No identical heavy starts found` with the table of start times  
5. Save `schedules.txt` with before/after  

- **Why:** overlapping full aggs + refresh create false “IIQ is down” pages.  
- **Expect:** at least one stagger change **or** an explicit no-collision table.

### Task 9 — Hosts / server inventory (105 light)

1. **Gear → Administrator Console → Hosts** / **Servers** (or Debug → `Server`)  
2. Record hostname, roles if shown, last heartbeat  
3. Single-node note (expected in lab):

```text
Hosts: 1 (lab). Prod intent: UI pool vs task pool; pin heavy agg to task host.
```

- **Why:** partitioning without knowing the host story is incomplete.  
- **Expect:** one-row inventory + prod intent sentence.

### Task 10 — `spadmin` hygiene note

Write `spadmin-hygiene.txt`:

```text
spadmin password in this Docker lab: admin (DEFAULT — throwaway stack only)
Allowed uses: bootstrap, lesson setup, break-glass drill
Forbidden: day-2 cert decisions, routine Request Access demos, Gitea “admin” habit
Day-2 personas: helen.ross, workgroup certifiers (245), managers for approvals
MFA for admin: ________ (configured / NOT in lab → residual RR-MNB-MFA-ADMIN)
```

Optionally search your recent evidence folders for portal demos done only as `spadmin` where a persona exists — redo one check as Helen if you find a clear miss.

- **Why:** classic 109 — standing shared admin is the anti-pattern.  
- **Expect:** hygiene file saved; residual MFA risk named if no MFA.

### Task 11 — Hardening summary for Capstone 250

Create `~/iiq-lab-evidence/sandbox/249/hardening-summary.txt`:

```text
Capabilities stripped: ________
245 proof re-verified: yes/no
Session timeout (minutes): ________
Lockout threshold: ________
Password policy: ________
Audit login proof: yes/no (result/screenshot)
Mail host:port: ________
Partitioning decision: ________
Schedule change: ________
Host inventory: ________
Residuals: RR-MNB-… ________
```

- **Why:** Capstone 250 should not rediscover your hardening state.  
- **Expect:** one summary file citing the settings you actually opened.

## If it fails

| Symptom | Fix |
| --- | --- |
| Stripping a capability breaks Priya certs | Re-add **only** via `MNB-WG-Wire-Owners`, not SystemAdministrator |
| Cannot find session timeout | Record NOT FOUND + residual id; check IdentityIQ Configuration tabs thoroughly |
| Password Policies menu missing | Debug → `PasswordPolicy` object; or create via Setup if available |
| No audit rows | Enable AuditConfig login class; retry login; widen time filter |
| Partitioning greyed out | Document connector limitation + OU/filter prod strategy |
| Schedule edit will not save | Check cron fields; avoid impossible day/hour combos |
| Mail settings point elsewhere | Reset to Mailpit per Lesson 203 before Capstone |

## You are done when

- [ ] Capability inventory + unjustified strips done; 245 deny proof still true  
- [ ] Login/session, password policy, AuditConfig, and Mail settings **values recorded** from IIQ  
- [ ] One partitioning decision documented against a real Task Definition + Task Result  
- [ ] Schedule collision fixed or explicitly cleared  
- [ ] `spadmin-hygiene.txt` + `hardening-summary.txt` saved under evidence  

## Control note

- **Control:** Pre-production hardening pass (least privilege + session/password/audit + task hygiene)  
- **Owner:** IAM Engineering  
- **SLA (lab):** Zero unjustified persona admin rights; heaviest task partitioning decision documented; login audit provable  
- **Evidence:** `~/iiq-lab-evidence/sandbox/249/`  
- **Out of scope:** Multi-node production cluster build-out; real SOC SIEM onboarding  

## Quick check

1. What must every persona capability trace to? → A lesson requirement or workgroup design  
2. Which Global Settings prove session hygiene? → Recorded timeout (+ lockout threshold)  
3. Acceptable reason to skip partitioning? → Dataset tiny or connector unsupported — **written** on the Task Definition note  
4. Why audit login as `spadmin` in this lesson? → Prove AuditConfig actually records privileged auth  
5. Is `spadmin`/`admin` OK outside Docker lab? → **No** — lab default only  

## Feedback

Could you run this hardening checklist on a fresh notes folder (capabilities → Global Settings values → password/audit/mail → partitioning → schedules → summary) without this page?

If something failed, note the **task number**, the IIQ path you opened, and the value you expected vs saw.

## Navigate

- Previous: [Lesson 248](248-ssd-promote-live.md)
- Next: [Lesson 250](250-capstone-bank-day.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
