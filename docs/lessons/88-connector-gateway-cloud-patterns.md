# Lesson 88 — Connector Gateway / Cloud Patterns

**Level:** Intermediate  
**Track:** Connectors — Infra, Logical, PAM  
**Time:** 60–90 min  
**Prereq:** Lesson 87 — Duo MFA Integration Patterns  

**Lab data:**
- Repo: `lab-data/connectors/README.md`
- Repo: `lab-data/connectors/ad/iqservice-checklist.md`
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Runtime: `~/iiq-lab-data/connectors/`
- Optional: `docker-compose.connectors.yml` at repo root

---

## Learning objectives

You will be able to:

- Explain **Cloud Gateway / VA / hybrid connector host** patterns for Meridian (on-prem IIQ talking to cloud and segmented networks)
- Draw Meridian’s trusted path: IIQ → Gateway/IQService → target
- Complete a lab-without-live-target placement worksheet for AD, SaaS, and mainframe segments
- Document TLS, allowlists, and secret distribution for gateway hosts
- Define ops SLAs for gateway health vs Application aggregation failures

---

## Why this matters

**Business.** Meridian apps live in on-prem DC, Azure/AWS, and partner segments. Connectors fail when network paths are afterthoughts.

**Control / audit.** Outages look like “IAM is down” when the gateway host or IQService is unhealthy. Examiners and ops need a clear diagram of trust boundaries, TLS, and who owns the jump path.

---

## Concepts

```
┌─────────────────┐     TLS      ┌──────────────────┐
│ IdentityIQ      │─────────────►│ Cloud Gateway /  │
│ (K8s / VM)      │              │ VA / IQService   │
└─────────────────┘              └────────┬─────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              AD / LDAP              SaaS APIs              RACF / DB
              (on-prem)             (internet)             (segment)
```

| Pattern | When Meridian uses it |
| --- | --- |
| IQService on Windows | AD Direct, Windows Local |
| Cloud Gateway / VA-style host | SaaS, restricted egress from IIQ pods |
| Direct from IIQ | Lab laptop / open lab networks only |
| Delimited / proxy files | Training when live path blocked |

**Lab-without-live-target:** Architecture + placement worksheets + health checklist. Optional read of `docker-compose.connectors.yml` for local stubs—do not require production gateway.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`
- [ ] Read `lab-data/connectors/README.md` live-vs-lab statement
- [ ] IQService checklist available
- [ ] Binder: `connectors/gateway/`

---

## Lab procedure

### Task 1 — Inventory connector network needs

1. From matrix, classify Meridian systems into: on-prem directory, database, SaaS, mainframe, PAM.
2. For each class, mark: Direct from IIQ / Gateway / IQService / File proxy.
3. Produce table in binder (minimum 6 rows).

**Expected result:** Classification table with path type per system class.

**If it fails:** Use AD=IQService, SaaS=Gateway, RACF=segment gateway, CSV=file.

---

### Task 2 — Meridian placement worksheet

Fill:

| Host role | Example name | Zone | Owns patching |
| --- | --- | --- | --- |
| IIQ app | `iiq-app` | App | Platform |
| IQService | `iqsvc-ad-01` | AD tier | Windows Ops |
| Cloud Gateway | `mnb-gw-saas-01` | DMZ/egress | Platform |
| Connector stubs | docker compose | Laptop | Trainee |

1. Mark which hosts store connector secrets.
2. Require TLS everywhere; note cert owner.

**Expected result:** Placement worksheet with zones and owners.

---

### Task 3 — IQService vs Cloud Gateway contrast

1. Annotate IQService checklist: used for Windows/AD operations near DCs.
2. Write five bullets for Cloud Gateway: outbound allowlist, mutual TLS, no inbound from internet to IIQ, health endpoint, separate autoscaling from IIQ UI.
3. State anti-pattern: installing IQService on the IIQ app container “for convenience.”

**Expected result:** Contrast page in binder.

**If it fails:** Minimum three bullets each.

---

### Task 4 — Lab docker / stub awareness

1. Open repo `docker-compose.connectors.yml` if present; list stub services (LDAP/DB/etc.).
2. Note: stubs are **learn track**, not production gateway.
3. Write how homelab CD (if used) differs from bank DMZ gateway.

**Expected result:** Short note distinguishing lab stubs vs enterprise gateway.

**If it fails:** Skip compose; still complete Tasks 1–3 and 5–6.

---

### Task 5 — Failure matrix (ops)

| Symptom | Check first | Owner |
| --- | --- | --- |
| All AD prov fail | IQService service / TLS | Windows Ops |
| One SaaS app fails | Gateway allowlist / API creds | Platform + App owner |
| All aggregations stuck | IIQ task servers | IAM Ops |
| Intermittent timeouts | Network path / DNS | Network |

Add Meridian SLA: gateway host disk/CPU alert = Sev3; complete connector outage = Sev2.

**Expected result:** Failure matrix + SLA line.

---

### Task 6 — Lab-without-live-target acceptance path

1. Do **not** require a live Cloud Gateway.
2. Attach: classification table, placement worksheet, contrast page, failure matrix.
3. Optional: configure one Application Description field with “Expected path: Gateway” for a SaaS app shell you already have.

**Expected result:** Four artifacts bound; optional Application annotation.

---

## Acceptance criteria

- [ ] System class → path type table complete
- [ ] Placement worksheet with zones/owners
- [ ] IQService vs Gateway contrast written
- [ ] Lab stubs vs enterprise note written
- [ ] Failure matrix + SLA documented
- [ ] No secrets committed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| IIQ pod cannot reach SaaS | Egress policy | Route via gateway allowlist |
| AD works in DC, fails in K8s | Missing IQService path | Place IQService near AD |
| TLS handshake errors | Cert mismatch | Fix trust store on gateway |
| Trainee blocked | No live GW | Use worksheet path |
| Secrets on gateway disk cleartext | Bad install | Use OS secret store / HSM pattern |

---

## Training binder evidence

- Classification table
- Placement worksheet
- IQService vs Gateway contrast
- docker-compose / lab stub note
- Failure matrix + SLA
- Optional Application “Expected path” screenshot

---

## Knowledge check

1. What Windows component commonly fronts AD Direct?
2. Why separate Cloud Gateway from the IIQ UI pod?
3. What is the lab-without-live-target deliverable set?
4. Are docker connector stubs production gateways?
5. Who typically owns IQService patching?

### Answers

1. IQService.  
2. Controlled egress, blast-radius isolation, independent scaling/health.  
3. Classification, placement, contrast, failure matrix (worksheets)—no live gateway required.  
4. No—learn/lab stubs only.  
5. Windows Ops (per placement worksheet).

---

## Stretch lab

Draft a Prometheus-style health checklist for gateway hosts (process up, cert expiry &lt; 30 days, disk &gt; 20% free) for ops runbooks.

---

## Summary

- Hybrid Meridian connectivity needs explicit IQService and Cloud Gateway placement.
- Ops distinguish gateway failure from Application logic failure.
- Training completes with architecture worksheets when live gateways are unavailable.

---

**Previous:** [Lesson 87 — Duo MFA Integration Patterns](87-duo-mfa-integration-patterns.md)  
**Next:** [Lesson 89 — Rule Types Catalog](89-rule-types-catalog.md)
