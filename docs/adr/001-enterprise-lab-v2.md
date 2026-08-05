# ADR 001 — Meridian Enterprise Lab v2 (local production simulation)

| Field | Value |
| --- | --- |
| Status | Accepted |
| Date | 2026-08-03 |
| Deciders | Meridian lab owners |
| Scope | Local Docker enterprise ecosystem for IIQ 8.5 |

## Context

Core Path (Lessons 01–50) and specialist connectors teach Meridian IAM with CSV Shadow apps plus three live backends (OpenLDAP, JDBC sample, Wire/SCIM mock). That is correct for pedagogy. After the curriculum wrap we need an opt-in stack that proves joiner → provision → **login** → approval → cert → leaver on a laptop **without SaaS tenants**.

## Decision

Ship **Enterprise Lab v2** as an additive Compose profile and SSD pack:

1. **Fully local Docker only** — no Okta/Workday/Entra tenants.
2. **Narrative names, honest connectors** — `MNB-Workday`, `MNB-Okta`, `MNB-ActiveDirectory` remain Meridian story names; connector types are Web Services / SCIM / LDAP (Samba), not native SaaS/AD-Direct+IQService unless a Windows stretch host is added later.
3. **Single identity master** — `lab-data/enterprise/identity-master.json` generates HR HCM mock, OpenLDAP seed material, Samba user lists, and Keycloak users so directories cannot drift.
4. **Core Path unchanged** — default `./tools/lab/docker/up.sh` stays light; enterprise services start only with `--enterprise` / `docker-compose.enterprise.yml`.
5. **IQService out of v2/v3 gate** — password/Exchange via IQService documented as optional Windows stretch; Samba LDAP path covers agg/correlation/group membership and IIQ pass-through login. **Password Interceptor = Out of scope** — see [`lab-data/enterprise/password/README.md`](../../lab-data/enterprise/password/README.md). Password proofs in the lab target OpenLDAP + Keycloak.

## Consequences

- **Positive:** Reproducible demo/hire/train estate; eight success criteria in [`docs/ENTERPRISE-LAB-V2.md`](../ENTERPRISE-LAB-V2.md) are testable.
- **Negative:** Native Workday/Okta/AD-Direct lessons still need Shadow worksheets for vendor-specific wizards; enterprise pack uses WS/SCIM/LDAP substitutes.
- **Ops:** Recommend ≥16 GB RAM when enterprise profile is up; Core profile remains the daily driver.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Hybrid SaaS sandboxes | Violates locked infra boundary (local-only). |
| Rewrite Core Path onto live systems | Breaks CSV pedagogy and Academy verify fixtures. |
| Full AD Direct + IQService in Docker | Requires Windows; not reliable on macOS Docker. |

## References

- [`docs/ENTERPRISE-LAB-V2.md`](../ENTERPRISE-LAB-V2.md)
- [`docs/lessons/_CORE_PATH_ROADMAP.md`](../lessons/_CORE_PATH_ROADMAP.md) (N+4)
- [`config/PACKS.md`](../../config/PACKS.md)
