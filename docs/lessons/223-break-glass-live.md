# Lesson 223 — Break-Glass Access Drill

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~90 minutes  
**Prereq:** Lessons 208, 216, 221–222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 37

> **Why:** Emergency access has to be time-boxed and auditable, or “break glass” is just a permanent backdoor with a dramatic name.

## What this is

**Break-glass** (also called emergency / fire-call access) is what ops uses when production is on fire at 2 a.m. and a slow Manager→Owner wait would make the outage worse.

It is still **governed** access — different rules than Lesson 222 routine Wire Initiator:

| Routine access (Lesson 222) | Break-glass (this lesson) |
| --- | --- |
| Business justification | **Incident id** (`INC-…`) in the justification |
| Unhurried Manager → Owner | **Same approval objects**, decided **back-to-back** (accelerated) |
| Long-lived until mover/leaver/cert | **Short sunset** (minutes in lab) then revoke |
| Normal Mailpit subjects | Mail / request trail must show the **INC** |

Nothing for break-glass is pre-built for you in this drill. You will:

1. Create a **disposable** identity (never Helen / Priya / Marcus)  
2. Promote live entitlement **`WIRE_APPR`** on **`MNB-CoreBanking`** into the catalog  
3. Build an **IT pack** + **requestable business role** from scratch  
4. Confirm Lifecycle Manager still launches your approval workflow  
5. Request with `INC-LAB-001` → approve fast → prove SQL → revoke on a clock  

**Credential custody** (vault passwords) is a later lesson. Here IIQ grants/revokes the **entitlement**; PAM would hold secrets.

> **Watch out:** Do **not** use seeded `MNB-Bundle-BreakGlass-Cloud` for this drill. That pack is PAM-safe oriented and usually has **no** Core Banking / Wire entitlement to query. You build `MNB-Bundle-BreakGlass-WireAppr` yourself.

## Know these

```text
Create disposable identity + Core Banking account row
  → Aggregate → WIRE_APPR in Entitlement Catalog
  → Create MNB-IT-BreakGlass-WireAppr (it) + MNB-Bundle-BreakGlass-WireAppr (business, requestable)
  → Confirm LCM → MNB-Workflow-Access-Approval (or OOTB manager,owner)
  → Request Access (INC-LAB-001) for disposable user
  → Approve Manager + Owner immediately (accelerated)
  → provision → psql shows WIRE_APPR
  → sunset clock → remove role → provision refresh → re-agg
  → psql shows entitlement gone / not WIRE_APPR
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Break-glass** | Emergency elevated access with compensating controls | `WIRE_APPR` via a dedicated requestable role |
| **Incident reference** | Ticket id tying the grant to an outage | `INC-LAB-001` in justification |
| **Sunset / time-box** | Access dies at a planned time | 8 minutes, then you revoke |
| **Accelerated approval** | Same controls, decided immediately | Manager + Owner back-to-back |
| **IT pack vs business role** | Entitlements on **it**; who/requestable on **business** | Same pattern as Lesson 216 Wire Initiator |
| **Revocation** | Remove role + provision + re-agg | SQL must match IIQ |

- **Wrong way:** Soft justification (“need access for project”) with no INC.  
- **Wrong way:** Leaving access after the window — temporary that never ends is permanent.  
- **Wrong way:** Putting entitlements on a **business** role — IIQ will refuse; use an **it** pack + Required Roles.  
- **Wrong way:** Using Helen / Priya / Marcus — later certs and SoD break.  
- **Wrong way:** Assuming Lesson 222’s LCM map is still set — **verify** before you request.

## Intent

- Build break-glass roles from zero against live `WIRE_APPR` on Core Banking.  
- Request with an INC through an auditable (accelerated) approval.  
- Prove grant and revoke on PostgreSQL — not only IIQ UI.  
- Leave an IdentityRequest timeline an incident responder could read.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — login as `spadmin` / `admin`
- [ ] Mailpit open: [http://localhost:8025](http://localhost:8025)
- [ ] HCM mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] Core Banking DB reachable:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select entitlement_code, display_name, risk_tier from mnb_app_entitlements where entitlement_code='WIRE_APPR';"
```

  - **Expect:** one row, `risk_tier` = `critical` (or similar). If the container name differs, run `docker ps` and substitute.

- [ ] You know Lesson 222’s approval idea (Manager then Owner). You will **re-check** the LCM map in this lesson — do not assume it survived.
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/223
```

## Do this

### Task 1 — Create a disposable identity (from scratch)

Never use Helen, Priya, Marcus, or Sanjay as the break-glass subject.

1. From the **repo root** on your Mac:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.breakglass1 Lab Breakglass \
  lab.breakglass1@meridiannb.com 'Bank Operations'
```

2. Confirm HCM:

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.breakglass1 \
  | python3 -m json.tool | grep -E 'userName|email|active|status|department'
```

- **Expect:** `userName` `lab.breakglass1`, `active` true.

3. In IIQ as `spadmin`:
   - **Setup → Tasks** (or Applications → `MNB-Workday` → Aggregate)
   - Run **Account Aggregation** on **`MNB-Workday`**
   - Wait for Task Result **Complete**

4. **Setup → Tasks → Refresh Identity Cube**
   - Filter / include `lab.breakglass1` if your UI allows
   - Enable promote attributes (and correlate if shown)
   - You do **not** need Process events for this hire unless you also want joiner workflow — cube create is enough
   - **Save** → **Run Now** → wait **Complete**

5. **Identities → Identity Warehouse** → search `lab.breakglass1`
   - Open the cube
   - Confirm the identity exists

- **Why:** break-glass needs a throwaway subject so shared personas stay intact for certs/SoD.
- **Expect:** cube `lab.breakglass1` exists.

Screenshot the identity header under evidence.

### Task 2 — Set a manager (required for Manager Approval)

The Manager Approval step needs a real manager on the cube. New HCM joiners often have **no** manager yet.

1. Still on `lab.breakglass1` → edit attributes / **View Identity** editor (pencil / Edit)
2. Set **Manager** to **`sanjay.kapoor`** (Identity name must match exactly)
3. **Save**

4. Re-open the cube and confirm Manager shows Sanjay Kapoor / `sanjay.kapoor`

- **Why:** without a manager, Manager Approval has no owner and the request stalls or self-routes badly.
- **Expect:** manager = `sanjay.kapoor`.

> **Watch out:** Display name alone is not enough — the Manager field must resolve to Identity **`sanjay.kapoor`**.

### Task 3 — Seed a Core Banking account for the disposable user

Provisioning updates an entitlement on an account that **exists**. Create the row yourself so you are not depending on a prior joiner path.

1. Insert a baseline account (low / non-approver entitlement):

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps -c "
INSERT INTO mnb_app_accounts (account_id, username, email, employee_id, status, entitlement)
VALUES ('jdbc-bg-001', 'lab.breakglass1', 'lab.breakglass1@meridiannb.com', 'lab.breakglass1', 'ACTIVE', 'DWRP')
ON CONFLICT (account_id) DO UPDATE
  SET username = EXCLUDED.username,
      email = EXCLUDED.email,
      status = 'ACTIVE',
      entitlement = 'DWRP';
"
```

2. Confirm:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select account_id, username, status, entitlement from mnb_app_accounts where username='lab.breakglass1';"
```

- **Expect:** one row, `entitlement` = `DWRP` (not `WIRE_APPR` yet).

3. In IIQ: Aggregate **`MNB-CoreBanking`** → Task Result Complete  
4. Open `lab.breakglass1` → **Application Accounts**  
   - **Expect:** link to `MNB-CoreBanking` with entitlement `DWRP` (or equivalent after correlate)

- **Why:** you need a live account to raise to `WIRE_APPR` and later prove revoke.
- **Expect:** correlated Core Banking account before any break-glass role exists.

Save the SQL output as `~/iiq-lab-evidence/sandbox/223/before-grant.sql.txt`.

### Task 4 — Promote `WIRE_APPR` into Entitlement Catalog

Roles can only attach entitlements IIQ already knows.

1. Confirm Core Banking schema marks `entitlement` as managed (Lesson 208):  
   **Applications → Application Definition → MNB-CoreBanking → Schema**  
   - Attribute **`entitlement`**: `entitlement=true`, `managed=true`

2. If you just changed schema: Aggregate **`MNB-CoreBanking`** again  

3. **Applications → Entitlement Catalog** (or Manage → Entitlements)  
   - Filter Application = **`MNB-CoreBanking`**  
   - Find **`WIRE_APPR`**

- **Expect:** `WIRE_APPR` listed (display may look like “Wire Portal — Approve”).

If missing:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select * from mnb_app_entitlements;"
```

Re-aggregate; if still empty, run **Account Group Aggregation** only if your build uses a separate group task for JDBC entitlements — for this JDBC app, account aggregation with managed `entitlement` is usually enough. Refresh the catalog view.

- **Why:** empty catalog = you cannot build the IT pack in Task 5.
- **Expect:** you can select `WIRE_APPR` in a role Entitlements picker.

### Task 5 — Create IT pack `MNB-IT-BreakGlass-WireAppr`

Entitlements live on type **it**, not on business roles.

1. **Setup → Roles**  
2. **Create New → Role** (manual Role — not Role Mining)  
3. Set exactly:

| Field | Value |
| --- | --- |
| **Name** | `MNB-IT-BreakGlass-WireAppr` |
| **Display Name** | `MNB IT BreakGlass WireAppr` (optional) |
| **Type** | **it** |
| **Owner** | `spadmin` |
| **Description** | `Break-glass IT pack: Core Banking WIRE_APPR only. Emergency / INC required. Not birthright.` |
| **Disabled** | unchecked |

4. **Entitlements → Add** (prefer **Simple View**):
   - **Application:** `MNB-CoreBanking`
   - Select **`WIRE_APPR` only** — do not add `WIRE_INIT`, `DWRP`, or anything else
5. Confirm the entitlements list shows **only** `WIRE_APPR`
6. **Submit** / Save

- **Why:** stock IIQ supports Entitlements on **it**; business type shows “Entitlements section is not supported.”
- **Expect:** IT role saved with one entitlement.

> **Watch out:** If you see *Entitlements section is not supported*, Type is still **business** — change to **it** and re-add.

### Task 6 — Create requestable business role `MNB-Bundle-BreakGlass-WireAppr`

1. **Setup → Roles → Create New → Role**  
2. Set exactly:

| Field | Value |
| --- | --- |
| **Name** | `MNB-Bundle-BreakGlass-WireAppr` |
| **Type** | **business** |
| **Owner** | `spadmin` |
| **Description** | `Time-boxed emergency Core Banking WIRE_APPR. INC required in justification. Not birthright.` |
| **Disabled** | unchecked |
| **Assignment Rule** | **leave empty** (nobody gets this automatically) |

3. Ignore the Entitlements warning on business type — that is expected  
4. **Required Roles → Modify Required Roles** → add **`MNB-IT-BreakGlass-WireAppr`** only  
5. Turn **Requestable** / **Available in Access Request** **ON** (`requestable=true`)  
6. **Submit** / Save  
7. Re-open the role and confirm:
   - Required Roles lists the IT pack  
   - Requestable is on  

- **Why:** the catalog item people request is the business role; the IT pack carries the live entitlement.
- **Expect:** role searchable later in Request Access.

> **Tip:** Name is intentional and **different** from Lesson 224’s future `MNB-Bundle-Wire-Approver`. Same entitlement value (`WIRE_APPR`), different governance path (emergency vs dual-control SoD).

### Task 7 — Confirm Request Access + Lifecycle Manager map

Do not assume Lesson 222 left the map correct.

#### 7a — QuickLink visible

1. Log out of `spadmin`  
2. Log in as `helen.ross` / `LabUser1!` (or your seed password)  
3. Confirm **Request Access** appears on Home  

If missing: as `spadmin`, confirm QuickLink `MNB-QuickLink-Request-Access` exists (Debug → QuickLink, or import `config/QuickLink/MNB-QuickLink-Request-Access.xml`) and `Self Service` DynamicScope includes workforce.

#### 7b — Lifecycle Manager Business Processes

1. Log back in as `spadmin`  
2. Open the **gear** → **Lifecycle Manager** → **Business Processes** tab  
3. Set both rows to **`MNB-Workflow-Access-Approval`** (create/fix the workflow from Lesson 222 if the name is missing):

| Lifecycle Manager row | Must show |
| --- | --- |
| **Access Request** | `MNB-Workflow-Access-Approval` |
| **Roles Request** | `MNB-Workflow-Access-Approval` |

4. **Save** → re-open and confirm both rows stuck  

**If custom workflow is missing or broken:** use the Lesson 222 fallback — put both rows on **`LCM Provisioning`**, then **Setup → Business Processes → LCM Provisioning → Process Variables** → `approvalScheme=manager,owner` and `approvalMode=serial`. Write under evidence which path you used.

- **Why:** Request Access does not read a workflow name off the Bundle. Wrong map = wrong approvals = Sanjay never sees the item.
- **Expect:** LCM map confirmed before any break-glass request.

### Task 8 — Document the sunset **before** you grant

Pick a short window you can watch (5–10 minutes). Write the clock **before** submit:

```bash
date '+Sunset start: %H:%M:%S'
```

Save under `~/iiq-lab-evidence/sandbox/223/sunset.txt`:

```text
Sunset window: 8 minutes
Start time: <paste from date>
Revoke method: Remove MNB-Bundle-BreakGlass-WireAppr from lab.breakglass1
               + Identity Refresh with provisioning
               + Aggregate MNB-CoreBanking
               + psql proof
Incident: INC-LAB-001
```

- **Why:** without a written sunset, “temporary” becomes forgotten permanent access.
- **Expect:** file saved before Task 9.

### Task 9 — Submit the break-glass request with INC justification

Use **request on behalf** so you are not blocked on pass-through login for a brand-new cube.

1. As `spadmin`, open **Request Access**  
   - If your build has **Request Access for Others** / select identity: choose **`lab.breakglass1`**  
   - If the UI only requests for the logged-in user: log in as `lab.breakglass1` only if pass-through works; otherwise stay on behalf-of as spadmin  

2. Search **`BreakGlass`** or **`WIRE_APPR`** / `MNB-Bundle-BreakGlass-WireAppr`  
3. Select **`MNB-Bundle-BreakGlass-WireAppr`**  
4. Justification — copy exactly (INC is mandatory):

```text
INC-LAB-001 — emergency Core Banking WIRE_APPR during on-call incident
```

5. Submit  
6. Note the **IdentityRequest** id (confirmation page, request history, or Manage Access Requests)

Write under evidence:

```text
IdentityRequest id: _______________
Subject: lab.breakglass1
Role: MNB-Bundle-BreakGlass-WireAppr
Justification includes: INC-LAB-001
```

- **Expect:** request accepted; **no** silent auto-grant of `WIRE_APPR` before approvals finish.

> **Watch out:** Soft text without `INC-LAB-001` fails this control — cancel and resubmit with the INC line.

### Task 10 — Accelerated approval (Manager then Owner, immediately)

Break-glass still uses audited approvals. “Accelerated” means you decide **now**, not that you skip the steps.

#### 10a — Manager Approval as Sanjay

1. Log in as `sanjay.kapoor` / `LabUser1!`  
   **Or** as `spadmin`: **Manage Work Items** → filter owner / assignee `sanjay.kapoor`  
2. Open the Manager Approval for `lab.breakglass1` / BreakGlass  
3. Confirm description looks like custom Manager approval (Lesson 222), not only a stock Owner-only item  
4. **Approve** with comment:

```text
INC-LAB-001 — emergency approval, sunset 8 minutes
```

- **Expect:** request moves to **Owner Approval**.

#### 10b — Owner Approval as spadmin

1. As `spadmin`, open the Owner Approval work item  
2. **Approve** with comment:

```text
INC-LAB-001 — owner ack, time-boxed WIRE_APPR
```

- **Expect:** workflow enters provisioning (`provisionProject` / plan executes).

Timestamps on both steps should be minutes apart — that is the acceleration proof vs a leisurely 222 drill.

Screenshot both approval comments under evidence.

### Task 11 — Mailpit: INC visible

1. Open [http://localhost:8025](http://localhost:8025)  
2. Sort by newest  
3. Search `INC-LAB-001`, `lab.breakglass1`, `sanjay`, or `BreakGlass`

- **Expect:** at least one message whose subject or body includes **`INC-LAB-001`**, **or** you record an honest gap:

```text
Work items exist with INC in justification; Mailpit assignment mail missing INC
because template does not print justification — gap for Lesson 232, not SMTP.
```

- **Why:** auditors want the INC outside IIQ too when mail fires; if the template omits justification, that is a template finding (Lesson 232), not a reason to skip the INC on the request itself.
- **Expect:** screenshot or gap note saved.

> **Tip:** `spadmin` often has **no email** — empty Mailpit for Owner is expected. Sanjay’s assignment mail is the one that matters.

### Task 12 — Prove grant on the live database

1. Aggregate **`MNB-CoreBanking`** again (picks up connector writes)  
2. Open `lab.breakglass1` → Application Accounts → confirm entitlement shows **`WIRE_APPR`**  
3. Ground truth:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select account_id, username, status, entitlement from mnb_app_accounts where username='lab.breakglass1';"
```

- **Expect:** `entitlement` = **`WIRE_APPR`**.

Save as `after-grant.sql.txt`.

If IIQ shows the role but SQL still says `DWRP`:

- **Setup → Provisioning Transactions** → open detail for `lab.breakglass1`  
- Fix Failed/Retry (Lesson 230 pattern) → retry  
- Do not continue to revoke until SQL shows `WIRE_APPR`

### Task 13 — Execute revoke when the sunset elapses

1. Wait until your sunset window ends (or reach T+window on purpose)  
2. As `spadmin`, open `lab.breakglass1`  
3. Remove **`MNB-Bundle-BreakGlass-WireAppr`** (Roles tab → remove / deassign the detected or assigned role)  
4. **Setup → Tasks → Refresh Identity Cube**
   - Include `lab.breakglass1`
   - Enable **provisioning** (`provision=true`)
   - Run Now → Complete  
5. Aggregate **`MNB-CoreBanking`**  
6. Re-check SQL:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select account_id, username, status, entitlement from mnb_app_accounts where username='lab.breakglass1';"
```

- **Expect:** `entitlement` is **no longer** `WIRE_APPR` (back to `DWRP`, empty, or prior baseline — not approver).

Save as `after-revoke.sql.txt`.

> **Watch out:** Role gone in IIQ but SQL still `WIRE_APPR` means provisioning or re-agg was skipped — same failure class as Lesson 218 mover cleanup.

### Task 14 — IdentityRequest timeline for incident response

1. Open the IdentityRequest from Task 9  
2. Confirm you can see in one place:
   - Subject `lab.breakglass1`  
   - Justification with `INC-LAB-001`  
   - Manager approval timestamp + comment  
   - Owner approval timestamp + comment  
   - Provisioning / completion status  
3. Note revoke time from Task 13 Refresh / Provisioning Transaction  

Write final evidence note:

```text
INC-LAB-001
IdentityRequest: ________
Grant SQL: WIRE_APPR at <time>
Revoke SQL: not WIRE_APPR at <time>
Sunset minutes: ________
LCM path used: MNB-Workflow-Access-Approval | OOTB manager,owner
```

- **Expect:** one pack under `~/iiq-lab-evidence/sandbox/223/` an IR lead could follow without asking you.

## If it fails

| Symptom | Fix |
| --- | --- |
| Cube `lab.breakglass1` missing | Re-run HCM joiner; Aggregate Workday; Refresh Identity Cube |
| Manager Approval has no owner | Task 2 — set Manager to `sanjay.kapoor` exactly; resubmit request |
| `WIRE_APPR` not in catalog | Task 4 — managed flag on schema + Aggregate Core Banking |
| Entitlements not supported on role | Type must be **it** for Task 5; business role only gets Required Roles |
| BreakGlass role not in Request Access | Task 6 — Requestable ON; search exact name; LCM Roles Request mapped |
| Only Owner WI for spadmin, no Sanjay | LCM still on stock `LCM Provisioning` with owner-only scheme — redo Task 7b; **resubmit** (old requests do not re-route) |
| SQL stuck on `DWRP` after approve | Confirm `MNB-CoreBanking` Rules → JDBCProvision = `MNB-Rule-JDBC-CoreBanking-Provision` (enterprise seed); then Provisioning Transaction detail / retry (Lesson 230) |
| SQL still `WIRE_APPR` after revoke | Refresh with **provisioning**; re-aggregate Core Banking; confirm role actually removed |
| Mailpit empty | Check Sanjay has an email on cube; Lesson 203 SMTP `mailpit:1025`; Owner/`spadmin` often has no mail |
| Used Helen/Priya/Marcus | Stop — create `lab.breakglass1` and restart from Task 1 |

## You are done when

- [ ] `MNB-IT-BreakGlass-WireAppr` + `MNB-Bundle-BreakGlass-WireAppr` exist (you created them)  
- [ ] Request for `lab.breakglass1` includes **`INC-LAB-001`**  
- [ ] Manager + Owner approvals recorded within minutes  
- [ ] SQL proved **`WIRE_APPR`** after grant  
- [ ] SQL proved **not** `WIRE_APPR` after sunset revoke  
- [ ] Evidence folder has before/after SQL + IdentityRequest id + sunset note  

## Control note

- **Control:** Emergency (break-glass) access with mandatory INC + time-box  
- **Owner:** Security Ops (approval) + IAM Ops (role design + revocation)  
- **SLA (lab):** 5–10 minute sunset; production windows often 4–24 hours with mandatory review  
- **Evidence:** `~/iiq-lab-evidence/sandbox/223/`  
- **Out of scope:** Vault / PAM password checkout (later privileged lesson)

## Quick check

1. What must the justification contain? → Incident id (e.g. `INC-LAB-001`)  
2. Why an IT pack **and** a business role? → Entitlements on **it**; requestable catalog item on **business**  
3. What proves grant/revoke for real? → `psql` on `mnb_app_accounts`, not only the IIQ Roles tab  
4. What does “accelerated” mean here? → Same Manager→Owner steps, decided immediately — not skipped  
5. Why not `MNB-Bundle-BreakGlass-Cloud` for this drill? → It usually has no live Core Banking entitlement to query  

## Feedback

Could you rebuild break-glass from a wiped role list without this page (IT pack → business requestable → INC request → dual approve → SQL → sunset revoke)?  

If something failed, note the **task number**, what you expected, and what you saw (especially SQL entitlement vs IIQ role).

## Navigate

- Previous: [Lesson 222](222-approvals-and-mail.md)
- Next: [Lesson 224](224-sod-wire-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Theory: [256 Connector Registry](256-connector-registry-theory.md) (JDBC Core Banking features for grant/revoke proof)
