# Lesson 102 — Custom Java Services

| Field | Value |
| --- | --- |
| **Level** | Advanced |
| **Track** | Plugins, APIs & SSD |
| **Time** | 75–90 minutes |
| **Prereq** | [Lesson 101 — SSB/SSD Promotion Discipline](101-ssb-ssd-promotion-discipline.md); Beanshell vs Java (catalog Lesson 90 concepts) |
| **Lab data** | `src/` tree; `pluginsrc/*/manifest.xml` `serviceExecutors`; `lab-data/connectors/rules/README.md` |

## Learning objectives

You will be able to:

- Decide when Meridian logic belongs in a **Rule (Beanshell)**, **compiled Rule/Java**, **RequestProcessor**, or **Service**
- Locate where custom Java lives in SSD (`src/`) vs plugin executors
- Sketch a Meridian service that performs a safe periodic ops check (no secrets)
- Document idempotency, logging, and failure handling for bank-grade jobs
- Wire the design to capabilities and AuditConfig events (Lessons 96, 104)

## Why this matters

Beanshell is fine for small field values; it is a liability for multi-step banking integrations. Compiled services give testability, typing, and code review—required when logic touches money movement adjacent systems (wire, core).

**Control / audit:** Custom executables are production code. They need owners, versions, unit tests, and a kill switch (disable service / feature flag).

## Concepts

| Pattern | Runs when | Meridian fit |
| --- | --- | --- |
| Beanshell Rule | Hook points (BuildMap, BeforeProv, …) | Quick transforms; see rules README |
| Java Rule / library in `src/` | Same hooks, compiled | Complex correlation, SoD helpers |
| Request / workflow library | LCM steps | Custom approvals, ticket open |
| **Service** (`serviceExecutors`) | Scheduled / interval inside IIQ | Heartbeats, queue drains, reconciliation helpers |
| Plugin REST | On HTTP call | Interactive toolkit (Lesson 98) |

```text
  Timer / Service execute()
        |
        v
  Read config (encrypted attrs / settings)
        |
        v
  Idempotent work unit (keyed by date/id)
        |
        +-- success --> audit + metrics
        +-- fail -----> log + retry policy + alert
```

**Rule type cheat sheet** (from `lab-data/connectors/rules/README.md`): BuildMap, Correlation, IdentityAttribute, Before/AfterProvisioning, Policy, Workflow, etc. Prefer moving heavy logic from Beanshell to `src/` when cyclomatic complexity or partner I/O grows.

**Idempotency:** If the service runs twice, Meridian must not double-create tickets or double-provision. Use natural keys (`identityName` + `businessDate`).

## Before you start

- [ ] SSD `src/` present (`com` / `sailpoint` packages may already exist)
- [ ] Lesson 98 plugin scaffold optional reference for `serviceExecutors`
- [ ] JDK available for compile **or** design-only acceptance
- [ ] Agree “lab service” scope: e.g., count open SoD violations and log—**read-only**

## Lab procedure

### Task 1 — Classify five Meridian needs

1. For each need, pick pattern (Rule / Java / Service / REST):
   - DisplayName formatting
   - BeforeProvisioning AD OU placement
   - Nightly orphan account report kickoff
   - Toolkit ping
   - ITSM ticket on leaver
2. Write choices in a table with one-line rationale.

**Expected result:** Classification table of five rows.

**If it fails:** Use catalog Lessons 89–94 names; still classify.

### Task 2 — Inspect serviceExecutors placeholder

1. Open `pluginsrc/SWECertificationsAddins/manifest.xml`.
2. Note empty `serviceExecutors` list—extension point for services.
3. Document how you would register `com.meridiannb.iiq.service.MnbSodWatchService` (example name).

**Expected result:** Registration note with FQCN example.

### Task 3 — Design MNB SoD watch service (paper + stub)

1. Name: `MNB-Service-SoD-Watch`.
2. Interval: every 15 minutes lab / hourly prod (config-driven).
3. Behavior: query open policy violations count for `MNB-SOD-*`; if above threshold, log WARN and optionally email `helen.ross@meridiannb.com`.
4. Non-goals: auto-mitigate, auto-revoke.
5. Create stub class under `src/` **or** binder pseudo-code with method signatures.

**Expected result:** Design doc + stub/pseudo-code.

**If it fails:** Pseudo-code alone is acceptable if compile classpath blocked.

### Task 4 — Config & secrets

1. List config keys: `enabled`, `threshold`, `mailTo`, `filterPrefix=MNB-SOD-`.
2. State: mail host credentials come from IIQ email config / secrets—not class constants.
3. Add kill switch: `enabled=false` stops work but service can still load.

**Expected result:** Config key table with kill switch.

### Task 5 — Observability contract

1. Define log fields: `service`, `violationCount`, `threshold`, `correlationId` (if available), `result`.
2. Define audit action name candidate: `MNB_SOD_WATCH_RUN`.
3. Note Lesson 104 will enable AuditConfig for custom actions if supported.

**Expected result:** Observability contract half-page.

### Task 6 — Test plan

1. Unit: threshold breach true/false.
2. Integration: empty violations → no WARN spam.
3. Failure: DB exception → logged, no crash loop without backoff.
4. Security: runs under service account rights; no `spadmin` password in code.

**Expected result:** Test plan with four cases.

## Acceptance criteria

- [ ] Five-need classification table complete
- [ ] serviceExecutors extension point understood
- [ ] `MNB-Service-SoD-Watch` design + stub/pseudo-code
- [ ] Config keys + kill switch documented
- [ ] Observability + audit action named
- [ ] Test plan written; no secrets in source

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Service never runs | Not registered / disabled | manifest serviceExecutors + enable flag |
| Duplicate emails | Non-idempotent notify | Dedupe by calendar hour key |
| ClassNotFound | Not in WAR | Ensure `src/` compiled into SSB war |
| Beanshell still used | Habit | Schedule refactor when rule > ~100 lines or I/O |
| Runs as god rights | Wrong service identity | Least privilege service principal |

## Training binder evidence

- Classification table  
- Service design page  
- Stub path or pseudo-code  
- Test plan  

## Knowledge check

1. When do you prefer compiled Java over Beanshell?
2. What is a Service’s scheduling role vs a Task?
3. Why does SoD watch refuse to auto-mitigate?
4. Where is custom Java placed in SSD?
5. Name one idempotency key strategy.

### Answers

1. Complexity, I/O, testability, code review—banking-grade logic.  
2. Services are continuous/interval executors inside the server; Tasks are typically operator/CI scheduled jobs (both can schedule—pick per platform norms and keep one owner pattern).  
3. Mitigation is a human/risk control decision, not a silent daemon.  
4. `src/` (and plugin src for plugin-bound executors).  
5. `businessDate + controlId` or `identityName + entitlement + day`.

## Stretch lab

Add unit-test outline in JUnit for threshold logic; place under `src/test` if project supports it.

## Summary

- Choose the right extension point; escalate to compiled services for real ops loops.
- Kill switches, idempotency, and audit names are mandatory.
- Promote Java through SSB like any other Meridian artifact.

## Beanshell escape criteria (Meridian)

Move to compiled Java when any apply:

- Rule exceeds ~80–100 lines or nested loops over identities
- Outbound HTTP/DB beyond SailPoint context helpers
- Needs unit tests for SoD/payment logic
- Multiple applications share the same helper
- Performance-sensitive correlation

Keep Beanshell for trivial FieldValue defaults and one-line maps.

### Task 7 — RequestProcessor / workflow library sketch

1. Name a library class `MnbTicketClient` under `src/` (stub).
2. Methods: `openLeaverTicket(identityName)`, `openSoDExceptionTicket(...)`.
3. Document that LCM workflows call the library—not raw HTTP in Beanshell.
4. Tie secrets to encrypted IIQ config attributes.

**Expected result:** Stub + workflow call notes.

### Code review checklist

- [ ] No hardcoded passwords/URLs
- [ ] Idempotent keys documented
- [ ] Logging without PII dumps
- [ ] Timeout/retry bounded
- [ ] Feature flag / enabled gate

---

**Previous:** [Lesson 101 — SSB/SSD Promotion Discipline](101-ssb-ssd-promotion-discipline.md)  
**Next:** [Lesson 103 — UI Customization & Branding](103-ui-customization-branding.md)
