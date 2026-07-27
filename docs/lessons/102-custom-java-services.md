# Lesson 102 — Custom Java Services

**Level:** Advanced  
**Track:** Plugins, APIs & SSD  
**Time:** 90–120 min  
**Prereq:** Lesson 101 — SSB/SSD Promotion Discipline; Beanshell vs Java (Lesson 90 concepts)  

**Lab data:**
- Repo: `src/` tree; `pluginsrc/*/manifest.xml` `serviceExecutors`
- `lab-data/connectors/rules/README.md`

---

## Learning objectives

You will be able to:

- Decide when Meridian logic belongs in a **Rule (BeanShell)**, **compiled Java**, **RequestProcessor/workflow library**, or **Service**
- Locate where custom Java lives in SSD (`src/`) vs plugin `serviceExecutors`
- Design `MNB-Service-SoD-Watch`: a safe periodic ops check with kill switch and no secrets
- Document idempotency, logging, and failure handling for bank-grade jobs
- Wire the design to capabilities and AuditConfig events (Lessons 96, 104)
- Apply a code-review checklist that an examiner would accept for privileged custom code

---

## Why this matters

**Business.** BeanShell is fine for small field values — `displayName = first + " " + last`. It is a liability for multi-step banking integrations. When Meridian needed a nightly orphan report and someone stuffed HTTP calls into a BeforeProvisioning BeanShell rule, the rule became untestable, unreviewable, and intermittently timed out during wire-adjacent provisioning for `priya.wire`. Compiled services give typing, unit tests, and code review.

**Control / audit.** Custom executables are production code. They need owners, versions, unit tests, and a kill switch (`enabled=false`). Examiners ask *"what custom code runs on a schedule inside IIQ, and how do you stop it?"* — not “we have some rules.” Silent auto-mitigation of SoD violations is especially forbidden: mitigation is a human/risk decision owned by `MNB-WG-Risk-Review`.

---

## Concepts

### Extension-point cheat sheet

| Pattern | Runs when | Meridian fit |
| --- | --- | --- |
| BeanShell Rule | Hook points (BuildMap, BeforeProv, …) | Quick transforms; see rules README |
| Java Rule / library in `src/` | Same hooks, compiled | Complex correlation, SoD helpers |
| Request / workflow library | LCM steps | Custom approvals, ticket open |
| **Service** (`serviceExecutors`) | Scheduled / interval inside IIQ | Heartbeats, queue drains, watch jobs |
| Plugin REST | On HTTP call | Interactive toolkit (Lesson 98) |

### BeanShell escape criteria (Meridian)

Move to compiled Java when any apply:

- Rule exceeds ~80–100 lines or nested loops over identities
- Outbound HTTP/DB beyond SailPoint context helpers
- Needs unit tests for SoD/payment logic
- Multiple applications share the same helper
- Performance-sensitive correlation

Keep BeanShell for trivial FieldValue defaults and one-line maps (Lesson 94 ticket prefix is fine).

### Idempotency

If the service runs twice, Meridian must not double-create tickets or double-provision. Use natural keys (`identityName` + `businessDate`, or `controlId` + calendar hour for notifications).

### The SoD watch — read-only by design

`MNB-Service-SoD-Watch` counts open policy violations for `MNB-SOD-*`. If above threshold, log WARN and optionally email `helen.ross@meridiannb.com`. **Non-goals:** auto-mitigate, auto-revoke. Daemons that silently “fix” SoD create auditor nightmares — and bypass `MNB-WG-Risk-Review`.

### Real-life Meridian example

A well-meaning engineer added “auto-close low-risk SoD” in a Workflow rule. It closed a Wire dual-control violation for a contractor before Risk reviewed. The finding wrote itself. Meridian’s answer: watch and alert only; humans mitigate.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| HTTP in BeforeProv BeanShell | Timeouts; no tests; retries double-fire | `MnbTicketClient` in `src/` |
| Secrets in class constants | Leak in WAR / git | IIQ encrypted config / vault |
| No kill switch | Cannot stop a runaway job | `enabled=false` still loads |
| Service runs as spadmin password | Credential sprawl | Least-privilege service principal |

---

## How it works

```
  Timer / Service execute()
        │
        ▼
  Read config (enabled, threshold, mailTo, filterPrefix)
        │
        ├── enabled=false → no-op (kill switch)
        │
        ▼
  Idempotent work unit (keyed by date/id)
        │
        ├── success → audit MNB_SOD_WATCH_RUN + metrics
        └── fail  → log + bounded retry + alert (no crash loop)
```

| Concern | Meridian contract |
| --- | --- |
| Config keys | `enabled`, `threshold`, `mailTo`, `filterPrefix=MNB-SOD-` |
| Secrets | Mail host creds from IIQ email config / vault — never class constants |
| Log fields | `service`, `violationCount`, `threshold`, `correlationId`, `result` |
| Audit action | `MNB_SOD_WATCH_RUN` (enable in AuditConfig — Lesson 104) |
| Rights | Least-privilege service principal — not `spadmin` password in code |
| Owner | `helen.ross` / `MNB-WG-IAM-Ops` |

**Registration:** Plugin manifests expose `serviceExecutors` (see empty list in study plugins such as `SWECertificationsAddins`). Example FQCN: `com.meridiannb.iiq.service.MnbSodWatchService`. Classes in `src/` must compile into the SSB WAR (Lesson 101).

---

## Real-world setup (custom services in production)

### Step 1 — Choose the extension point

1. Classify the need (Task 1 table) before writing code.
2. Prefer workflow library for LCM side-effects; prefer Service for interval watchers; prefer REST for interactive ops.

### Step 2 — Config-driven everything

1. Intervals, thresholds, and mail targets live in Configuration / plugin settings — not hardcoded.
2. Kill switch `enabled=false` must stop work while still allowing the service to load (so ops can prove it is installed but dormant).

### Step 3 — Promote via SSB

1. Java under `src/` → `./build.sh clean war` → deploy (Lesson 101).
2. Plugin-bound executors → plugin version bump + bake (Lesson 98).
3. Unit tests for threshold logic in `src/test` when the project supports it.

### Step 4 — Observability before go-live

1. Named audit action + structured logs without PII dumps.
2. Alert route to `MNB-WG-IAM-Ops` / `helen.ross`.
3. Code review checklist: no secrets, idempotent keys, bounded timeout/retry, feature flag.

---

## Before you start

- [ ] SSD `src/` present
- [ ] Lesson 98 plugin scaffold optional reference for `serviceExecutors`
- [ ] JDK available for compile **or** design-only acceptance
- [ ] Agree lab scope: count open SoD violations and log — **read-only**
- [ ] Lesson 101 promotion path understood for Java changes

---

## Lab procedure

### Task 1 — Classify five Meridian needs

Wrong extension points create unmaintainable banks. Classify first.

1. For each need, pick pattern (Rule / Java / Service / REST):
   - DisplayName formatting
   - BeforeProvisioning AD OU placement
   - Nightly orphan account report kickoff
   - Toolkit ping
   - ITSM ticket on leaver
2. Write choices in a table with one-line rationale.

**Expected result:** Classification table of five rows.

### Task 2 — Inspect serviceExecutors placeholder

1. Open `pluginsrc/SWECertificationsAddins/manifest.xml` (or another study plugin with `serviceExecutors`).
2. Note empty `serviceExecutors` list — extension point for services.
3. Document how you would register `com.meridiannb.iiq.service.MnbSodWatchService`.

**Expected result:** Registration note with FQCN example.

### Task 3 — Design MNB SoD watch service (paper + stub)

1. Name: `MNB-Service-SoD-Watch`.
2. Interval: every 15 minutes lab / hourly prod (config-driven).
3. Behavior: query open policy violations for `MNB-SOD-*`; if above threshold, log WARN and optionally email `helen.ross@meridiannb.com`.
4. Non-goals: auto-mitigate, auto-revoke — state this in the class Javadoc / design doc.
5. Create stub class under `src/` **or** binder pseudo-code with method signatures (`execute()`, `countOpenViolations()`, `maybeAlert()`).

**Expected result:** Design doc + stub/pseudo-code.

**If it fails:** Pseudo-code alone is acceptable if compile classpath blocked.

### Task 4 — Config & secrets

1. List config keys: `enabled`, `threshold`, `mailTo`, `filterPrefix=MNB-SOD-`.
2. State: mail host credentials come from IIQ email config / secrets — not class constants.
3. Add kill switch: `enabled=false` stops work but service can still load.
4. Record who can flip the switch: `MNB-WG-IAM-Ops` via Configuration — not every developer.

**Expected result:** Config key table with kill switch and owner.

### Task 5 — Observability contract

1. Define log fields: `service`, `violationCount`, `threshold`, `correlationId`, `result`.
2. Define audit action name: `MNB_SOD_WATCH_RUN`.
3. Forbid logging full SSN, account numbers, or wire amounts.
4. Note Lesson 104 will enable AuditConfig for custom actions if supported.

**Expected result:** Observability contract half-page.

### Task 6 — Test plan

1. Unit: threshold breach true/false.
2. Integration: empty violations → no WARN spam.
3. Failure: DB exception → logged, no crash loop without backoff.
4. Security: runs under service account rights; no `spadmin` password in code.
5. Idempotency: two runs in same hour → one alert key.

**Expected result:** Test plan with five cases.

### Task 7 — RequestProcessor / workflow library sketch

LCM should call libraries — not raw HTTP in BeanShell.

1. Name library class `MnbTicketClient` under `src/` (stub).
2. Methods: `openLeaverTicket(identityName)`, `openSoDExceptionTicket(...)`.
3. Document that LCM workflows (Lesson 93) call the library.
4. Tie secrets to encrypted IIQ config attributes.
5. Run code review checklist: no hardcoded passwords/URLs; idempotent keys; logging without PII; bounded timeout/retry; enabled gate.

**Expected result:** Stub + workflow call notes + checklist pass.

### Task 8 — Examiner question drill

*"What custom code runs on a schedule inside IIQ, and how do you stop it?"*

Write the three-artifact answer: (1) service design + FQCN / manifest registration note, (2) config showing `enabled` kill switch, (3) audit/log contract for `MNB_SOD_WATCH_RUN` plus SSB promotion path for the class.

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Five-need classification table complete
- [ ] serviceExecutors extension point understood
- [ ] `MNB-Service-SoD-Watch` design + stub/pseudo-code
- [ ] Config keys + kill switch documented
- [ ] Observability + audit action named
- [ ] Test plan written; code review checklist applied; no secrets in source
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Service never runs | Not registered / disabled | manifest `serviceExecutors` + enable flag |
| Duplicate emails | Non-idempotent notify | Dedupe by calendar hour key |
| ClassNotFound | Not in WAR | Ensure `src/` compiled into SSB war |
| BeanShell still used | Habit | Schedule refactor when rule > ~100 lines or I/O |
| Runs as god rights | Wrong service identity | Least privilege service principal |
| Auto-mitigate creep | Scope creep in PR | Reject in review — Risk owns mitigate |

---

## Training binder evidence

- Classification table
- Service design page
- Stub path or pseudo-code
- Config + kill switch table
- Test plan + code review checklist
- Examiner proof steps

---

## Knowledge check

1. When do you prefer compiled Java over BeanShell?
2. What is a Service’s scheduling role vs a Task?
3. Why does SoD watch refuse to auto-mitigate?
4. Where is custom Java placed in SSD?
5. Name one idempotency key strategy.
6. What does the kill switch `enabled=false` guarantee?

### Answers

1. Complexity, I/O, testability, code review — banking-grade logic.
2. Services are continuous/interval executors inside the server; Tasks are typically operator/CI scheduled jobs (keep one owner pattern).
3. Mitigation is a human/risk control decision (`MNB-WG-Risk-Review`), not a silent daemon.
4. `src/` (and plugin src for plugin-bound executors).
5. `businessDate + controlId` or `identityName + entitlement + day`.
6. Work stops while the service can still load — ops can prove installed-but-dormant.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “services” / “RequestProcessor” / “custom Java” for your version’s extension points.
- [lab-data/connectors/rules/README.md](../../lab-data/connectors/rules/README.md) — Meridian rule-type cheat sheet and when to escape BeanShell.
- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/) — review practices for privileged custom code.
- [NIST SP 800-53 Rev. 5 — SI-2 / CM-7](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — flaw remediation and least functionality for platform services.
- [FFIEC IT Handbook — Architecture, Infrastructure, and Operations](https://ithandbook.ffiec.gov/) — operational expectations for scheduled jobs and change control in banks.

---

## Stretch lab

Add a JUnit outline for threshold logic under `src/test` if the project supports it. Then map `MNB_SOD_WATCH_RUN` into the AuditConfig design you will enable in Lesson 104. Draft the CAB blurb: “read-only SoD watch; no auto-mitigate.”

---

## Summary

- Choose the right extension point; escalate to compiled services for real ops loops.
- Kill switches, idempotency, and audit names are mandatory — no silent SoD auto-fix.
- Promote Java through SSB like any other Meridian artifact.

---

**Previous:** [Lesson 101 — SSB/SSD Promotion Discipline](101-ssb-ssd-promotion-discipline.md)  
**Next:** [Lesson 103 — UI Customization & Branding](103-ui-customization-branding.md)
