# Lesson 240 — Logical Application Over Live Apps

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lessons 209–210, 227–229 (cert / remediation ideas)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 85

> **Why:** Logical apps give certifiers one surface for many connectors — but a decision against the logical account still has to remediate on the real tier account, or the revoke is theater examiners will catch.

## What this is

A **Logical Application** is IIQ’s composite-view connector. It does **not** talk to Wire or CRM itself. It stitches accounts already aggregated from tier apps into one virtual account per identity using a **composite / correlation** definition (and often a composite rule).

You will build **`MNB-Logical-Banking-Suite`** from scratch over:

| Tier | Application | What it contributes |
| --- | --- | --- |
| Wire | `MNB-WirePortal` (Web Services — Lesson 209/237) | `entitlements` / wire lifecycle |
| CRM | `MNB-Salesforce-CRM-Live` (SCIM — Lesson 210/238) | `groups` / CRM lifecycle |

Disposable subject: **`lab.logical1`** with real accounts on **both** tiers (never Helen / Priya / Marcus as the write/revoke subject).

```text
Certifier sees: one MNB-Logical-Banking-Suite row
Remediation must hit: MNB-WirePortal and/or MNB-Salesforce-CRM-Live
Logical app itself: cannot provision
```

## Know these

```text
Hire lab.logical1 → ensure Wire + CRM accounts (POST mocks if needed)
  → Aggregate MNB-WirePortal + MNB-Salesforce-CRM-Live
  → Create Logical Application MNB-Logical-Banking-Suite
       tiers = Wire + CRM ; composite key = username / userName
  → Composite / correlation rule (or UI composite definition)
  → Aggregate logical app → composite account on cube
  → Targeted cert (228 pattern) on logical app → Revoke CRM group
  → PT targets MNB-Salesforce-CRM-Live (not logical)
  → curl CRM proves group/active change
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Tier application** | Real connector with inventory | Wire, CRM Live |
| **Logical application** | Composite view only | `MNB-Logical-Banking-Suite` |
| **Composite key** | Attribute that lines tiers up | `username` / `userName` = `lab.logical1` |
| **Composite rule** | BeanShell/UI logic that builds the logical account | Map wire entitlements + CRM groups onto one schema |
| **Remediation target** | Where revoke actually writes | Tier app PT — never the logical shell |

- **Wrong way:** Assuming revoke against the logical app provisions — logical apps are composite/read-only.  
- **Wrong way:** Building the logical app before both tiers have accounts for the subject.  
- **Wrong way:** Correlating Wire on `employeeId` and CRM on `externalId` to different cubes — composite needs one identity.  
- **Wrong way:** Using Priya as the revoke subject — use `lab.logical1`.  
- **Wrong way:** Skipping tier re-agg — stale tiers make empty logical accounts look like a composite-rule bug.

## Intent

- Build `MNB-Logical-Banking-Suite` from an empty Application list entry.  
- Prove `lab.logical1` shows one composite account with Wire + CRM attributes.  
- Run a logical-scoped cert decision (revoke) and prove PT + mock hit the **CRM tier**.  
- Leave evidence under `~/iiq-lab-evidence/sandbox/240/`.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] `MNB-WirePortal` is **Web Services** aggregating (Lesson 209/237) — not only CSV  
- [ ] `MNB-Salesforce-CRM-Live` aggregating (Lesson 210)  
- [ ] Mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] You know Targeted cert mechanics (Lesson 228) and remediation/PT ideas (Lesson 229/230) — this lesson points at those flows; you still execute revoke proof here.
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/240
```

## Do this

### Task 1 — Create disposable `lab.logical1`

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.logical1 Lab Logical \
  lab.logical1@meridiannb.com 'Bank Operations'
```

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.logical1 \
  | python3 -m json.tool | grep -E 'userName|email|active|status'
```

1. Aggregate **`MNB-Workday`** → Complete  
2. **Refresh Identity Cube** for `lab.logical1` → Complete  
3. Confirm cube exists; set `userId` = `lab.logical1` if blank  

- **Why:** composite view needs a clean subject with two tier links you control.
- **Expect:** Warehouse cube `lab.logical1` before any tier POSTs.

### Task 2 — Ensure Wire tier account exists

```bash
curl -s -X POST http://localhost:8091/users \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "wp-lab-logical1",
    "username": "lab.logical1",
    "email": "lab.logical1@meridiannb.com",
    "employeeId": "lab.logical1",
    "active": true,
    "entitlements": ["WIRE_INIT"]
  }' | python3 -m json.tool
```

If you already have Create Account wired (Lesson 237), you may Create Account from IIQ instead — same native id `wp-lab-logical1`.

```bash
curl -s http://localhost:8091/users/wp-lab-logical1 | python3 -m json.tool
```

1. Aggregate **`MNB-WirePortal`** → Complete  
2. Open `lab.logical1` → confirm Wire link + `WIRE_INIT`  

Save curl as `tier-wire.json`.

- **Why:** logical composite cannot invent Wire inventory — tier must exist first.
- **Expect:** correlated Wire account on the cube.

### Task 3 — Ensure CRM tier account exists

```bash
curl -s -X POST http://localhost:8091/crm/scim/v2/Users \
  -H 'Content-Type: application/json' \
  -d '{
    "userName": "lab.logical1",
    "externalId": "lab.logical1",
    "email": "lab.logical1@meridiannb.com",
    "givenName": "Lab",
    "familyName": "Logical",
    "active": true,
    "groups": [{"display": "CRM-Users"}]
  }' | python3 -m json.tool
```

```bash
curl -s -G 'http://localhost:8091/crm/scim/v2/Users' \
  --data-urlencode 'filter=userName eq "lab.logical1"' \
  | python3 -m json.tool
```

1. Aggregate **`MNB-Salesforce-CRM-Live`** → Complete  
2. Confirm CRM link on `lab.logical1` with group `CRM-Users`  

Save as `tier-crm.json`. Note CRM `id` (e.g. `crm-lab.logical1`).

- **Why:** revoke proof later needs a live CRM entitlement to remove.
- **Expect:** both tier links on one cube before Task 4.

### Task 4 — Create Logical Application `MNB-Logical-Banking-Suite`

1. **Applications → Application Definition → New → Logical Application** (or type **Logical** / Composite — wording varies by IIQ skin)  
2. Set exactly:

| Field | Value |
| --- | --- |
| **Name** | `MNB-Logical-Banking-Suite` |
| **Owner** | `spadmin` |
| **Description** | `Composite view: Wire Portal + CRM Live for dual-surface certs. Not a provisioner.` |

3. **Tier applications** / component apps — add:

- `MNB-WirePortal`  
- `MNB-Salesforce-CRM-Live`  

4. Composite / correlation key — align on login-shaped name:

| Tier | Attribute |
| --- | --- |
| Wire | `username` |
| CRM | `userName` |
| Logical account identity | same string → identity `lab.logical1` |

5. Define a minimal **logical schema** that surfaces both tiers, for example:

| Logical attribute | Source idea |
| --- | --- |
| `username` | Wire `username` / CRM `userName` |
| `wireEntitlements` | Wire `entitlements` |
| `crmGroups` | CRM `groups` |
| `wireActive` | Wire `active` |
| `crmActive` | CRM `active` |

Exact composite mapping UI differs by version — map each logical attr to the tier attribute your build’s Logical App editor exposes.

- **Why:** certifiers need named fields from both systems on one row.
- **Expect:** Logical app saved with **two** tiers; no direct connector URL on the logical app itself.

> **Watch out:** Create Identities must stay **OFF**. Logical apps never birth cubes.

### Task 5 — Composite / correlation rule

If your build requires a **Composite Account Rule** / **Logical Provisioning** rule (Setup → Rules, type matching your version’s Logical docs):

1. Create rule `MNB-Rule-Logical-Banking-Suite` (name exact)  
2. Intent of the rule (implement in the editor’s expected API for your version):

```text
For identity lab.logical1 (and others):
  find Wire link on MNB-WirePortal + CRM link on MNB-Salesforce-CRM-Live
  if both present (match username/userName):
    emit one logical account native id = username
    copy wire entitlements → wireEntitlements
    copy crm groups → crmGroups
```

3. Attach the rule on `MNB-Logical-Banking-Suite` (Rules / Composite definition tab)  
4. **Save**

If the Logical Application UI builds composites **without** a separate rule (tier list + attribute map only):

```text
Composite rule: UI composite definition only — no separate Rule object required on this build.
```

Record that under evidence and continue — do not invent a rule type your registry lacks.

- **Why:** empty composites are almost always key mismatch or missing rule attachment — make the join explicit.
- **Expect:** rule attached **or** honest UI-only note saved.

### Task 6 — Aggregate the logical app

1. Re-aggregate **Wire** and **CRM** if anything changed since Task 3  
2. Run **Account Aggregation** on **`MNB-Logical-Banking-Suite`** → Complete  
3. Open `lab.logical1` → **Application Accounts**  

- **Expect:** one **`MNB-Logical-Banking-Suite`** account showing wire entitlements **and** CRM groups (or your mapped logical attrs).

Screenshot composite account → `composite-account.png` (or UI capture).

If empty:

- Confirm both tier links use the **same** username string `lab.logical1`  
- Confirm tiers aggregated after POSTs  
- Re-check composite key / rule attachment  

- **Why:** logical agg reads tier links already on the cube — it is not a second pull from `connector-mock`.
- **Expect:** composite row present before certification.

### Task 7 — Targeted cert on the logical app (228 pattern)

Pointer: full Targeted UI steps live in [Lesson 228](228-targeted-cert-live.md). Execute this scoped variant:

1. **Certifications → Schedule / Generate → Targeted Certification**  
2. Scope: **Application** = **`MNB-Logical-Banking-Suite`** only  
3. Certifier: **Specific Identity** → `helen.ross` (reviewer — not the subject)  
4. Name: `MNB-Logical-Banking-Suite-<today>`  
5. **Generate Now**  

- **Expect:** cert generates; `lab.logical1` appears as **one** combined row (not two separate app campaigns).

Write row count under evidence.

> **Tip:** If generation fails because logical apps are excluded from Targeted in your build, use Application Owner cert (227 pattern) scoped to the logical app, or Manager cert filtered to `lab.logical1` — still decide revoke on the composite row. Note which path you used.

### Task 8 — Revoke CRM-sourced access; prove tier remediation

1. Log in as `helen.ross` / `LabUser1!`  
2. Open the cert → find `lab.logical1`  
3. **Revoke** the CRM group / CRM-sourced entitlement (or the composite line that represents CRM — prefer CRM `CRM-Users` if the UI shows tier-tagged items)  
4. Complete / sign-off enough for remediation to fire (per your build — Lesson 229 remediation phase)  
5. As `spadmin`, open **Setup → Provisioning Transactions**  

- **Expect:** transaction targets **`MNB-Salesforce-CRM-Live`** (or Wire if you revoked Wire — record which).  
- **Expect:** transaction does **not** list `MNB-Logical-Banking-Suite` as the provisioner.

6. Prove on CRM mock (adjust id if needed):

```bash
curl -s -G 'http://localhost:8091/crm/scim/v2/Users' \
  --data-urlencode 'filter=userName eq "lab.logical1"' \
  | python3 -m json.tool
```

If remediation removed group membership or disabled the account, the JSON must show that change. If your connector remove-group path is not wired on CRM Live, accept this lab fallback and document it:

```text
PT targeted MNB-Salesforce-CRM-Live (screenshot/id: ________).
CRM mock group remove not implemented / PT Failed: ________
Manual compensating proof: PATCH active=false on CRM id, re-agg CRM + logical —
still proves logical cert decision routes to tier, not logical provisioner.
```

Prefer real PT success when the tier supports the op; honesty if the mock/connector lacks group remove.

Save PT id + curl (or fallback note) as `remediation-proof.txt`.

- **Why:** the whole point of logical certs is one review surface with **real** tier writes.
- **Expect:** remediation evidence names a **tier** application.

### Task 9 — One-sentence control story + evidence pack

Write `control-story.txt`:

```text
Helen certified lab.logical1 Wire+CRM as one MNB-Logical-Banking-Suite decision;
revoke remediated on MNB-Salesforce-CRM-Live (PT ________), not on the logical app.
```

Confirm folder:

```text
tier-wire.json
tier-crm.json
composite-account screenshot
remediation-proof.txt
control-story.txt
```

- **Expect:** pack shows tier truth → composite view → tier remediation.

## If it fails

| Symptom | Fix |
| --- | --- |
| No composite accounts | Tier keys differ (`employeeId` vs `userName`); align both to `lab.logical1`; re-agg tiers then logical |
| Logical agg empty after tiers OK | Composite rule not attached / UI map incomplete; Task 5 |
| Cert rows empty | Logical not aggregated; or scope wrong app name |
| PT targets logical app and errors | Expected failure mode — remediation must route to tier; fix cert remediation / revoke mapping |
| CRM curl unchanged after revoke | Tier connector lacks remove; use documented fallback PATCH + still keep PT target proof |
| Wire is CSV only | Rebuild WS Wire (209/237) — CSV cannot join this live composite story cleanly |
| Used Priya/Helen as subject | Stop — `lab.logical1` from Task 1 |

## You are done when

- [ ] `MNB-Logical-Banking-Suite` exists with Wire + CRM tiers (you created it)  
- [ ] `lab.logical1` shows one composite account with both tiers’ data  
- [ ] Cert decision recorded on the logical app  
- [ ] Remediation proof names **`MNB-Salesforce-CRM-Live` or `MNB-WirePortal`**, not the logical app  
- [ ] Evidence folder complete  

## Control note

- **Control:** Composite-view certification with correct tier-level remediation  
- **Owner:** IAM Engineering + App Owners (Wire, CRM)  
- **SLA (lab):** Revoke decision routes to real tier same cert cycle  
- **Evidence:** `~/iiq-lab-evidence/sandbox/240/`  
- **Out of scope:** Logical app as a provisioner; multi-tier SoD redesign (224 owns Wire dual-control policy)

## Quick check

1. Can a logical application provision on its own? → No — composite/read-only; plans route to tiers  
2. What must match across tiers? → Composite key (here `username` / `userName`)  
3. What did the logical view save Helen from doing? → Two separate app certs + manual row correlation  
4. Where must revoke land? → Tier PT (`MNB-Salesforce-CRM-Live` / Wire), proven on mock or PT detail  
5. Why `lab.logical1`? → Disposable dual-tier subject; shared personas stay clean  

## Feedback

Could you rebuild a logical app over two live tiers and prove revoke hit the tier — without this page?

If something failed, note the **task number**, whether tier links existed, and the Provisioning Transaction application name (logical vs tier).

## Navigate

- Previous: [Lesson 239](239-itsm-ticket-mock.md)
- Next: [Lesson 241](241-rules-before-after-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
