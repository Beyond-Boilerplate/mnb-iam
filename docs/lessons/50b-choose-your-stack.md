# After Capstone 50 — Choose Your Stack

**Level:** Intermediate  
**Track:** Core Path · Bridge  
**Time:** 20–30 minutes  
**Prereq:** [Lesson 50 — Capstone](50-capstone-exam-readiness.md)  
**Path:** Core (shown in TOC) — unlocks specialist tracks intentionally

---

> **Verify:** Bridge / paperwork — write the stack choice card. Academy **Verify now** is disabled; mark the binder complete when you opt into a specialist track.

## Learning objectives

You will be able to:

- Pick **one** specialist track that matches Meridian’s next quarter of work (or your team’s stack)
- Map that choice to concrete Academy lessons (Directory/JDBC first if unsure)
- Keep Core Path evidence intact while you opt into Part II
- Write a one-paragraph “why this track” note for your binder / manager

---

## Why this matters

**Business.** Finishing Capstone 50 means you can run Meridian’s governance loop. It does **not** mean you must grind Lessons 51–110 in order. Real teams onboard AD/LDAP and databases before Salesforce tenants appear.

**Control / audit.** Examiners care that you chose the right connector class for the next app — not that you completed every catalog page. This bridge stops “curriculum completionism” from replacing judgment.

---

## How to choose

| If your next pain is… | Start here | Live lab today? |
| --- | --- | --- |
| AD / LDAP / directory truth | **51–58**, then 61–62 | **Yes — OpenLDAP** in `./tools/lab/docker/up.sh` (Lesson 58 provision stretch) |
| Database / core apps via SQL | **63–64** | **Yes — jdbc-pg :5435** (seeded `mnb_apps`) |
| Custom REST / SCIM SaaS | **68–69** (then 70+) | **Yes — connector-mock :8091** |
| Cloud IdP / M365 / Okta / AWS | 59, 73–76 | Tenant optional — real-world setup primary |
| ERP / HRIS modernization | 77–82 | Mostly design + coexistence |
| Rules / LCM / plugins / SSD | 89–103 | After you have objects worth exporting |
| Production hardening / DR | 104–110 | Production-engineer track |

Default recommendation for Core graduates with no team mandate: **Directory (58) → JDBC (63–64) → API mock (68–69)** — all live without a SaaS tenant.

```
Capstone 50 evidence pack
        │
        ├── Directory live  → Lesson 51…58
        ├── JDBC live       → Lesson 63–64
        ├── API mock live   → Lesson 68–69
        └── Other SaaS/ERP  → choose from matrix above
```

---

## Lab procedure

### Task 1 — Archive Capstone 50

1. Confirm Capstone binder index exists (pipeline, SoD, certs, JML).  
2. Mark residual risks still open.  
3. Do **not** delete Core Path objects to “make room” for Part II.

### Task 2 — Write the stack choice card

```text
MNB-STACK-CHOICE
Engineer: <you>
Date: <today>
Chosen track: <Directory | JDBC | API/SCIM | Other: ___>
First lesson number: <e.g. 58 or 63 or 68>
Why (3 sentences): …
Live backends I will use: OpenLDAP / jdbc-pg / connector-mock / tenant
```

### Task 3 — Opt in on the Academy TOC

1. In the Academy rail, click **Show specialist** (Core Path stays the default for new learners).  
2. Open your first chosen lesson.  
3. Keep [First 90 days](first-90-days.md) nearby for ticket-type mapping.

### Task 4 — Smoke the live backend for your track

| Track | Smoke |
| --- | --- |
| Directory | `ldapsearch` against `localhost:389` (Lesson 58 before-you-start) |
| JDBC | `psql …@localhost:5435/mnb_apps` → 4 rows |
| API/SCIM | `curl http://localhost:8091/health` and `/users` or `/scim/v2/Users` |

---

## Acceptance criteria

- [ ] Stack choice card written  
- [ ] First specialist lesson opened  
- [ ] Live backend smoke for that track (or dated deferral)  

---

## Summary

- Capstone 50 ends Core Path; Part II is **opt-in by stack**.  
- Prefer live Directory → JDBC → API mock before tenant-heavy SaaS.  
- Judgment over catalog completion.

**Previous:** [Lesson 50 — Capstone: Exam Readiness](50-capstone-exam-readiness.md)  
**Next (examples):** [Lesson 51 — Connector Landscape](51-connector-landscape-and-registry.md) · [Lesson 58 — OpenLDAP](58-ldap-openldap-connector.md) · [Lesson 63 — JDBC](63-jdbc-connector-fundamentals.md) · [Lesson 68 — Web Services](68-web-services-connector.md)
