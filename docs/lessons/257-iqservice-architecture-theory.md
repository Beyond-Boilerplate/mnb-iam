# Lesson 257 — IQService Architecture (Theory)

**Track:** Enterprise Sandbox Path — **Theory**  
**Time:** ~45 minutes  
**Prereq:** Lesson 205 (Samba AD live ops), Lesson 256  
**Stack:** `./tools/lab/docker/up.sh --enterprise --with=ad` (AD app for contrast; **no** Windows IQService required)

**Maps to classic track:** 53

> **Why:** IdentityIQ often runs on Linux. Corporate AD password reset and many enable paths do **not** finish inside the IIQ JVM — they need a Windows **IQService** agent near the domain controllers.

## What this is

**Theory** lesson — architecture and examiner artifacts. This estate’s Samba AD path (**205**, **234**) proves **account/group aggregation and membership** without a live IQService. Production Meridian AD Direct still needs the agent for password/Exchange-class ops.

You will leave knowing: what IQService is, where it sits, TLS/blast-radius rules, least privilege, and **what this lab does vs does not prove**.

## Know these

```text
IIQ (Linux/container)
  --TLS--> IQService (Windows near DCs)
              --> Domain Controllers / Exchange
```

| Concern | Without IQService | With IQService |
| --- | --- | --- |
| Password set/change | Fragile / unsupported for bank pattern | Executes on Windows near DC |
| Network blast radius | IIQ opened to every DC | IIQ → IQService only; IQService → DC |
| Exchange / mailbox | Needs Windows management surface | IQService host in scope when Exchange = yes |

| Term | Plain English |
| --- | --- |
| **IQService** | Windows agent that runs AD Direct mutating ops |
| **Blast radius** | How widely IIQ credentials can reach DCs |
| **Least privilege** | Service account rights scoped to OUs/groups — not Domain Admin |
| **Samba lab path** | Local AD-shaped directory **without** IQService password proof |

- **Wrong way:** “Open LDAPS from IIQ pods to every DC” instead of narrowing to IQService.
- **Wrong way:** Domain Admin for the connector account “so Test Connection works.”
- **Wrong way:** Claiming Lesson 205 proved production password reset — it did not.

## Intent

- Sketch Meridian’s IQService placement and TLS trust boundary.
- Complete a least-privilege / ports checklist under evidence.
- Write an honest lab-vs-prod gap statement for Samba.

## Before you start

- [ ] Lesson 205 completed (or `MNB-ActiveDirectory-Live` aggregating)
- [ ] Lesson 256 selection matrix has a Corporate AD row
- [ ] Evidence:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/257
```

## Do this

### Task 1 — Contrast live Samba vs prod AD Direct

Open `MNB-ActiveDirectory-Live` (or your Samba app). Note what you already proved (agg, groups in 234).

Write:

```text
Lab proves: account/group aggregation, membership add/remove (234).
Lab does NOT prove: IQService TLS, Windows password set, Exchange mailbox create.
Prod Meridian AD Direct requires: IQService host + least-priv account + TLS.
```

- **Why:** separates pedagogy from architecture promises.
- **Expect:** gap statement saved.

### Task 2 — Placement sketch

Draw or write:

```text
[IIQ tier] --TLS :5050*--> [IQService VM near DC site] --> [DCs]
* confirm port in your IQService install guide — never hardcode blindly
```

Decide:

| Item | Your lab/prod note |
| --- | --- |
| IQService hostname | |
| TLS / private CA | Required in prod — cleartext = finding |
| Forest / domain | `meridiannb.com` lab default |
| Exchange in scope? | Y/N |

- **Expect:** checklist filled under evidence.

### Task 3 — Least privilege worksheet

List rights the service account **should** have:

- Create/modify/disable users in scoped OUs  
- Manage membership of in-scope groups  
- Password reset only where helpdesk/JML requires  
- Exchange rights **only if** mailbox provisioning is in scope  

Explicitly write: **not Domain Admin**.

- **Expect:** rights model on disk for examiners.

### Task 4 — Failure modes to monitor

Note three monitoring signals:

1. IQService process / Windows service down  
2. TLS trust break (IIQ cannot connect)  
3. Provisioning Transaction timeouts on PASSWORD/ENABLE  

Cross-link Lesson **230** triage for when AD ops fail.

- **Expect:** runbook bullets saved.

## If it fails

| Symptom | Fix |
| --- | --- |
| Want to “just install IQService in Docker” | Out of scope — use this theory lesson; Samba remains the live AD-shaped target |
| Confused why 205 “AD” works without IQService | Aggregation/LDAP-shaped ops ≠ full AD Direct password path |

## You are done when

- [ ] Lab-vs-prod gap statement written  
- [ ] Placement + least-privilege checklist saved  
- [ ] You can answer: “Where does TLS terminate for AD password reset?”  

## Control note

- **Control:** AD Direct execution path and credential blast radius  
- **Owner:** IAM Engineering + Windows/AD Ops  
- **Evidence:** `~/iiq-lab-evidence/sandbox/257/`  

## Quick check

1. Why does AD Direct need IQService? → Mutating/password ops run on Windows near DCs  
2. What network pattern do banks prefer? → IIQ → IQService (TLS), not IIQ → every DC  
3. What did Samba lessons not prove? → Production IQService password/Exchange path  

## Feedback

Could you explain IQService to a network engineer in four sentences? If you over-claimed password proof from Lesson 205, rewrite the gap statement before moving on.

## Navigate

- Previous: [Lesson 256](256-connector-registry-theory.md)
- Next: [Lesson 258](258-ldif-offline-evidence-theory.md)
- Related live: [205](205-samba-ad-live-ops.md) · [234](234-ad-groups-ous-live.md) · [230](230-provisioning-troubleshoot-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md)
