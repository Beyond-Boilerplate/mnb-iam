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
| 1 | 01–08 + **08b** | Lab access, naming, unlock / failed agg / “no access” triage, bad HR delta refuse |
| 2 | 09–16 + **mid-16** + **16b** | Onboard delimited apps, runbook order, read Task Results before correlation |
| 3 | 17–19 + **19b** + 20–22 | Uncorrelated + orphan war room, false-merge risk, manager hierarchy, attr sync |
| 4 | 23–28 | Birthright design, dept/job packs, privileged role guardrails |
| 5 | 29 + **29b** + 30–34 + **mid-34** | Joiner/mover/leaver/LoA via runners; optional LCM design; emergency offboard |
| 6 | 35–36 + **36b** + 37–38 | Catalog + **be the approver** (approve/reject), break-glass, IdentityRequest audit |
| 7 | 39–46 + **mid-46** | SoD triage, dual-control, cert campaigns, remediation evidence |
| 8 | 47–50 | Provisioning plan failures, audit reports, Capstone go-live checklist |

Scenario runners (avoid hand-editing HR) — full list in [`lab-data/scenarios/README.md`](../../lab-data/scenarios/README.md):

```bash
./tools/lab/scripts/scenarios/apply-joiner.sh
./tools/lab/scripts/scenarios/apply-mover.sh
./tools/lab/scripts/scenarios/apply-leaver.sh
./tools/lab/scripts/scenarios/apply-loa.sh
./tools/lab/scripts/scenarios/apply-rehire.sh
./tools/lab/scripts/scenarios/apply-batch-hire.sh
./tools/lab/scripts/scenarios/apply-contractor-end.sh
./tools/lab/scripts/scenarios/apply-bad-row.sh   # diagnose only
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

Full bridge lesson: [`50b-choose-your-stack.md`](50b-choose-your-stack.md).

| If your team’s next pain is… | Start here | Live today |
| --- | --- | --- |
| AD / LDAP / directory truth | 51–58, 61–62 | OpenLDAP + provision ACL |
| Database apps | 63–64 | `jdbc-pg` host **:5435** |
| Custom REST / SCIM | 68–69 | `connector-mock` **:8091** |
| Cloud IdP / M365 / Okta / AWS | 59, 73–76 | Tenant optional |
| ERP / HRIS modernization | 77–82 | Design-heavy |
| Rules / LCM / plugins / SSD | 89–103 | After Capstone objects exist |
| Production hardening | 104–110 | Production-engineer track |

Default for Core grads: **58 → 63–64 → 68–69**, then opt into SaaS tenants.

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
