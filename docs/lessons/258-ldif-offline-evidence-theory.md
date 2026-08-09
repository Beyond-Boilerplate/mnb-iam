# Lesson 258 — LDIF Offline Directory Evidence (Theory)

**Track:** Enterprise Sandbox Path — **Theory**  
**Time:** ~45 minutes  
**Prereq:** Lessons 204, 235  
**Stack:** `./tools/lab/docker/up.sh --enterprise` (contrast live OpenLDAP; LDIF file from repo)

**Maps to classic track:** 60

> **Why:** When VPN to LDAP is down — or M&A ships a dump without bind credentials — banks still need certifiable inventory. LDIF is that **offline evidence**, not a second live directory.

## What this is

**Theory + light file inspection.** An **LDIF** (LDAP Data Interchange Format) file is a text serialization of directory entries. An LDIF connector **iterates the file**; it does not bind to port 389.

Live OpenLDAP (**204**, **235**) is BAU. LDIF is for M&A extracts, DR windows, and air-gapped evidence. Never point joiner/leaver **PASSWORD** / **ENABLE** at an LDIF app.

## Know these

```text
Vendor / directory export
  → LDIF dump (as-of timestamp + hash)
  → LDIF Application (iterate-only, often NO_RANDOM_ACCESS)
  → Account Aggregation → correlate to HR cubes
  ✗ no PASSWORD / ENABLE / live provision
```

| | Live OpenLDAP (204/235) | LDIF connector |
| --- | --- | --- |
| Transport | Bind `ldap://` / `ldaps://` | Read file on disk |
| Freshness | Near real-time | As-of dump |
| Features | PROVISIONING / ENABLE possible | Iterate / `NO_RANDOM_ACCESS` |
| JML target? | Yes (when proven) | **Never** |

| Term | Plain English |
| --- | --- |
| **LDIF** | Text encoding of directory entries (`dn:` lines) |
| **As-of** | Timestamp the dump was taken |
| **Chain of custody** | Hash + who handled the file |
| **Non-authoritative** | Does not create workforce cubes — Workday does |

- **Wrong way:** Scheduling LDIF nightly next to `MNB-OpenLDAP` as equal sources of truth.
- **Wrong way:** Helpdesk “reset password via the LDIF app.”
- **Wrong way:** Turning create-identities on for an LDIF application.

## Intent

- Inspect a repo LDIF and count `dn:` lines.
- Document as-of + hash discipline.
- Write when Meridian uses LDIF vs live bind.

## Before you start

- [ ] Live OpenLDAP path understood (204/235)
- [ ] Repo LDIF available, e.g. `lab-data/connectors/ldap/mnb-openldap.ldif` (or any sample under `lab-data/`)
- [ ] Evidence:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/258
```

## Do this

### Task 1 — Inspect the dump

```bash
# Adjust path if your repo layout differs
wc -l lab-data/connectors/ldap/mnb-openldap.ldif 2>/dev/null \
  || find lab-data -name '*.ldif' 2>/dev/null | head -5

grep -c '^dn:' lab-data/connectors/ldap/mnb-openldap.ldif 2>/dev/null || true
```

- **Why:** aggregation row counts must match `dn:` predictions.
- **Expect:** a DN count written under evidence.

### Task 2 — Chain of custody note

Write:

```text
File: ________
As-of (when dump was taken): ________
SHA-256: ________   # shasum -a 256 <file>
Handler: <your name>
Purpose: M&A | DR evidence | air-gap training
```

```bash
shasum -a 256 lab-data/connectors/ldap/mnb-openldap.ldif 2>/dev/null || true
```

- **Expect:** custody block saved.

### Task 3 — Decision table

| Scenario | Use live OpenLDAP | Use LDIF |
| --- | --- | --- |
| Nightly BAU agg | Yes | No (unless Architecture schedules controlled dump feed) |
| VPN down / examiner evidence | Prefer last good live Task Result; LDIF if that is all you have | Yes |
| M&A without bind creds | No | Yes |
| Joiner create / password | Yes (235) | Never |

- **Expect:** table under evidence.

### Task 4 — Limitations card

```text
LDIF app: NO_RANDOM_ACCESS / iterate-only (typical).
Do not design get-by-DN password unlock against it.
Create-identities: OFF — Workday owns cubes.
Contrast proof: live ldapsearch (235) vs file grep '^dn:'.
```

- **Expect:** card saved; you can explain this to an examiner.

## If it fails

| Symptom | Fix |
| --- | --- |
| No `.ldif` in repo | Use `find lab-data -name '*.ldif'`; or export one entry with `ldapsearch -L` from live OpenLDAP for inspection practice only |
| Tempted to build full LDIF Application now | Optional stretch — theory bar is inspection + custody + limitations; live build is classic 60 |

## You are done when

- [ ] DN count + hash/custody note saved  
- [ ] Decision table separates BAU live vs offline evidence  
- [ ] You refuse PASSWORD/ENABLE on LDIF in one sentence  

## Control note

- **Control:** Offline directory evidence and non-authoritative inventory  
- **Owner:** IAM Ops + M&A / DR leads  
- **Evidence:** `~/iiq-lab-evidence/sandbox/258/`  

## Quick check

1. Is LDIF a live directory? → No — a file serialization  
2. Can JML target LDIF for disable? → No  
3. What metadata makes a dump examiner-ready? → As-of timestamp + hash + handler  

## Feedback

Could you tell M&A why you need a hashed LDIF instead of a spreadsheet? If you only have live LDAP, note how you’d produce an emergency dump (`ldapsearch -L`) for custody practice.

## Navigate

- Previous: [Lesson 257](257-iqservice-architecture-theory.md)
- Next: [Lesson 201](201-boot-enterprise-stack.md) (path restart) or Capstone [250](250-capstone-bank-day.md)
- Related live: [204](204-openldap-live-ops.md) · [235](235-ldap-provision-stretch.md) · [256](256-connector-registry-theory.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md)
