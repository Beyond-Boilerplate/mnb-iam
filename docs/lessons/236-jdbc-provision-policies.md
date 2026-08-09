# Lesson 236 — JDBC Create/Disable Policies

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lesson 208  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 64

> **Why:** Aggregation only *reads* Core Banking. Without Create/Disable policies (and SQL that implements them), IIQ cannot open or soft-close an account on leaver — and a hard `DELETE` destroys the audit trail examiners expect to still find.

## What this is

`MNB-CoreBanking` is a `JDBCConnector` against PostgreSQL table `mnb_app_accounts`:

| Column | Role in this lesson |
| --- | --- |
| `account_id` | Native identity (`identityAttribute`) |
| `username` | Display / correlation helper |
| `email`, `employee_id` | Create payload |
| `status` | Lifecycle: `ACTIVE` ↔ `DISABLED` |
| `entitlement` | Governed capability (certs/SoD) — leave alone here |

Seed features already include `PROVISIONING, SYNC_PROVISIONING, ENABLE`. Enterprise seed also attaches baseline rule **`MNB-Rule-JDBC-CoreBanking-Provision`** (Create / Modify entitlement / Disable) so Lessons 217–223 can write Core Banking. This lesson still builds the **Create/Disable provisioning policies** (plan fields) and proves Create→Disable with `psql` — policies alone still do nothing without that rule.

You will:

1. Dry-run parameterized SQL on the live DB  
2. Add **Create** and **Disable** provisioning policies on `MNB-CoreBanking`  
3. Confirm (or re-attach) `MNB-Rule-JDBC-CoreBanking-Provision` on the JDBC provision slot — extend Source only if your seed rule is missing Create/Disable  
4. Hire disposable **`lab.jdbctest`**, Create account → prove `ACTIVE`  
5. Disable the same account → prove `DISABLED` and the row still exists  

## Know these

```text
Dry-run INSERT + UPDATE on mnb_app_accounts (docker exec psql)
  → Applications → MNB-CoreBanking → Provisioning Policies
       Create (fields) + Disable (status=DISABLED)
  → Setup → Rules → MNB-Rule-JDBC-CoreBanking-Provision (JDBCOperationProvisioning)
  → Attach rule on Application → Rules / JDBC Provision
  → Create disposable lab.jdbctest + Create Account
  → psql: status=ACTIVE, row exists
  → Disable account in IIQ
  → psql: status=DISABLED, COUNT(*) still 1  (no DELETE)
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Provisioning Policy** | Which attributes go into the plan for an op | Create fields: `account_id`, `username`, … |
| **JDBCOperationProvisioning rule** | BeanShell that turns the plan into SQL | `INSERT` / `UPDATE status` |
| **Disable vs Delete** | Soft-close vs remove the row | `DISABLED` keeps rehire / audit evidence |
| **Native identity** | Target key IIQ uses on later ops | `account_id` (e.g. `jdbc-lab-jdbctest`) |
| **ENABLE feature** | Connector capability for Enable/Disable | Already on `featuresString` |

- **Wrong way:** Mapping Disable to `DELETE FROM mnb_app_accounts` — loses history and breaks re-correlation on rehire.  
- **Wrong way:** Configuring policies but never attaching a JDBC provision rule — plan looks fine; DB never changes.  
- **Wrong way:** Using Helen / Priya / Marcus as the write subject — pollutes shared personas.  
- **Wrong way:** Proving only IIQ UI “Disabled” without `psql`.  
- **Wrong way:** Assuming Create/Disable **policies** already exist after Lesson 208 — they do not (the JDBC **rule** may already be seeded; policies are still your job).

## Intent

- Author Create + Disable policies on `MNB-CoreBanking` from an empty Policies tab.  
- Confirm the seeded JDBC provision rule (or attach/fix `MNB-Rule-JDBC-CoreBanking-Provision`) implements Create and Disable SQL — never hard `DELETE`.  
- Create a Core Banking row for `lab.jdbctest` and prove `status=ACTIVE` in Postgres.  
- Disable the same account and prove `status=DISABLED` with the row still present.  
- Leave evidence under `~/iiq-lab-evidence/sandbox/236/`.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — login as `spadmin` / `admin`
- [ ] Lesson 208: `MNB-CoreBanking` Test Connection green; you can Aggregate it
- [ ] JDBC container reachable (name may vary — confirm with `docker ps | grep jdbc`):

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select account_id, username, status from mnb_app_accounts order by account_id limit 6;"
```

  - **Expect:** seed rows (e.g. `priya.wire`, `samir.hassan`). If the container name differs, substitute it everywhere below.

- [ ] HCM mock healthy:

```bash
curl -sf http://localhost:8091/health
```

- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/236
```

## Do this

### Task 1 — Dry-run Create + Disable SQL (before touching IIQ)

Prove the statements against Postgres first. Use a throwaway key you will clean up only by leaving it `DISABLED` (no hard delete required).

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps <<'SQL'
INSERT INTO mnb_app_accounts
  (account_id, username, email, employee_id, status, entitlement)
VALUES
  ('jdbc-dry-236', 'lab.dry236', 'lab.dry236@meridiannb.com', 'lab.dry236', 'ACTIVE', 'DWRP')
ON CONFLICT (account_id) DO UPDATE
  SET status = 'ACTIVE', updated_at = CURRENT_TIMESTAMP;

SELECT account_id, username, status, entitlement
FROM mnb_app_accounts WHERE account_id = 'jdbc-dry-236';

UPDATE mnb_app_accounts
SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP
WHERE account_id = 'jdbc-dry-236';

SELECT account_id, username, status
FROM mnb_app_accounts WHERE account_id = 'jdbc-dry-236';

SELECT COUNT(*) AS still_there
FROM mnb_app_accounts WHERE account_id = 'jdbc-dry-236';
SQL
```

- **Why:** if SQL is wrong, fixing IIQ policies will not help.  
- **Expect:** first select `ACTIVE`; second select `DISABLED`; `still_there` = `1`.

Save output as `~/iiq-lab-evidence/sandbox/236/dry-run.sql.txt`.

> **Watch out:** Host port `5435` is optional on your Mac. Prefer `docker exec … psql` so you match the same DB IIQ uses (`jdbc-pg` / `mnb-jdbc-sample`).

### Task 2 — Confirm policies are missing (assume nothing)

1. **Applications → Application Definition → MNB-CoreBanking**  
2. Open **Provisioning Policies** (or Configuration → Provisioning Policies)  
3. Note what is listed for Create / Disable / Delete  

- **Why:** after a wipe or partial seed this tab is often empty even when aggregation works.  
- **Expect:** no usable Create/Disable policy yet — or incomplete stubs you will replace.  
- **Expect:** you will **not** add a Delete policy.

### Task 3 — Create the Create provisioning policy

1. Still on `MNB-CoreBanking` → **Provisioning Policies** → **Add Policy** / **Create**  
2. **Name:** `Create` (or `Account Create`) · operation / type **Create**  
3. Add fields (Value Settings → Script or Static as shown):

| Field | How to set value |
| --- | --- |
| `account_id` | Script: `return "jdbc-lab-" + identity.getName();` |
| `username` | Script: `return identity.getName();` |
| `email` | Script: `return identity.getEmail();` |
| `employee_id` | Script: `return identity.getName();` |
| `status` | Static / literal: `ACTIVE` |
| `entitlement` | Static / literal: `DWRP` |

4. Mark required fields as required if the UI offers the checkbox  
5. **Save** the policy, then **Save** the Application  

- **Why:** the plan must carry every column the INSERT binds.  
- **Expect:** Create policy lists those six attributes; `status` is literally `ACTIVE`.

> **Tip:** If Field scripts fail to save, use **Value** type Script under each field’s Value Settings (not only the Settings tab). Same pattern as OpenLDAP Create fields in Lesson 216.

### Task 4 — Create the Disable provisioning policy

1. **Add Policy** → type / operation **Disable**  
2. **Name:** `Disable`  
3. Add field:

| Field | Value |
| --- | --- |
| `status` | Static: `DISABLED` |

4. Do **not** create a Delete policy  
5. **Save** policy + Application  

- **Why:** Disable must flip lifecycle state; Delete would remove evidence.  
- **Expect:** Disable policy present; Delete mapping **absent**.

### Task 5 — JDBC provisioning rule (seeded — verify or create)

Policies alone do not execute SQL. The JDBC connector needs a **`JDBCOperationProvisioning`** rule.

**Enterprise default:** `./tools/lab/docker/up.sh --enterprise` imports `config/Rule/MNB-Rule-JDBC-CoreBanking-Provision.xml` and sets **JDBCProvision** on `MNB-CoreBanking`. Open **Setup → Rules** — if that rule exists and the Application Rules tab points at it, skip to Task 6 confirmation (re-open app and verify the name stuck). Only create/paste below if the rule is missing after a wipe without enterprise import.

1. **Setup → Rules → Add New Rule** (or Gear → Global Settings → Rules)  
2. Set:

| Field | Value |
| --- | --- |
| **Name** | `MNB-Rule-JDBC-CoreBanking-Provision` |
| **Type** | `JDBCOperationProvisioning` |
| **Language** | BeanShell |
| **Description** | Create INSERT + Disable UPDATE for mnb_app_accounts (no hard DELETE) |

3. Paste this **Source** exactly:

```java
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.List;

import sailpoint.object.ProvisioningPlan;
import sailpoint.object.ProvisioningPlan.AccountRequest;
import sailpoint.object.ProvisioningPlan.AttributeRequest;
import sailpoint.object.ProvisioningResult;

ProvisioningResult result = new ProvisioningResult();

String attr(AccountRequest ar, String name) {
  if (ar == null) return null;
  AttributeRequest a = ar.getAttributeRequest(name);
  if (a == null || a.getValue() == null) return null;
  return a.getValue().toString();
}

try {
  if (plan == null) {
    result.setStatus(ProvisioningResult.STATUS_FAILED);
    result.addError("MNB JDBC provision: plan was null");
    return result;
  }

  List accountRequests = plan.getAccountRequests();
  if (accountRequests == null || accountRequests.isEmpty()) {
    result.setStatus(ProvisioningResult.STATUS_COMMITTED);
    return result;
  }

  for (Object o : accountRequests) {
    AccountRequest ar = (AccountRequest) o;
    AccountRequest.Operation op = ar.getOperation();

    if (AccountRequest.Operation.Create.equals(op)) {
      String accountId = attr(ar, "account_id");
      String username = attr(ar, "username");
      String email = attr(ar, "email");
      String employeeId = attr(ar, "employee_id");
      String status = attr(ar, "status");
      String entitlement = attr(ar, "entitlement");

      if (accountId == null || username == null) {
        result.setStatus(ProvisioningResult.STATUS_FAILED);
        result.addError("MNB JDBC Create missing account_id or username");
        return result;
      }
      if (status == null) status = "ACTIVE";

      String sql =
        "INSERT INTO mnb_app_accounts "
        + "(account_id, username, email, employee_id, status, entitlement) "
        + "VALUES (?,?,?,?,?,?)";
      PreparedStatement ps = connection.prepareStatement(sql);
      ps.setString(1, accountId);
      ps.setString(2, username);
      ps.setString(3, email);
      ps.setString(4, employeeId);
      ps.setString(5, status);
      ps.setString(6, entitlement);
      ps.executeUpdate();
      ps.close();
      result.setStatus(ProvisioningResult.STATUS_COMMITTED);
    }
    else if (AccountRequest.Operation.Disable.equals(op)
          || AccountRequest.Operation.Delete.equals(op)) {
      // Soft-close only — never hard DELETE the banking row
      String accountId = ar.getNativeIdentity();
      if (accountId == null) accountId = attr(ar, "account_id");
      if (accountId == null) {
        result.setStatus(ProvisioningResult.STATUS_FAILED);
        result.addError("MNB JDBC Disable missing nativeIdentity/account_id");
        return result;
      }

      String sql =
        "UPDATE mnb_app_accounts "
        + "SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP "
        + "WHERE account_id = ?";
      PreparedStatement ps = connection.prepareStatement(sql);
      ps.setString(1, accountId);
      int n = ps.executeUpdate();
      ps.close();
      if (n < 1) {
        result.setStatus(ProvisioningResult.STATUS_FAILED);
        result.addError("MNB JDBC Disable matched 0 rows for " + accountId);
        return result;
      }
      result.setStatus(ProvisioningResult.STATUS_COMMITTED);
    }
    else if (AccountRequest.Operation.Enable.equals(op)) {
      String accountId = ar.getNativeIdentity();
      String sql =
        "UPDATE mnb_app_accounts "
        + "SET status = 'ACTIVE', updated_at = CURRENT_TIMESTAMP "
        + "WHERE account_id = ?";
      PreparedStatement ps = connection.prepareStatement(sql);
      ps.setString(1, accountId);
      ps.executeUpdate();
      ps.close();
      result.setStatus(ProvisioningResult.STATUS_COMMITTED);
    }
    else {
      // Modify etc. not required for this lesson
      result.setStatus(ProvisioningResult.STATUS_COMMITTED);
    }
  }
}
catch (SQLException e) {
  result.setStatus(ProvisioningResult.STATUS_FAILED);
  result.addError("MNB JDBC SQLException: " + e.getMessage());
}

return result;
```

4. **Save**

- **Why:** Create inserts; Disable/Delete both become `status='DISABLED'` so a leaver plan that emits Delete still cannot wipe the row.  
- **Expect:** rule saved as type `JDBCOperationProvisioning`.

### Task 6 — Attach the rule on MNB-CoreBanking

1. **Applications → Application Definition → MNB-CoreBanking**  
2. Open **Rules** (or Configuration → Rules / Provisioning Rules)  
3. Set **JDBCProvision** / **Provisioning Rule** / **JDBC Operation Provisioning Rule** (label varies) to:

   `MNB-Rule-JDBC-CoreBanking-Provision`

4. **Save** the Application  
5. Re-open and confirm the rule name stuck  

- **Why:** unattached rules never run.  
- **Expect:** Application shows `MNB-Rule-JDBC-CoreBanking-Provision` in the JDBC provision slot.

> **Watch out:** Do not put this rule in the **Before Provisioning** slot — that is a different rule type (Lesson 241).

### Task 7 — Create disposable identity `lab.jdbctest`

Never use Helen, Priya, Marcus, or Sanjay as the write subject.

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.jdbctest JDBC Test \
  lab.jdbctest@meridiannb.com 'Bank Operations'
```

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.jdbctest \
  | python3 -m json.tool | grep -E 'userName|email|active|department'
```

1. In IIQ: Aggregate **`MNB-Workday`** → Complete  
2. **Setup → Tasks → Refresh Identity Cube** — include `lab.jdbctest`, promote/create identities as needed → **Run Now**  
3. **Identities → Identity Warehouse** → open `lab.jdbctest`  
4. Confirm **Email** is populated (edit cube if empty: `lab.jdbctest@meridiannb.com`)  

- **Why:** Create Field scripts read `identity.getEmail()` / `getName()`.  
- **Expect:** cube exists; no Core Banking link yet.

### Task 8 — Create Account via IIQ (exercise Create policy)

1. On `lab.jdbctest` → **Application Accounts** / **Manage** → **Create Account** (wording varies)  
2. Application: **`MNB-CoreBanking`**  
3. Confirm preview / form shows your Create fields (`account_id` ≈ `jdbc-lab-lab.jdbctest`, `status` = `ACTIVE`, `entitlement` = `DWRP`)  
4. Submit / provision  
5. **Setup → Provisioning Transactions** → open the detail for this create  

- **Why:** this is the live Create path — not a hand `INSERT` pretending to be IIQ.  
- **Expect:** Provisioning Transaction **Committed** (not Failed).

If Failed: open detail → fix Field scripts / rule attach (Tasks 3–6) → retry the same transaction (Lesson 230 pattern).

### Task 9 — Prove Create on Postgres (`ACTIVE`)

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select account_id, username, email, employee_id, status, entitlement
      from mnb_app_accounts where username='lab.jdbctest';"
```

- **Expect:** one row; `status` = **`ACTIVE`**; `account_id` = `jdbc-lab-lab.jdbctest` (or your Field script’s value).  

Save as `~/iiq-lab-evidence/sandbox/236/after-create.sql.txt`.

Aggregate **`MNB-CoreBanking`** and confirm the link on the cube matches SQL.

### Task 10 — Disable the account (exercise Disable policy)

1. On `lab.jdbctest` → Application Accounts → **`MNB-CoreBanking`**  
2. Choose **Disable** (Manage Accounts → Disable, or account action menu)  
3. Confirm / provision  
4. Open **Provisioning Transactions** → expect **Committed** for Disable  

- **Why:** leaver-style soft-close without destroying the row.  
- **Expect:** IIQ shows the account disabled / inactive for Core Banking.

> **Watch out:** If your UI only offers Delete, still proceed — the rule maps Delete → `UPDATE … DISABLED`. Do **not** run a raw `DELETE` in `psql` to “help.”

### Task 11 — Prove Disable without DELETE

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps <<'SQL'
SELECT account_id, username, status, entitlement, updated_at
FROM mnb_app_accounts
WHERE username = 'lab.jdbctest';

SELECT COUNT(*) AS row_count
FROM mnb_app_accounts
WHERE username = 'lab.jdbctest';
SQL
```

- **Expect:** `status` = **`DISABLED`**; `row_count` = **`1`** (row intact; entitlement may still be `DWRP`).  

Save as `~/iiq-lab-evidence/sandbox/236/after-disable.sql.txt`.

Write a one-line control note in evidence:

```text
Disable = status flip. Hard DELETE forbidden for Core Banking accounts (audit + rehire).
```

### Task 12 — Optional export for SSD

1. Debug → Application `MNB-CoreBanking` → export / copy Provisioning Policies section if present  
2. Debug → Rule `MNB-Rule-JDBC-CoreBanking-Provision` → export XML  
3. Strip `id` / `created` / `modified` before saving under `config/` (see `config/README.md`)  

- **Expect:** re-importable Rule XML; policies either in Application XML or documented for Lesson 248.

## If it fails

| Symptom | Fix |
| --- | --- |
| Create policy saves; no DB row | Rule not attached (Task 6) or PT Failed — open Provisioning Transaction detail |
| `SQLException` / syntax error | Re-run Task 1 dry-run; fix rule SQL; retry PT |
| Duplicate key on Create | Row already exists — Disable/cleanup that `account_id`, or change Field script |
| Disable Committed but still `ACTIVE` | Wrong native identity — confirm `account_id` on the Link matches SQL `WHERE` |
| Row vanished after Disable | Someone ran hard `DELETE` or a different rule — restore from Task 1 pattern; fix rule to UPDATE only |
| `psql` / container not found | `docker ps \| grep jdbc` and substitute container name |
| Cube missing email | Edit identity email before Create Account |
| Used Helen/Priya/Marcus | Stop — restart from Task 7 with `lab.jdbctest` |

## You are done when

- [ ] Create + Disable provisioning policies exist on `MNB-CoreBanking` (you created them)  
- [ ] `MNB-Rule-JDBC-CoreBanking-Provision` attached as the JDBC provision rule  
- [ ] `psql` proved **`ACTIVE`** after Create for `lab.jdbctest`  
- [ ] `psql` proved **`DISABLED`** after Disable with **`row_count = 1`**  
- [ ] Evidence folder has dry-run + after-create + after-disable SQL  

## Control note

- **Control:** Core Banking account lifecycle without evidence loss (soft disable)  
- **Owner:** IAM Engineering / Core Banking App Owner  
- **SLA (lab):** Create and Disable same session; no hard deletes  
- **Evidence:** `~/iiq-lab-evidence/sandbox/236/`  

## Quick check

1. Why Disable instead of DELETE on leaver? → Keeps audit/rehire row; status carries lifecycle  
2. What executes the SQL — the policy form or the JDBC rule? → `JDBCOperationProvisioning` rule; policies supply plan attributes  
3. Which `docker` form should you prefer for proof? → `docker exec -it mnb-jdbc-sample psql …`  
4. What must `row_count` be after Disable? → `1`  
5. Which disposable identity did this lesson use? → `lab.jdbctest`  

## Feedback

Could you rebuild Create + Disable from an empty Policies tab and prove ACTIVE→DISABLED with `psql` without this page?

If something failed, note the **task number**, Provisioning Transaction status, and the exact `psql` `status` / `row_count` you saw.

## Navigate

- Previous: [Lesson 235](235-ldap-provision-stretch.md)
- Next: [Lesson 237](237-ws-connector-deep.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
