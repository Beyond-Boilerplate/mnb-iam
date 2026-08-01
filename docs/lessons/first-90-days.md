# First 90 days as an IIQ engineer — Meridian map

**Audience:** Entry-level IdentityIQ engineers  
**Path:** Core (Lessons 01–50) + chosen specialist track  
**Lab:** Local Docker / Tomcat academy with Meridian National Bank fixtures

Use this one-pager to connect **Academy lessons** to the **ticket types** you will actually own. Keep it next to your CHANGELOG.

---

## How to use this map

1. Stay on **Core Path** in the Academy TOC (Lessons 01–50 + mid-capstones). Hide specialist tracks until Capstone 50.
2. For each week block, practice the matching ticket type end-to-end in the lab.
3. After Lessons 16, 34, and 46, run the **mid-capstone Verify** bundles before moving on.
4. After Lesson 50, pick **one** specialist track that matches your team’s stack (Directory/JDBC first if unsure).

---

## Week map (Core Path)

| Weeks | Lessons | Real ticket types you are practicing |
| ---: | --- | --- |
| 1 | 01–08 | Lab access, naming standards, “HR feed broke aggregation,” schema / attribute promotion, refresh failures, population requests |
| 2 | 09–16 + **mid-16** | Onboard delimited inventory app, entitlement dictionary cleanup, multi-app aggregation runbook, “why is create-identities on?” |
| 3 | 17–22 | Uncorrelated account queue, false-merge risk review, orphan/dormant hunting, manager hierarchy broken, attribute sync drift |
| 4 | 23–28 | Birthright design review, dept/job role pack, privileged role guardrails, detection vs assignment confusion |
| 5 | 29–34 + **mid-34** | Joiner SLA miss, mover residual access, same-day leaver, contractor expiry, LoA freeze vs terminate, emergency offboarding |
| 6 | 35–38 | Access request catalog gaps, approval / escalation stuck work items, break-glass evidence, IdentityRequest audit pull |
| 7 | 39–46 + **mid-46** | SoD violation triage, dual-control payment findings, policy mitigation, manager/owner cert campaigns, remediation evidence packs |
| 8 | 47–50 | Failed provisioning plan, audit reports for exam week, notification template fix, Capstone go-live checklist |

Scenario runners (avoid hand-editing HR):

```bash
./tools/lab/scripts/scenarios/apply-joiner.sh
./tools/lab/scripts/scenarios/apply-mover.sh
./tools/lab/scripts/scenarios/apply-leaver.sh
./tools/lab/scripts/scenarios/apply-loa.sh
```

---

## Associate-key cheat sheet (do not drift)

| Surface | Column / attr | Notes |
| --- | --- | --- |
| HR feed / identity | **`userId`** | Native key (`MNB#####`) — Lesson 04/05 |
| IT dumps / target apps | **`employeeId`** | Same values as HR `userId` |
| Correlation | account `employeeId` → identity **`userId`** | Then email |
| Leave | `exceptions=LOA` | Not termination |
| Terminate | `inactive=true` / `status=Terminated` | Plus `terminationDate` |

Full map: [`lab-data/reference/hr-column-map.md`](../../lab-data/reference/hr-column-map.md)

---

## After Capstone 50 — pick a specialist track

| If your team’s next pain is… | Start here |
| --- | --- |
| AD / LDAP / directory truth | Lessons 51–58, 61–62 (OpenLDAP is live in Docker) |
| Database apps | Lessons 63–64 (JDBC sample Postgres) |
| SaaS / API | Lessons 68–76 (tenant optional — treat real-world setup as primary reading) |
| ERP / HRIS modernization | Lessons 77–82 |
| Rules / LCM / plugins / SSD | Lessons 89–103 |
| Production hardening | Lessons 104–110 |

Bridge narrative: complete Capstone 50 evidence pack → write one paragraph naming *your* next track → only then expand the Academy TOC to specialist lessons.

---

## Evidence habit (every ticket)

1. What changed (object names `MNB-*`)
2. Task Result / screenshot
3. Persona impact (`nina.joiner`, `priya.wire`, `jordan.reed`, `sofia.torres`, …)
4. Residual risk if incomplete

Academy **Verify now** is the automated floor — binder evidence is still required for interviews and exams.

---

## Navigation

- [Curriculum home](README.md)
- [Core Path implementation roadmap](_CORE_PATH_ROADMAP.md)
- Mid-capstones: [16](mid-16-apps-capstone.md) · [34](mid-34-jml-capstone.md) · [46](mid-46-certs-capstone.md)
