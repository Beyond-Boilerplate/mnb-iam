# Lesson 243 — Forms & Field Validation

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lessons 221–222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 94

> **Why:** Forms stop requesters from submitting garbage. A blank or one-word “business justification” is useless when someone later asks why access was granted.

## What this is

An IIQ **Form** is the structured capture of requester metadata (justification, change ticket, cost center) onto an **IdentityRequest** — before approvals start. Stock Access Request often accepts free-text comments with no length or pattern check. That is decoration, not a control.

Nothing for this drill is pre-built for you. You will:

1. Create a **disposable** identity (`lab.forms1` — never Helen / Priya / Marcus)  
2. Create **`MNB-Form-AccessRequest-Extras`** from scratch with two validated fields  
3. Attach it to a **live** Wire / Request Access path  
4. **Fail** a short justification, then **pass** a real one  
5. Prove the IdentityRequest stored your fields  
6. Export scrubbed XML to `config/Form/` for Lesson 248  

| Form concept | Plain English | Meridian example |
| --- | --- | --- |
| **Identity Request form** | Extra fields during Manage Access / Request Access | Justification + change ticket |
| **Provisioning Policy form** | Create/modify account attributes on an Application | OpenLDAP Create (Lesson 217) — not this drill |
| **Validation script** | Runs on submit; must return `String` error or `null` | Min length 20 on justification |
| **FieldValue rule** | Optional default for a single field | Prefill ticket prefix `MNB-` |

> **Watch out:** Returning `false` or throwing from BeanShell validation raises a generic error page — not your message. Always `return "…message…";` or `return null;`.

## Know these

```text
Create disposable lab.forms1 + manager
  → Confirm requestable MNB-Bundle-Wire-Initiator (or build per 216/221)
  → Confirm LCM → MNB-Workflow-Access-Approval (or OOTB manager,owner)
  → Create MNB-Form-AccessRequest-Extras (justification + changeTicket)
  → Add validation (min 20 chars + MNB-[0-9]{4,} regex)
  → Attach form to Wire / Access Request path (narrow scope)
  → Request as/for lab.forms1 with "need it" → blocked
  → Resubmit with ≥20 char justification + MNB-24001 → IdentityRequest created
  → Export scrubbed Form XML → config/Form/
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Form object** | Named UI definition stored in IIQ | `MNB-Form-AccessRequest-Extras` |
| **businessJustification** | Why access is needed (audit text) | Min **20** characters |
| **changeTicket** | CAB / ITSM link | Pattern `MNB-[0-9]{4,}` e.g. `MNB-24001` |
| **Attach point** | Where LCM/app policy loads the form | Wire request form / LCM extras — not “hope comments” |
| **Fail-then-pass** | Reject proof **and** accept proof | Screenshots of both |

- **Wrong way:** Hoping requesters paste tickets into comments.  
- **Wrong way:** Attaching a broken form **globally** so every request in the bank fails.  
- **Wrong way:** Using Helen / Priya / Marcus as the subject — keep shared personas for certs/SoD.  
- **Wrong way:** Assuming a Form already exists under `config/Form/` — that folder is empty until you export.  
- **Wrong way:** Only proving the happy path — auditors want the reject screenshot too.

## Intent

- Build `MNB-Form-AccessRequest-Extras` from zero with real validation.  
- Attach it narrowly to a live Access Request path.  
- Prove reject (`need it`) then accept (≥20 chars + `MNB-24001`).  
- Leave scrubbed XML ready for SSD promotion (Lesson 248).

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — login as `spadmin` / `admin`
- [ ] Mailpit open (optional for this lesson): [http://localhost:8025](http://localhost:8025)
- [ ] HCM mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] You completed Lessons **221–222** ideas (requestable Wire role + LCM approval map). You will **re-check** both — do not assume they survived.
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/243
```

## Do this

### Task 1 — Create a disposable identity (from scratch)

Never use Helen, Priya, Marcus, or Sanjay as the form-test subject.

1. From the **repo root** on your Mac:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.forms1 Lab Forms \
  lab.forms1@meridiannb.com 'Bank Operations'
```

2. Confirm HCM:

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.forms1 \
  | python3 -m json.tool | grep -E 'userName|email|active|status|department'
```

- **Expect:** `userName` `lab.forms1`, `active` true.

3. In IIQ as `spadmin`:
   - Run **Account Aggregation** on **`MNB-Workday`** → Task Result **Complete**
   - **Setup → Tasks → Refresh Identity Cube** — include `lab.forms1`, promote attributes → **Run Now** → **Complete**
4. **Identities → Identity Warehouse** → open `lab.forms1`
5. Set **Manager** to **`sanjay.kapoor`** → **Save** → re-open and confirm

- **Why:** Manager Approval (Lesson 222) needs a real manager; disposable cubes keep cert personas clean.
- **Expect:** cube `lab.forms1` with manager `sanjay.kapoor`.

Screenshot the identity header under evidence.

### Task 2 — Confirm the live request path (assume nothing)

The form is useless if Request Access does not launch a real approval workflow or the Wire role is not requestable.

#### 2a — Requestable role

1. **Setup → Roles** → search `MNB-Bundle-Wire-Initiator`
2. If missing: build IT + business Wire Initiator per Lessons **216 / 221** (do not invent a third naming scheme)
3. Confirm **Requestable** / Available in Access Request is **ON**

#### 2b — Lifecycle Manager map

1. Gear → **Lifecycle Manager** → **Business Processes**
2. Confirm both rows (or set them):

| Lifecycle Manager row | Must show |
| --- | --- |
| **Access Request** | `MNB-Workflow-Access-Approval` |
| **Roles Request** | `MNB-Workflow-Access-Approval` |

3. **Save** → re-open and confirm  

**Fallback:** both rows on **`LCM Provisioning`** with `approvalScheme=manager,owner` and `approvalMode=serial` (Lesson 222). Note which path under evidence.

- **Why:** Form validation runs on submit; approvals prove the request actually entered governance.
- **Expect:** LCM map confirmed before any form attach.

### Task 3 — Inventory forms (name what exists)

You cannot attach what you cannot name. Do not assume `MNB-Form-*` is already there.

1. **Debug → Forms** (or **Setup → Forms** if your build shows it)
2. Search `Identity`, `Access`, `LCM`, `Wire`, `Provision`
3. Write under evidence at least three rows:

```text
Form name | Owner / unknown | Notes
----------|-----------------|------
…         | …               | OOTB / app policy / none
```

4. Confirm **`MNB-Form-AccessRequest-Extras` does not exist yet** (or delete a broken prior attempt and recreate in Task 4)

- **Why:** Duplicate “justification” fields with three spellings is how audits fail.
- **Expect:** inventory file saved; you know you are creating a new Meridian form.

### Task 4 — Create `MNB-Form-AccessRequest-Extras` from scratch

1. **Debug → Forms → New Form** (or Create Form in Setup)
2. Set exactly:

| Field | Value |
| --- | --- |
| **Name** | `MNB-Form-AccessRequest-Extras` |
| **Owner** | `spadmin` |
| **Description** | `Meridian Access Request extras: businessJustification (min 20) + changeTicket (MNB-[0-9]{4,}). Narrow attach — Lesson 243.` |

3. Add field **`businessJustification`**:
   - Type: **Textarea** (or String if Textarea unavailable)
   - **Required:** yes
   - Display / help: `Explain business need (minimum 20 characters). Example: Need Wire Initiator to process Commercial Banking client wires this quarter.`
4. Add field **`changeTicket`**:
   - Type: **String**
   - **Required:** yes
   - Display / help: `Change ticket pattern MNB-#### (four or more digits). Example: MNB-24001`
   - Optional default / FieldValue: static `MNB-` so the requester only completes digits
5. **Save**

- **Why:** These two fields are the examiner-grade metadata Meridian expects on privileged / payments requests.
- **Expect:** Form object saved with both fields and help text visible when editing.

> **Tip:** Field names are intentional — use `businessJustification` and `changeTicket` exactly so Lesson 248 exports and examiner drills match.

### Task 5 — Add validation (the control)

Help text without reject behavior is decoration.

#### 5a — Justification min length

On `businessJustification`, add a **Validation** script (BeanShell / rule per UI):

```java
// Meridian Lesson 243 — min length on businessJustification
String v = value == null ? "" : value.toString().trim();
if (v.length() < 20) {
  return "Justification must be at least 20 characters — explain business need, not just \"need access\".";
}
return null;
```

#### 5b — Ticket regex

On `changeTicket`, add validation:

```java
// Meridian Lesson 243 — change ticket pattern
String v = value == null ? "" : value.toString().trim();
if (!v.matches("MNB-[0-9]{4,}")) {
  return "Change ticket must match MNB-[0-9]{4,} (example: MNB-24001).";
}
return null;
```

6. **Save** the form  
7. Write expected error strings under evidence (copy the return messages above)

- **Why:** Validation rejects before Manager Approval — garbage never becomes an IdentityRequest.
- **Expect:** scripts return `String` on fail, `null` on pass; form saves without DTD errors.

> **Watch out:** Do **not** `return false;` or `throw` — you will get a generic error instead of your message.

### Task 6 — Attach the form to the Wire / Access Request path (narrow)

Global attach can block every request in the bank. Scope to Wire first.

1. Prefer one of these attach points (use what your 8.5 UI exposes — screenshot which):

| Preference | Where |
| --- | --- |
| **Best for lab** | Application **`MNB-WirePortal`** (or Core Banking Wire path) → Provisioning Policies / Request / Modify form → reference **`MNB-Form-AccessRequest-Extras`** |
| **Alternate** | Gear → **Lifecycle Manager** → Forms / Access Request configuration → add extras form for role requests |
| **Last resort** | Workflow early **Form** step on `MNB-Workflow-Access-Approval` that collects the two fields before Approvals |

2. Screenshot the attachment point  
3. Write rollback under evidence:

```text
Rollback: detach MNB-Form-AccessRequest-Extras from <exact attach point>
```

- **Why:** Narrow scope limits blast radius if validation is wrong.
- **Expect:** next Request Access for Wire shows your two fields (or Form preview proves them if UI only shows after cart).

If the form never appears on Request Access after attach: use **Debug → Forms →** open `MNB-Form-AccessRequest-Extras` → **Preview** (if available) for Task 7 logic, then fix attach before calling the lesson done — Preview alone is not enough for “You are done when.”

### Task 7 — Fail then pass on a live request

Use **request on behalf** as `spadmin` for `lab.forms1` if pass-through login is awkward.

#### 7a — Fail (too short)

1. **Request Access** → subject **`lab.forms1`**  
2. Select **`MNB-Bundle-Wire-Initiator`**  
3. Fill:
   - `businessJustification` = `need it`
   - `changeTicket` = `TEST`
4. Attempt **Submit**

- **Expect:** blocked inline with **your** validation message(s) — not a blank IdentityRequest, not a stack-trace page.
- **Why:** reject evidence is half the control proof.

Screenshot the error under `~/iiq-lab-evidence/sandbox/243/reject.png` (or equivalent).

#### 7b — Pass (valid metadata)

1. Same cart / new request for `lab.forms1` + Wire Initiator  
2. Fill exactly:

```text
businessJustification: Need Wire Initiator access to support Commercial Banking client onboarding wires this quarter.
changeTicket: MNB-24001
```

3. **Submit**  
4. Note **IdentityRequest** id  
5. Open the IdentityRequest and confirm `businessJustification` / `changeTicket` (or form answers) are stored

Write under evidence:

```text
IdentityRequest id: _______________
Subject: lab.forms1
Role: MNB-Bundle-Wire-Initiator
businessJustification length: ≥20
changeTicket: MNB-24001
Reject proven: yes (need it / TEST)
```

- **Expect:** request accepted into approval / provisioning path; fields visible on the IdentityRequest.
- **Why:** examiners ask for justification + ticket on the grant — the IdentityRequest *is* the answer.

You do **not** need to finish Manager→Owner approval for form proof (Lesson 222 already covered that). Cancel lingering work items if you want a clean inbox — optional.

### Task 8 — Export scrubbed Form XML

1. Debug → export **`MNB-Form-AccessRequest-Extras`** (or Object Exporter)  
2. Save to (name matches the Form object):

```text
config/Form/MNB-Form-AccessRequest-Extras.xml
```

3. Strip instance attributes before commit (same scrub as `tools/lab/scripts/sync_iiq_config.py`):
   - Remove `id=`, `created=`, `modified=`, `significantModified=` on the Form root and nested objects  
   - On `<Reference …>`, keep `class` + `name`, drop `id`  
4. Optional helper from repo root (if MCP is up):

```bash
export MCP_API_KEY=mnb-lab-mcp-key
./tools/lab/scripts/sync-iiq-config.sh --write
git diff -- config/Form/
```

5. Confirm file re-imports: Debug → Import from that path (or leave for Lesson 248 `importdynamic`)

- **Why:** UI-only forms die on `docker down -v`; `config/Form/` is what Lesson 248 promotes.
- **Expect:** clean XML under `config/Form/` with no instance ids.

Save export path + IdentityRequest id under evidence.

## If it fails

| Symptom | Fix |
| --- | --- |
| Cube `lab.forms1` missing | Re-run HCM joiner; Aggregate Workday; Refresh Identity Cube |
| Form never appears on Request Access | Task 6 — wrong attach point; re-check Wire policy / LCM Forms; screenshot attach |
| Generic error page on submit | Validation returned `false`/threw — change to `String` / `null` (Task 5) |
| Valid submit still blocked | Trim whitespace in scripts; confirm length ≥20 after trim; ticket must be `MNB-` + ≥4 digits |
| `TEST` accepted as ticket | Regex validator not attached to `changeTicket` — re-open form field |
| No IdentityRequest on “pass” | Submit never succeeded — fix validation/attach; do not count a blocked attempt |
| Used Helen/Priya/Marcus | Stop — create `lab.forms1` and restart from Task 1 |
| Broke all Access Requests bank-wide | Execute Task 6 rollback; re-attach only to Wire |

## You are done when

- [ ] `MNB-Form-AccessRequest-Extras` exists (you created it) with both fields + validation  
- [ ] Form attached on a **narrow** Wire / Access Request path (rollback note written)  
- [ ] Reject proven for `need it` / `TEST` with **your** message  
- [ ] Pass proven with ≥20-char justification + `MNB-24001` and a real **IdentityRequest** id  
- [ ] Scrubbed XML under `config/Form/`  
- [ ] Evidence under `~/iiq-lab-evidence/sandbox/243/`  

## Control note

- **Control:** Business-justification + change-ticket quality gate on access requests  
- **Owner:** IAM Engineering + Access Governance  
- **SLA (lab):** Sub-20-character justifications and non-`MNB-####` tickets never create an IdentityRequest  
- **Evidence:** `~/iiq-lab-evidence/sandbox/243/` + `config/Form/MNB-Form-AccessRequest-Extras.xml`
- **Out of scope:** Full Manager→Owner completion (Lesson 222); SSD promote of the whole arc (Lesson 248)

## Quick check

1. What must a BeanShell validation script return on failure? → A **String** error message (not `false` / throw)  
2. What two field names does Meridian use here? → `businessJustification`, `changeTicket`  
3. What ticket pattern is required? → `MNB-[0-9]{4,}`  
4. Why scope attach to Wire first? → Bad global attach blocks every Access Request in the bank  
5. What proves the control to an examiner? → Reject screenshot **and** IdentityRequest showing both fields  

## Feedback

Could you rebuild `MNB-Form-AccessRequest-Extras` from a wiped Forms list (create → validate → narrow attach → fail → pass → export) without this page?

If something failed, note the **task number**, what you expected, and what you saw (especially validation message vs generic error, and whether the form appeared on Request Access).

## Navigate

- Previous: [Lesson 242](242-workflow-lcm-customize.md)
- Next: [Lesson 244](244-quicklinks-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
