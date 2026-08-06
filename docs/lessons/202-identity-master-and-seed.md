# Lesson 202 — Identity Master & Enterprise Seed

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~45 minutes  
**Prereq:** Lesson 201  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** Packs

> **Why:** A single identity master stops LDAP/AD/IdP/HCM from drifting into six different truths about the same person. Before you correlate anything, answer: which system is authoritative, and how do the others stay in sync with it?

## What this is

> **Already covered in 201:** `up.sh --enterprise` imports Application XML as **definitions only**. Identity Warehouse still has **spadmin** — not Helen. This lesson owns the **identity master** behind those personas and how to re-run seed deliberately.

In Core Path, each connector lesson invents its own CSV. That does not scale for a bank-shaped estate: the same ~30 Meridian employees must exist — with the *same* `userId` / username / email — in HCM, OpenLDAP, Samba AD, and Keycloak at once.

Three pieces:

| Piece | Path / script | Job |
| --- | --- | --- |
| **Identity master** | `lab-data/enterprise/identity-master.json` | One JSON array of people (`userId`, `username`, names, `email`, `department`, `title`, `managerUserId`, `employeeType`, `status`, `password`, IdP `groups`) |
| **Generator** | `tools/lab/enterprise/generate-identity-artifacts.py` | Fans the master into every connector’s native shape |
| **Seed** | `seed-enterprise.sh` | Regenerate + import durable IIQ objects from `config/` via MCP + best-effort Samba |

This is the “Enterprise” pack in [`config/PACKS.md`](../../config/PACKS.md) — distinct from CD “Academy” (HelloWorld only) and Core “Lab seed” (authoritative `MNB-HR` + cubes).

```text
identity-master.json
        │
        ▼
generate-identity-artifacts.py
        │
        ├─► OpenLDAP LDIF
        ├─► Samba CSV
        ├─► HCM workers.json   ◄── live at :8091 (UI + API)
        ├─► CRM SCIM Users.json
        ├─► ITSM stub
        └─► Keycloak users.json
                │
                ▼
        seed-enterprise.sh  ──► IIQ XML import (apps) + Samba
                │
                ▼
        Identity Warehouse still empty of workforce
        (Lesson 207: Aggregate MNB-Workday → cubes)
```

## Know these

- Default password for every seeded persona: **`LabUser1!`**
- IdP groups: `mnb-employees`, `mnb-managers`, `wire-initiators`, `wire-approvers`, `portal-users`
- Primary personas you will meet again and again:

  | Username | userId | Role (lab) | Notes |
  | --- | --- | --- | --- |
  | `helen.ross` | `MNB00001` | Head of IAM | No manager; groups `mnb-employees` + `mnb-managers` |
  | `priya.wire` | `MNB00090` | Relationship Manager | Wire access by request, not birthright |
  | `marcus.approve` | `MNB00091` | Wire Approver | Approvals lessons |
  | `sanjay.kapoor` | `MNB00006` | Manager of Priya | Lesson 214 leans on this link |

- Every record carries `employeeType` **and** `status` — later leaver/mover lessons and CRM exclusion (210) read **`status`** (`active` / `terminated`).
- **Authoritative in this estate:** `MNB-Workday` (Web Services → HCM mock). `MNB-HR` remains a non-authoritative CSV contrast from Core Path — do not aggregate it to create cubes.
- **Wrong way:** Hand-editing a *generated* file (e.g. the LDIF) instead of `identity-master.json` — your edit is silently overwritten on the next generator run.

## Intent

- Know the master → generator → seed pipeline and the three recurring personas.
- Regenerate connector artifacts and re-import enterprise durable objects.
- Prove the same persona in a **live** feed (HCM UI/API) while IIQ Warehouse still has no workforce cube.
- Accept (and understand) soft-fail object types on first import.

## Before you start

- [ ] Lesson 201 stack up; `e2e-smoke.sh` green
- [ ] `mnb-iiq-mcp` running (`docker ps | grep mcp`)
- [ ] `IIQ_MCP_URL` / `MCP_API_KEY` available (printed at end of `up.sh --enterprise`)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/202
```

## Do this

### Task 1 — Regenerate artifacts from the master

One edit to `identity-master.json` must fan out to every connector shape together — otherwise a bank ends up with an HR record and no matching directory account.

```bash
python3 tools/lab/enterprise/generate-identity-artifacts.py
```

- **Why:** the generator is the only safe way to keep LDAP / Samba / HCM / CRM / Keycloak in sync with the master.
- **Expect:** six `wrote ...` lines, one per generated artifact.

> **Tip:** Prove fan-out in **live systems** (HCM UI/API next), not by browsing the generated files.

### Task 2 — Prove HCM fan-out is live

Same human, native HCM shape — the correlation problem Lesson 214 formalizes, proven at the source *before* cubes exist.

1. Open **MNB Workday**: [http://localhost:8091/hcm/ui](http://localhost:8091/hcm/ui)
2. Search `helen.ross` — confirm `id` `MNB00001`, status **Active**
3. Peek at the raw API IIQ will aggregate later:

```bash
curl -s http://localhost:8091/hcm/v1/workers | python3 -m json.tool | head -40
```

- **Why:** UI convenience ≠ what the connector speaks — both should show Helen.
- **Expect:** Helen visible in the UI and in the API JSON.

### Task 3 — Re-import the enterprise pack

```bash
./tools/lab/enterprise/seed-enterprise.sh
```

- **Why:** re-runs the generator, refreshes app definitions (still **no** aggregation), imports enterprise XML via MCP, and best-effort seeds Samba if `mnb-samba-ad` is healthy.
- **Expect:**
  - Script completes
  - **Warnings are OK**; hard stops are not
  - Ending note reminds cubes come in Lesson 207

> **Watch out:** `IdentityTrigger` / `CertificationDefinition` soft-fails on first MCP import are normal — some types need referenced Workflow/Application first. Move on unless the script hard-stops.

### Task 4 — Confirm enterprise Applications in IIQ

Open http://localhost:8080/identityiq → **Applications → Application Definition** and confirm:

| Application | What to check |
| --- | --- |
| `MNB-Workday` | Authoritative HCM — definition only so far |
| `MNB-ActiveDirectory-Live` | Present |
| `MNB-Okta` | Present |
| `MNB-CoreBanking` | Present |
| `MNB-Salesforce-CRM-Live` | Present |
| `MNB-ServiceNow` | Present |

- **Why:** these sit **alongside** Core CSV apps (`MNB-HR` non-authoritative, …) — you retire CSV paths deliberately later, not by deleting them now.
- **Expect:** all six visible; `MNB-Workday` shows authoritative / create-identities intent on the app object.

### Task 5 — Prove Warehouse is still empty of workforce

People live in HCM/directories first; IIQ cubes are an operator action in Lesson 207.

1. **Identities → Identity Warehouse**
2. Search `helen.ross`, `priya.wire`, `marcus.approve`

- **Why:** this is the seed contract — definitions imported, cubes not minted.
- **Expect:** **no** workforce hits (only `spadmin` if you search broadly).

> **Watch out:** Do **not** aggregate `MNB-HR` to “fix” an empty Warehouse — that defeats the Workday-first path.

### Task 6 — Close with asserts

```bash
./tools/lab/enterprise/verify-lesson.sh 202
```

- **Why:** hard checks cover apps + live HCM Helen — not Warehouse cubes yet.
- **Expect:** hard asserts PASS.

## If it fails

| Symptom | Fix |
| --- | --- |
| Generator: missing `identity-master.json` | Not at repo root, or file deleted — `git checkout -- lab-data/enterprise/identity-master.json` |
| `seed-enterprise.sh` can’t reach MCP | Confirm `mnb-iiq-mcp` running; `IIQ_MCP_URL` / `MCP_API_KEY` match `up.sh` output |
| Samba seed step does nothing | Wait until `mnb-samba-ad` is **healthy** (2+ min first boot), then `./tools/lab/enterprise/seed-samba.sh` |
| Apps imported but attributes look stale | You edited the master after a prior seed — re-run generator **and** `seed-enterprise.sh` together |
| HCM UI empty / refused | `connector-mock` down — `curl -sf http://localhost:8091/health`; finish Lesson 201 first |
| Warehouse already has Helen | Leftover from an old Core-style seed — wipe with `up.sh --enterprise` (no `--keep-existing`) or ignore and continue; Lesson 207 still owns Workday as source of truth |

## You are done when

- [ ] Six enterprise Applications exist in IIQ
- [ ] Live HCM UI/API returns Helen (`MNB00001` / `helen.ross`)
- [ ] Warehouse has **no** workforce cubes for Helen / Priya / Marcus
- [ ] You can name `MNB-Workday` as the authoritative HCM app (Lesson 207 creates the cubes)
- [ ] `./tools/lab/enterprise/verify-lesson.sh 202` hard asserts PASS

## Control note

- **Control:** Identity source-of-truth governance (single master feed, no fixture drift)
- **Owner:** IAM Ops / HR data steward
- **SLA (lab):** regenerate + reseed in the same change window as any `identity-master.json` edit
- **Evidence:** `~/iiq-lab-evidence/sandbox/202/` — generator output, seed log, Application list screenshot, Warehouse empty search screenshot

## Quick check

1. What file is the single source of truth? → `lab-data/enterprise/identity-master.json`
2. Which script fans it into six connector-native shapes? → `generate-identity-artifacts.py`
3. Where do Helen’s IIQ cubes come from? → Lesson 207 — Aggregate `MNB-Workday` + Identity Refresh (create identities)
4. Why leave Core CSV `MNB-HR` in place? → non-authoritative contrast; do not use it to mint enterprise cubes

## Feedback

Could you name the master file, the generator, and why Warehouse is empty after seed without looking? If a step failed, note **Task number + expected vs actual** (and the `verify-lesson.sh` FAIL line if any).

## Navigate

- Previous: [Lesson 201](201-boot-enterprise-stack.md)
- Next: [Lesson 207 — Authoritative HCM (Workday-Shaped)](207-hcm-workday-shaped.md) *(first workforce cubes — do this before 204–206)*
- Also: [Lesson 203 — Mailpit](203-mailpit-iiq-email.md) (mail wiring; no cubes required)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
