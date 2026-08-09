# Lesson 230 — Troubleshoot a Failed Provision

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lessons 204, 208, 222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 47

> **Why:** Most real IIQ incidents aren’t “the product is broken” — they’re a bad DN, an expired credential, or a plan referencing an attribute the target doesn’t have.

## What this is

When provisioning fails, beginners often restart containers or re-click Approve. Operators do something else: **read the error surface**, classify the failure, fix the cause, **retry the same transaction**.

This lesson deliberately breaks three paths one at a time:

| Break | What you sabotage | Error shape you’ll learn |
| --- | --- | --- |
| **#1 LDAP bind** | Wrong OpenLDAP bind password | `INVALID_CREDENTIALS` / bind failure |
| **#2 JDBC credential** | Wrong Core Banking DB password | `SQLException` / auth denied |
| **#3 Malformed plan** | Bogus attribute name in a plan | Schema / attribute-not-found |

You will find each error in **Provisioning Transaction detail** and/or **Task Result stack trace**, fix it, and get **Committed** on retry.

Leave with a personal triage card: *where do I look first?*

## Know these

```text
Symptom: access didn't land / disable didn't stick
  → Provisioning Transactions (list + DETAIL)
  → Task Result stack trace (full text)
  → IdentityRequest / work-item history (who approved what)
  → Application → Test Connection
  → Classify: auth vs schema vs network vs process
  → Fix cause → retry SAME transaction (or re-run plan)
  → Confirm Committed + target proof
```

| Failure class | Typical text | First place to look |
| --- | --- | --- |
| Bad LDAP bind | `INVALID_CREDENTIALS`, bind failed | PT detail + OpenLDAP Application password |
| Bad JDBC auth | `SQLException`, password authentication failed | Task Result + Core Banking Application password |
| Bad plan / schema | Unknown attribute, schema violation | Task Result — **different** wording than auth |
| Stale pool | Test Connection green, provision still fails | Restart task / recycle connector cache |
| Wrong LCM process | Approvals done, no plan / wrong owner | IdentityRequest trail + Lifecycle Manager map (Lesson 222) |

| Term | Plain English |
| --- | --- |
| **Test Connection** | App config can bind/connect *right now* |
| **Provisioning Transaction** | One attempted change on a target |
| **IdentityRequest trail** | Who requested/approved before the plan ran |
| **Retry** | Re-execute after fixing root cause |
| **Connection pool cache** | Old bad password may linger until recycle |

- **Wrong way:** Assuming Test Connection green means the next provision will succeed — pools can mask a fix until recycle.
- **Wrong way:** Reading only the PT list row — full stack often lives in Task Result detail.
- **Wrong way:** Changing a *different* Application than the plan targets (similar names confuse).
- **Wrong way:** Leaving the lab broken — always restore correct passwords before you finish.
- **Wrong way:** Debugging only the connector when the IdentityRequest shows the wrong workflow/approver — process bugs look like “provision failed.”

## Intent

- Break OpenLDAP provisioning with a bad bind password; read the error; fix; retry to Committed.
- Break JDBC Core Banking credentials; read that distinct error; fix; retry.
- Break a plan with a bogus attribute; confirm a third error shape; revert; succeed.
- Write a three-line triage card under evidence.

## Before you start

- [ ] `MNB-OpenLDAP` and Core Banking app (`MNB-Application-CoreBanking` / your live name) currently green
- [ ] Correct seed passwords on hand (OpenLDAP bind `admin` / admin secret; JDBC user `mnb` / password `mnb` — confirm against your lab docs if customized)
- [ ] A repeatable provisioning action available (retry a PT, request an LDAP-backed entitlement, or a small disable from Lesson 219 pattern)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/230
```

> **Watch out:** You are about to break production-like connectors on purpose. Restore every password before leaving the lesson.

## Do this

### Task 1 — Break #1: bad LDAP bind password

1. **Applications → Application Definition → MNB-OpenLDAP**  
2. Change the bind / manager password to a **wrong** value  
3. **Save**  
4. Trigger a provisioning action that touches OpenLDAP (e.g. request an OpenLDAP-backed entitlement for a test user, or retry a pending LDAP PT)  

- **Expect:** action fails.

### Task 2 — Read the LDAP error surface

1. **Setup → Provisioning Transactions** → find the **Failed** row  
2. Open **detail** (not just the list)  
3. Copy the exact error text  

- **Expect:** LDAP `INVALID_CREDENTIALS` / bind failure language.

Screenshot / paste under evidence as `break1-ldap.txt`.

### Task 3 — Fix LDAP and retry to Committed

1. Restore correct bind password (`admin` / your seed)  
2. **Test Connection** → green  
3. Retry the failed transaction (or re-run the approval / refresh that creates the plan)  

- **Expect:** transaction flips to **Committed**.

If Test Connection is green but retry still fails: recycle the task / connector cache (see If it fails), then retry again.

```text
Break1: bad LDAP bind → PT detail INVALID_CREDENTIALS → restore admin → Committed
```

### Task 4 — Break #2: bad JDBC credential

1. Open Core Banking Application definition  
2. Change `password` from `mnb` to a wrong value  
3. **Save**  
4. **Test Connection**  

- **Expect:** immediate connection failure — JDBC/driver exception, **different shape** than LDAP bind text.

Save the Test Connection error text as `break2-jdbc-testconn.txt`.

### Task 5 — Attempt JDBC provisioning / see Task Result

Trigger a JDBC-touching action (e.g. disable a Core Banking account via a small leaver-style refresh, or any provision against that app).

Open the **Task Result** for the provisioning / aggregation task — read the stack trace.

- **Expect:** `SQLException` / auth-denied style message — distinct from Task 2’s LDAP text.

Save as `break2-jdbc-taskresult.txt`.

### Task 6 — Fix JDBC and retry

1. Password back to `mnb`  
2. **Test Connection** green  
3. Retry provision  

- **Expect:** provisioning succeeds / Committed.

```text
Break2: bad JDBC password → TestConn + TaskResult SQLException → restore mnb → Committed
```

### Task 7 — Break #3: malformed plan (bogus attribute)

Goal: force a **schema** failure, not an auth failure.

Practical approaches (pick one your UI allows):

- Temporarily add a provisioning policy / AttributeRequest for a **non-existent** attribute on Core Banking (valid columns are typically `account_id`, `username`, `email`, `employee_id`, `status`, `entitlement` — invent `notARealColumn`)  
- Or edit a role/workflow plan step to request that bogus attribute  

Trigger the plan.

- **Expect:** schema / attribute-not-found error — **third** distinct failure shape, not a connection error.

Save as `break3-schema.txt`.

> **Tip:** Compare the three files side by side — auth vs auth-other-driver vs schema. That comparison *is* the lesson.

### Task 8 — Revert malformed change and succeed

1. Remove the bogus attribute request / restore the policy  
2. Re-run  
3. Confirm **Committed**  

```text
Break3: bogus attribute → TaskResult schema error → revert → Committed
```

### Task 9 — Write your triage card

Under `~/iiq-lab-evidence/sandbox/230/triage-card.txt`:

```text
1) <what you broke> → <where error lived> → <fix> → <retry result>
2) ...
3) ...

First places I look next time:
- PT detail
- Task Result stack
- IdentityRequest / approval trail (process vs connector)
- Test Connection
- Confirm I edited the SAME Application the plan targets
```

Optional: open the IdentityRequest from Lesson 222 for `priya.wire` and note how you’d distinguish “connector auth failed” from “wrong workflow / never provisioned.”

- **Expect:** triage card saved; you can name process vs connector as separate classes.

## If it fails

| Symptom | Fix |
| --- | --- |
| Test Connection passes, provision still fails | Connector connection pool cache — restart failing task or bounce connector cache via Debug; retry |
| No error text on PT list row | Open transaction **detail**; full stack often in Task Result |
| Fix doesn’t take effect | Confirm Application **Save**; confirm you edited the app the plan targets |
| Lab left broken for later lessons | Re-verify both Test Connections green before you stop |
| Can’t trigger a provision | Reuse Lesson 222 approval retry or a disposable entitlement request |

## You are done when

- [ ] All three induced failures diagnosed from real error surfaces  
- [ ] All three fixed and confirmed Committed on retry  
- [ ] Three-line triage card saved  
- [ ] Both connectors Test Connection **green** again  

## Control note

- **Control:** Provisioning failure triage and connector credential hygiene  
- **Owner:** IAM Ops (connector config) + app owners (target credentials)  
- **SLA (lab):** Same session; production credential outages should be caught by connector health checks before they hit a provisioning queue  
- **Evidence:** `~/iiq-lab-evidence/sandbox/230/` — three break/fix/retry lines, error-text screenshots, triage card  

## Quick check

1. Where does a truncated PT row’s full error often live? → Task Result stack trace / PT detail  
2. Why do LDAP and JDBC credential failures look different? → Different connector/driver error shapes for the same root cause (bad secret)  
3. What’s a third failure class beyond bad credentials? → Malformed plan / non-existent target attribute  
4. Why can Test Connection lie after a fix? → Connection pool may still hold the old credential  
5. When is “provision failed” actually a process bug? → IdentityRequest shows wrong workflow / never reached `provisionProject` (Lesson 222)  

## Feedback

Could you triage “provision failed” by naming your first three clicks without this page? If one break didn’t produce a clear error, note which surface was empty (PT list vs detail vs Task Result) — that tells us where the lesson should point harder next time.

## Navigate

- Previous: [Lesson 229](229-cert-remediation-live.md)
- Next: [Lesson 231](231-audit-reports-live.md)
- Theory: [Lesson 256 — Connector Registry](256-connector-registry-theory.md) (`featuresString` / what a connector can honestly provision)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
