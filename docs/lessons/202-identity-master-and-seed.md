# Lesson 202 — Identity Master & Enterprise Seed

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~50 minutes  
**Prereq:** Lesson 201  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** Packs

> **Why (1–2 lines):** A single identity master stops LDAP/AD/IdP/HCM from drifting into six different truths about the same person. An examiner's first correlation question is always "which system is authoritative, and how do the others stay in sync with it?" — this lesson is the answer.

## What this is

In Core Path, each connector lesson invents its own CSV. In the enterprise estate that doesn't scale — the same ~30 Meridian employees need to exist, with the *same* `userId`/username/email, in the HCM mock, OpenLDAP, Samba AD, and Keycloak simultaneously. `lab-data/enterprise/identity-master.json` is that single source of truth: one JSON array of identities (`userId`, `username`, `firstName/lastName`, `email`, `department`, `title`, `managerUserId`, `employeeType`, `status`, `password`, IdP `groups`). `tools/lab/enterprise/generate-identity-artifacts.py` reads it once and fans it out into every connector's native shape: an OpenLDAP LDIF, a Samba `samba-users.csv`, the HCM mock's `workers.json`, a CRM SCIM `Users.json`, an ITSM catalog stub, and a Keycloak `keycloak-users.json`. `seed-enterprise.sh` then imports the durable IIQ objects (Applications, Workflows, IdentityTriggers, Bundles, QuickLinks, CertificationDefinitions under `config/`) via MCP and best-effort seeds Samba. This is the "Enterprise" pack described in [`config/PACKS.md`](../../config/PACKS.md) — distinct from the CD "Academy" pack (HelloWorld only) and the default "Lab seed" pack (`MNB-HR` + `MNB-OpenLDAP`).

## Know these

- One master file → six generated artifacts: LDIF, Samba CSV, HCM JSON, CRM SCIM JSON, ITSM stub, Keycloak JSON.
- Default password for every seeded persona: `LabUser1!`. IdP groups: `mnb-employees`, `mnb-managers`, `wire-initiators`, `wire-approvers`, `portal-users`.
- Primary personas: `helen.ross` (`MNB00001`, Head of Identity & Access, no manager, groups `mnb-employees`+`mnb-managers`), `priya.wire` (`MNB00090`, Relationship Manager, `mnb-employees` only — wire access by request, not birthright), `marcus.approve` (`MNB00091`, Wire Approver).
- `seed-enterprise.sh` = regenerate + seed Core lab data if missing + import enterprise XML via MCP + best-effort Samba seed.
- Every identity record carries both an `employeeType` and a `status` — `status` (e.g. `active`/`terminated`) is what later lessons' leaver/mover scenarios (218–219) and the CRM feed's exclusion rule (Lesson 210) actually read.
- **Wrong way:** Hand-editing a generated file (e.g. the LDIF) directly instead of `identity-master.json` — your edit is silently overwritten on the next generator run and nothing downstream stays in sync.

## Intent

- Know where the one true identity list lives and how to read it before touching any connector.
- Regenerate every downstream artifact from that single file and see the fan-out with your own eyes.
- Import the enterprise durable objects (Applications/Workflows/Triggers/Bundles) into a running IIQ.
- Accept — and understand why — a couple of object types soft-fail on first import.

## Before you start

- [ ] Lesson 201's stack up and `e2e-smoke.sh` green
- [ ] `mnb-iiq-mcp` running (`docker ps | grep mcp`)
- [ ] `IIQ_MCP_URL`/`MCP_API_KEY` available (printed at the end of `up.sh --enterprise`)
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/202`

## Do this

1. Open `lab-data/enterprise/identity-master.json`. Find `userId: "MNB00001"` (`helen.ross`), `priya.wire` (`MNB00090`), and `marcus.approve` (`MNB00091`).  
   **Why:** these three are your recurring personas for the rest of this path — know their `userId`s and groups cold.  
   **Expect:** top-level `defaultPassword` reads `LabUser1!`; five `groups` values match Know these.

2. Regenerate the artifacts: `python3 tools/lab/enterprise/generate-identity-artifacts.py`.  
   **Why:** one edit to `identity-master.json` should regenerate every downstream shape together, so a real bank never ends up with an HR record with no matching directory account.  
   **Expect:** six `wrote ...` lines print, one per generated artifact.

3. Open two of the generated files to see the fan-out concretely: `lab-data/enterprise/generated/openldap-people.ldif` and `lab-data/connectors/hcm/workers.json`.  
   **Why:** same human, two different native shapes — this is exactly the correlation problem Lesson 214 formalizes.  
   **Expect:** both files contain a record for `MNB00001` with matching name/email.

4. Import the enterprise pack: `./tools/lab/enterprise/seed-enterprise.sh`.  
   **Why:** re-runs the generator, seeds Core lab data if missing, imports enterprise XML via MCP (`import-enterprise-xml.py`), and best-effort seeds Samba if `mnb-samba-ad` is running.  
   **Expect:** script completes; warnings are acceptable, hard stops are not.

5. In IIQ (`http://localhost:8080/identityiq` → **Applications → Application Definition**), confirm the enterprise Applications landed: `MNB-Workday`, `MNB-ActiveDirectory-Live`, `MNB-Okta`, `MNB-CoreBanking`, `MNB-Salesforce-CRM-Live`, `MNB-ServiceNow`.  
   **Why:** these sit alongside (not instead of) the Core CSV apps (`MNB-HR`, `MNB-ActiveDirectory`, `MNB-Salesforce-CRM`) — you retire the CSV ones deliberately in Lessons 207–210, not by deleting them now.  
   **Expect:** all six enterprise Applications visible in the list.

6. Accept that `IdentityTrigger` and `CertificationDefinition` objects can soft-fail on first import via MCP.  
   **Why:** some object types need their referenced Workflow/Application to exist first, or need a plugin-side importer not wired up yet — Lesson 248 (SSD Export & Promote) teaches the real import order.  
   **Expect:** `seed-enterprise.sh` finishes with warnings but no hard stop; move on.

7. Cross-check one more persona by hand: find `sanjay.kapoor` in `identity-master.json` and note his `userId` (`MNB00006`) — he's `priya.wire`'s manager per `managerUserId`, and Lesson 214 will lean on this exact relationship to prove manager-hierarchy correlation later.  
   **Why:** knowing a manager relationship exists in the master file before you ever see it resolved in a cube saves real debugging time when a later lesson's manager field comes back blank.  
   **Expect:** `sanjay.kapoor`'s `userId` matches `priya.wire`'s `managerUserId`.

## If it fails

- **Generator errors "missing lab-data/enterprise/identity-master.json"** — not at repo root, or file deleted; `git status` / `git checkout` it back.
- **`seed-enterprise.sh` can't reach MCP** — confirm `mnb-iiq-mcp` is running and `IIQ_MCP_URL`/`MCP_API_KEY` match what `up.sh` printed.
- **Samba seed step does nothing** — `mnb-samba-ad` isn't healthy yet (2+ minutes on first boot); re-run `./tools/lab/enterprise/seed-samba.sh` once `docker ps` shows it healthy.
- **Applications imported but attributes look stale** — you edited `identity-master.json` after a previous seed; re-run the generator *and* `seed-enterprise.sh` together.

## You are done when

The six enterprise Applications exist in IIQ, the `generated/` folder has fresh timestamps matching your last edit to `identity-master.json`, and you can point to Helen's `userId` (`MNB00001`) as the thread tying her HCM worker record, LDIF entry, and Keycloak user together.

## Control note

- **Control:** Identity source-of-truth governance (single master feed, no fixture drift).
- **Owner:** IAM Ops / HR data steward.
- **SLA (lab):** regenerate + reseed in the same change window as any `identity-master.json` edit.
- **Evidence:** `~/iiq-lab-evidence/sandbox/202/` — generator output, seed script log, Application list screenshot.

## Quick check

1. What file is the single source of truth for every persona? → `lab-data/enterprise/identity-master.json`.
2. Which script fans it out into six connector-native shapes? → `generate-identity-artifacts.py`.
3. Why leave `MNB-HR`/`MNB-ActiveDirectory`/`MNB-Salesforce-CRM` (CSV) in place? → they're retired deliberately in later lessons, not deleted here.

## Navigate

- Previous: Lesson 201
- Next: Lesson 203
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
