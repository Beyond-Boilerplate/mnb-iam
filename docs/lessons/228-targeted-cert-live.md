# Lesson 228 — Targeted / Focused Campaign

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 226  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 45

> **Why (1–2 lines):** Targeted certs shrink blast radius — a full sweep is slow and noisy when a bank exam only cares about one population or one high-risk app.

## What this is

A full manager or app-owner sweep (Lessons 226–227) certifies everything a certifier owns. IIQ's **Targeted Certification** scopes by population/filter (e.g. `employeeType == "Contractor"`) or by a single application, producing a smaller, faster campaign with the same decide → provision → sign-off mechanics. You'll build one against contractors from Lesson 220 and one against Wire-only access, then compare volume and completion time to the broad manager cert.

## Know these

| Scope type | Example filter | Certifier |
| --- | --- | --- |
| Population/Identity | `employeeType == "Contractor"` | Named identity (not manager/owner) |
| Application | `MNB-WirePortal` only | Named identity or the app owner |

**Wrong way:** Assuming "targeted" automatically means faster — you have to verify the row count actually shrank versus Lesson 226, not just trust the label.

## Intent

- Build a Targeted Certification scoped to a population (contractors) rather than an org chart.
- Build a second scoped to a single application (Wire) rather than a manager.
- Complete both and prove the scoping actually reduced rows and time versus Lesson 226.
- Record row counts and elapsed time as a targeted-vs-broad comparison.

## Before you start

- [ ] Lesson 220 contractors (`rachel.khatri`, `james.nguyen`) exist with `employeeType=Contractor`
- [ ] Lesson 226 manager cert row count/time noted for comparison
- [ ] `marcus.approve` available as a named certifier
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/228`

## Do this

1. **Certifications → Schedule/Generate → Targeted Certification**. Certification Type: Identity; population/filter matching `employeeType == "Contractor"`. Certifier `helen.ross`. Name `MNB-Targeted-Contractors-<today>`, **Generate Now**.  
   **Expect:** Generation succeeds; row count visible on the confirmation screen.

2. Note the row count.  
   **Expect:** A number you can compare against Lesson 226's full-org cert.

3. Log in as `helen.ross`, complete every decision, **Complete Certification**. Time it against Lesson 226's cert of similar identity count.  
   **Expect:** Targeted feels faster — less per-identity noise to scan.

4. Build a second Targeted Certification: Certification Type Application, scoped to `MNB-WirePortal` (or `MNB-Salesforce-CRM-Live`) only. Certifier `marcus.approve`.  
   **Expect:** Row set excludes any other app he might own.

5. Complete as `marcus.approve`.  
   **Expect:** Row count smaller than a full app-owner sweep covering every account he owns.

6. Write a one-line comparison: `<targeted row count> rows in <minutes> vs <lesson 226 row count> rows in <minutes>`.  
   **Why:** This is the number you'd bring to a bank auditor arguing for narrower, more frequent campaigns over one annual mega-cert.  
   **Expect:** Concrete comparison recorded.

7. Save both cert summaries and the comparison note under `~/iiq-lab-evidence/sandbox/228/`.  
   **Expect:** Evidence files present.

## If it fails

- **Population filter returns 0** — confirm contractors from Lesson 220 have `employeeType=Contractor` on the cube; re-run Refresh Identity Cubes if promoted late.
- **Targeted cert still shows all apps for an app-owner certifier** — confirm the certification definition's Application filter actually restricts to the one app, not just labeled targeted.
- **Certifier field greyed out / defaults to spadmin** — pick "Specific Identity" rather than leaving the default resolution rule active.

## You are done when

Both focused campaigns are completed and you have a written row-count/time comparison against Lesson 226's broad cert.

## Control note

- **Control:** Scoped/targeted certification design.  
- **Owner:** IAM Ops (campaign design) + compliance (population selection).  
- **SLA (lab):** Same session; production targeted campaigns often run monthly for high-risk populations vs. annual broad sweeps.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/228/` — both cert summaries, row-count/time comparison.

## Quick check

1. What two scope types does Targeted Certification support here? → Population/Identity filter, or single Application.  
2. Who becomes certifier when scope isn't manager or app-owner? → A named identity you pick explicitly.  
3. What's the actual proof scoping helped? → A written row-count/time comparison, not just a feeling of speed.

## Navigate

- Previous: Lesson 227  
- Next: Lesson 229  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
