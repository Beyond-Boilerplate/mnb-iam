# Core Path — implementation roadmap

Owner posture: ship **Core Path (01–50)** as the entry-level product; specialist tracks (51–110) are opt-in.

---

## Shipped

### Packaging + N+1 (Core realism)

See prior sections in git history / Academy: naming drift, Core TOC filter, mid-capstones, scenario runners, ticket-shaped labs (`08b`–`36b`).

### N+2 — Live credibility (**done**)

| ID | Work item | Location |
| --- | --- | --- |
| L1 | JDBC 63–64 live on `jdbc-pg` **:5435** with seeded SQL; in main stack | `docker-compose.iiq.yml`, `lab-data/connectors/jdbc/` |
| L2 | LDAP provision stretch (group add/remove via `svc-iiq-provision`) | Lesson 58 Task 8 + `lab-data/connectors/ldap/provision-stretch-*.ldif` |
| L3 | `connector-mock` :8091 for Wire Portal + SCIM; Lessons 68–69 primary path | `tools/connector-mock/`, compose service |
| L4 | Capstone bridge — choose your stack | `50b-choose-your-stack.md` |

**Exit met:** Core graduate can run Directory + JDBC + API mock tracks without a SaaS tenant; Capstone 50 no longer dumps straight into Lesson 51.

---

## Iteration N+3 — Specialist polish (**next**)

| ID | Work item | Acceptance |
| --- | --- | --- |
| S1 | Top 5 SaaS lessons to Lesson-71-grade depth | Real-world setup primary |
| S2 | No niche industry connector expansion | Keep WS/SCIM/JDBC/Logical routing |
| S3 | Rules/workflows after Core grads | 89–96 prereq Capstone 50 |
| S4 | Hardening marked production-engineer | TOC specialist grouping |

---

## Verify / product hardening (parallel)

| ID | Work item | Notes |
| --- | --- | --- |
| V1 | `identity.hasBundle` / entitlement absence checks | Hard “Nina has birthright, no wire” |
| V3 | Public academy deploy rebuild | CD / `learn/build.py` |
| V4 | Homelab collision policy | `lab-data/scenarios/README.md` |

---

## Sequencing board

```text
Packaging  → done
N+1        → done
N+2        → done (live Directory / JDBC / API mock + bridge)
N+3 (next) → S1–S4 selective specialist depth
Parallel   → V1, V3–V4
```

---

## References

- JDBC: [`../../lab-data/connectors/jdbc/README.md`](../../lab-data/connectors/jdbc/README.md)
- LDAP: [`../../lab-data/connectors/ldap/README.md`](../../lab-data/connectors/ldap/README.md)
- Mock: [`../../tools/connector-mock/README.md`](../../tools/connector-mock/README.md)
- Bridge: [`50b-choose-your-stack.md`](50b-choose-your-stack.md)
- Curriculum: [`README.md`](README.md)
