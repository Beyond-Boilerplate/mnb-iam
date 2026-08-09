# Lesson 241 — Before/After Provisioning Rules

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~80 minutes  
**Prereq:** Lessons 230, 236  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 89 / 91

> **Why:** Provisioning Policy tabs map attributes; they cannot say “reject this plan if the identity is ineligible” or “email compliance after every successful Core Banking create.” Before/After rules are the connector-layer dual-control — without them, role mistakes become silent target changes.

## What this is

**BeforeProvisioning** and **AfterProvisioning** are BeanShell (or Java) rules attached to an Application. They wrap the connector call:

```text
Access / Create Account / role assign
  → ProvisioningPlan compiled
  → BeforeProvisioning  (may throw → connector never runs)
  → connector (JDBC SQL, LDAP, WS, …)
  → AfterProvisioning   (side effects: email, ticket — must be idempotent)
```

Classic 89 catalogs rule types; 91 is Before/After depth. This lesson authors **live** rules on **`MNB-CoreBanking`** (PROVISIONING already proven in Lesson 236), not comment-only stubs.

Nothing for this drill is pre-built. You will:

1. Create two disposable identities (`lab.rulesfail1`, `lab.rulespass1`)  
2. Paste a real BeforeProvisioning department guard  
3. Attach it to `MNB-CoreBanking`  
4. **Fail** a Create for Technology Platforms — prove SQL unchanged  
5. Paste an AfterProvisioning Mailpit notify rule  
6. **Pass** a Create for Treasury & Payments — prove row + mail  
7. Export both rules under evidence / `config/Rule/`  

## Know these

```text
Create lab.rulesfail1 (Technology Platforms) + lab.rulespass1 (Treasury & Payments)
  → Setup → Rules → MNB-Rule-CoreBanking-Dept-Guard (BeforeProvisioning)
  → Attach on MNB-CoreBanking Before Provisioning Rule
  → Create Account for lab.rulesfail1 → BLOCKED (your message)
  → psql: still no row for lab.rulesfail1
  → Setup → Rules → MNB-Rule-CoreBanking-Notify (AfterProvisioning) + EmailTemplate
  → Attach After Provisioning Rule
  → Create Account for lab.rulespass1 → Committed
  → psql ACTIVE + Mailpit subject
```

| Rule type | When it runs | This lesson |
| --- | --- | --- |
| **BeforeProvisioning** | Immediately before connector execute | Dept guard — reject ineligible Creates |
| **AfterProvisioning** | After connector work (success path) | Mailpit notify on Core Banking Create |
| IdentityAttribute / others | Agg / refresh pipelines | Out of scope — don’t boil the ocean |

| Term | Plain English |
| --- | --- |
| **`plan`** | `ProvisioningPlan` handed to the rule |
| **`GeneralException`** | Throw from Before to abort the connector call |
| **Idempotent After** | Safe if the same success is processed twice |
| **Wrong slot** | Putting JDBC SQL rule in Before — or Before in JDBCProvision |

- **Wrong way:** Trusting only nightly SoD (Lesson 224) while connectors happily provision ineligible accounts.  
- **Wrong way:** Inventing AccountRequests for *other* apps inside Before — mutate the plan you were given, don’t expand scope.  
- **Wrong way:** Leaving a throwing Before rule attached after the fail proof — always restore a safe guard (eligible depts only).  
- **Wrong way:** Using Helen / Priya / Marcus for fail/pass destructive creates.  
- **Wrong way:** Assuming Before/After rules already exist on Core Banking — verify; create if missing.

## Intent

- Author a BeforeProvisioning rule with paste-ready BeanShell that blocks ineligible Core Banking Creates.  
- Prove fail: PT/error carries your message; Postgres has no new row.  
- Author an AfterProvisioning rule that emails Mailpit on successful Create.  
- Prove pass: `ACTIVE` row + Mailpit message for the eligible disposable user.  
- Export both rules cleanly.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up as `spadmin` / `admin`
- [ ] Lesson 236 complete: Create policy + `MNB-Rule-JDBC-CoreBanking-Provision` attached and proven
- [ ] Mailpit open: [http://localhost:8025](http://localhost:8025) (Lesson 203 SMTP)
- [ ] Core Banking DB reachable:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select count(*) from mnb_app_accounts;"
```

- [ ] HCM healthy: `curl -sf http://localhost:8091/health`
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/241
```

## Do this

### Task 1 — Create disposable fail + pass identities

Never use Helen, Priya, Marcus, or Sanjay as the rule subjects.

**Fail subject** (ineligible department):

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.rulesfail1 Rules Fail \
  lab.rulesfail1@meridiannb.com 'Technology Platforms'
```

**Pass subject** (eligible department):

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.rulespass1 Rules Pass \
  lab.rulespass1@meridiannb.com 'Treasury & Payments'
```

1. Aggregate **`MNB-Workday`**  
2. **Refresh Identity Cube** for both names (promote/create as needed)  
3. Open each cube → confirm **department** (or equivalent attribute) matches the HCM values above  
4. Confirm **email** populated on both  

If department did not promote, edit the cube attribute `department` (or your mapped name) to the exact strings:

- `lab.rulesfail1` → `Technology Platforms`  
- `lab.rulespass1` → `Treasury & Payments`  

- **Why:** the Before rule reads identity department — wrong attribute = false pass/fail.  
- **Expect:** two cubes; **no** Core Banking links yet.

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select username from mnb_app_accounts
      where username in ('lab.rulesfail1','lab.rulespass1');"
```

- **Expect:** zero rows (baseline before fail/pass).

### Task 2 — Create BeforeProvisioning rule (exact source)

1. **Setup → Rules → Add New Rule**  
2. Set:

| Field | Value |
| --- | --- |
| **Name** | `MNB-Rule-CoreBanking-Dept-Guard` |
| **Type** | `BeforeProvisioning` |
| **Language** | BeanShell |
| **Description** | Reject Core Banking Create when department is not Treasury/Commercial/Bank Ops |

3. Paste this **Source** exactly:

```java
import sailpoint.object.Identity;
import sailpoint.object.ProvisioningPlan;
import sailpoint.object.ProvisioningPlan.AccountRequest;
import sailpoint.tools.GeneralException;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

if (plan == null) {
  return;
}

Identity identity = plan.getIdentity();
if (identity == null && identityName != null) {
  identity = context.getObjectByName(Identity.class, identityName);
}
if (identity == null) {
  return;
}

String dept = null;
Object d = identity.getAttribute("department");
if (d == null) d = identity.getAttribute("departmentName");
if (d != null) dept = d.toString();

Set eligible = new HashSet(Arrays.asList(
  "Treasury & Payments",
  "Commercial Banking",
  "Bank Operations"
));

List accountRequests = plan.getAccountRequests();
if (accountRequests == null) {
  return;
}

for (Object o : accountRequests) {
  AccountRequest ar = (AccountRequest) o;
  if (ar == null || ar.getApplication() == null) continue;
  if (!"MNB-CoreBanking".equals(ar.getApplication())) continue;

  AccountRequest.Operation op = ar.getOperation();
  boolean guarded =
      AccountRequest.Operation.Create.equals(op)
      || AccountRequest.Operation.Enable.equals(op)
      || AccountRequest.Operation.Modify.equals(op);

  if (!guarded) continue;

  if (dept == null || !eligible.contains(dept)) {
    String who = identity.getName();
    String msg = "Wire/Core Banking role denied: " + who
        + " is not in an eligible department (saw '" + dept + "')";
    if (log != null) {
      log.warn("MNB-Rule-CoreBanking-Dept-Guard BLOCK: " + msg);
    }
    throw new GeneralException(msg);
  }
}
```

4. **Save**

- **Why:** connector-layer guard — even a mistaken direct Create Account is blocked.  
- **Expect:** rule type **BeforeProvisioning**; compiles on save/run.

### Task 3 — Attach Before rule on MNB-CoreBanking

1. **Applications → Application Definition → MNB-CoreBanking**  
2. **Rules** tab  
3. Set **Before Provisioning Rule** = `MNB-Rule-CoreBanking-Dept-Guard`  
4. Leave **JDBCProvision** / JDBC Operation rule as Lesson 236’s `MNB-Rule-JDBC-CoreBanking-Provision`  
5. **Save** → re-open → confirm both slots  

- **Why:** Before and JDBCProvision are different hooks; you need both.  
- **Expect:** Before slot shows the dept guard; JDBC slot still shows the SQL rule.

> **Watch out:** Empty Before slot = rule never fires. Attaching only under Debug Application XML without Save is a common miss.

### Task 4 — Fail proof: Create Account for `lab.rulesfail1`

1. Open `lab.rulesfail1` → **Create Account** → **`MNB-CoreBanking`**  
2. Submit / provision  

- **Expect:** request / Provisioning Transaction **fails** (or workflow error)  
- **Expect:** error text includes:

```text
Wire/Core Banking role denied: lab.rulesfail1 is not in an eligible department
```

3. Capture error from **Provisioning Transactions** detail and/or:

```bash
docker logs mnb-identityiq 2>&1 | grep -i "MNB-Rule-CoreBanking-Dept-Guard" | tail -20
```

4. Re-check Postgres:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select account_id, username, status from mnb_app_accounts
      where username='lab.rulesfail1';"
```

- **Why:** Before threw → JDBC rule must not have inserted.  
- **Expect:** **zero** rows.

Save error text + empty SQL as `~/iiq-lab-evidence/sandbox/241/fail-blocked.*`.

### Task 5 — Create EmailTemplate for After notify

1. **Setup → Email Templates → Add New Email Template**  
2. Set:

| Field | Value |
| --- | --- |
| **Name** | `MNB-EmailTemplate-CoreBanking-Prov` |
| **Subject** | `Core Banking provisioning succeeded: $identityName` |
| **Body** | `Compliance notify: Core Banking change for $identityName completed in the Meridian lab.` |

3. **Save**

- **Why:** After rule looks up the template by exact name.  
- **Expect:** template listed as `MNB-EmailTemplate-CoreBanking-Prov`.

**Alternate:** Debug → Import from a small XML you author; name must match.

### Task 6 — Create AfterProvisioning rule (exact source)

1. **Setup → Rules → Add New Rule**  
2. Set:

| Field | Value |
| --- | --- |
| **Name** | `MNB-Rule-CoreBanking-Notify` |
| **Type** | `AfterProvisioning` |
| **Language** | BeanShell |
| **Description** | Mailpit compliance notify after successful Core Banking Create |

3. Paste this **Source** exactly:

```java
import sailpoint.object.EmailOptions;
import sailpoint.object.EmailTemplate;
import sailpoint.object.Identity;
import sailpoint.object.ProvisioningPlan;
import sailpoint.object.ProvisioningPlan.AccountRequest;
import sailpoint.object.ProvisioningResult;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

if (plan == null) {
  return;
}

Identity identity = plan.getIdentity();
if (identity == null && identityName != null) {
  identity = context.getObjectByName(Identity.class, identityName);
}
String who = (identity != null) ? identity.getName() : String.valueOf(identityName);

boolean created = false;
List accountRequests = plan.getAccountRequests();
if (accountRequests != null) {
  for (Object o : accountRequests) {
    AccountRequest ar = (AccountRequest) o;
    if (ar == null || ar.getApplication() == null) continue;
    if (!"MNB-CoreBanking".equals(ar.getApplication())) continue;
    if (AccountRequest.Operation.Create.equals(ar.getOperation())) {
      ProvisioningResult pr = ar.getResult();
      if (pr == null || ProvisioningResult.STATUS_COMMITTED.equals(pr.getStatus())
          || ProvisioningResult.STATUS_COMMITTED.equals(String.valueOf(pr.getStatus()))) {
        created = true;
      }
      // Some builds leave result on the plan only — still notify on Create after connector
      if (pr == null) created = true;
    }
  }
}

if (!created) {
  return;
}

String tplName = "MNB-EmailTemplate-CoreBanking-Prov";
EmailTemplate template = context.getObjectByName(EmailTemplate.class, tplName);
if (template == null) {
  if (log != null) log.error("MNB-Rule-CoreBanking-Notify missing template " + tplName);
  return;
}
template = (EmailTemplate) template.deepCopy(context);

Map args = new HashMap();
args.put("identityName", who);

String to = "compliance-lab@meridiannb.com";
EmailOptions ops = new EmailOptions(to, args);
context.sendEmailNotification(template, ops);

if (log != null) {
  log.warn("MNB-Rule-CoreBanking-Notify mailed " + to + " for " + who);
}
```

4. **Save**

- **Why:** After runs only after the connector path; fail proof must not mail.  
- **Expect:** rule type **AfterProvisioning**.

### Task 7 — Attach After rule

1. `MNB-CoreBanking` → **Rules**  
2. **After Provisioning Rule** = `MNB-Rule-CoreBanking-Notify`  
3. **Save** → confirm Before + After + JDBCProvision all three set  

- **Expect:** Application rules section shows all three names.

### Task 8 — Pass proof: Create Account for `lab.rulespass1`

1. Open `lab.rulespass1` → **Create Account** → **`MNB-CoreBanking`**  
2. Submit / provision  

- **Expect:** Provisioning Transaction **Committed**  

3. Postgres:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select account_id, username, status, entitlement
      from mnb_app_accounts where username='lab.rulespass1';"
```

- **Expect:** one row, `status` = **`ACTIVE`**.

4. Mailpit [http://localhost:8025](http://localhost:8025)  

- **Expect:** message to `compliance-lab@meridiannb.com` (or caught-all) with subject containing **`lab.rulespass1`**.

5. Confirm fail identity still has **no** row:

```bash
docker exec -it mnb-jdbc-sample psql -U mnb -d mnb_apps \
  -c "select username from mnb_app_accounts
      where username in ('lab.rulesfail1','lab.rulespass1');"
```

- **Expect:** only `lab.rulespass1`.

Save SQL + Mailpit screenshot under `~/iiq-lab-evidence/sandbox/241/`.

### Task 9 — Export rules (SSD hygiene)

1. Debug → Rule → `MNB-Rule-CoreBanking-Dept-Guard` → copy XML  
2. Debug → Rule → `MNB-Rule-CoreBanking-Notify` → copy XML  
3. Strip `id`, `created`, `modified`  
4. Save under evidence (and optionally `config/Rule/` per `config/README.md`):

- `MNB-Rule-CoreBanking-Dept-Guard.xml`  
- `MNB-Rule-CoreBanking-Notify.xml`  

- **Why:** examiner-visible, re-importable lab assets (Lesson 248).  
- **Expect:** files re-import via Debug → Import without id collisions.

> **Tip:** Leave the dept guard **attached** — it is the control. Do not delete it after the fail test.

## If it fails

| Symptom | Fix |
| --- | --- |
| Before never fires | Wrong slot or wrong Application; Confirm Task 3 Save |
| Fail identity still gets a row | Before not attached / department attribute blank / name mismatch on app (`MNB-CoreBanking`) |
| Generic UI error only | Read PT detail + `docker logs mnb-identityiq` for your message |
| Pass blocked incorrectly | Department string must match eligible set exactly (`Treasury & Payments`) |
| After fires, no mail | Lesson 203 SMTP `mailpit:1025`; template name misspelled; check Mailpit catch-all |
| After mails on fail | Fail path should throw in Before — if mail arrived, connector ran; re-check Task 4 SQL |
| BeanShell compile error | Paste source again; check imports; Save, then retry Create |
| JDBC slot empty after attach | Re-select Lesson 236 rule; Save Application |

## You are done when

- [ ] Before rule blocks `lab.rulesfail1` Create with your message  
- [ ] Postgres shows **no** row for `lab.rulesfail1`  
- [ ] After rule + template attached; `lab.rulespass1` Create **Committed**  
- [ ] Postgres shows `ACTIVE` for `lab.rulespass1` + Mailpit notify  
- [ ] Both rules exported (ids stripped) under evidence / `config/Rule/`  

## Control note

- **Control:** Connector-layer department enforcement + privileged-create notification  
- **Owner:** IAM Engineering  
- **SLA (lab):** Block same request; notify within seconds via Mailpit  
- **Evidence:** `~/iiq-lab-evidence/sandbox/241/` + exported Rule XML  

## Quick check

1. Which rule can stop the connector call? → BeforeProvisioning  
2. What do you throw to abort? → `GeneralException` with a clear message  
3. Why attach Before **and** keep the JDBCProvision rule? → Guard vs SQL execute are different slots  
4. What proves the fail path for real? → Error text **and** zero Postgres rows  
5. Why export to `config/Rule/`? → SSD promote / repeatable lab (248)  

## Feedback

Could you paste a Before/After pair, attach them, and run fail-then-pass with SQL + Mailpit proof without this page?

If something failed, note the **task number**, whether the PT was Failed vs Committed, department value on the cube, and whether `psql` showed a row.

## Navigate

- Previous: [Lesson 240](240-logical-application-live.md)
- Next: [Lesson 242](242-workflow-lcm-customize.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
