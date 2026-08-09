# Lesson 235 — OpenLDAP Provision Stretch

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lessons 204, 216–217, 230  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 58

> **Why:** Reads without writes teach half a connector. If group membership remove and ACL denials were never exercised, production is the first time anyone finds out.

## What this is

Lesson 204 operated OpenLDAP read-heavy. Lessons 216–217 already **create** OpenLDAP accounts via birthright (Create Field scripts → no Form). This lesson is the **stretch beyond create**:

| Already proved (216–217) | Stretch here |
| --- | --- |
| Account create for joiners | Group **member add** and **member remove** |
| Birthright `all-employees` path | Deliberate ACL denial → fix directory ACL → retry |
| Cube matches after joiner | Re-agg drift check after membership churn |

`MNB-OpenLDAP` lists `PROVISIONING` in `featuresString` — IIQ *can* write. You prove membership writes and ACL hygiene with `ldapsearch`, not UI success alone.

Classic 58 taught LDAP ops; here add/remove + ACL fix are the bar.

## Know these

```text
Disposable identity (or existing LDAP-linked user)
  → request/assign OpenLDAP group entitlement
  → provision ADD → ldapsearch group member
  → remove assignment → provision REMOVE → ldapsearch
  → break bind to read-only / wrong ACL → PT shows denial
  → restore admin bind / fix olcAccess → retry → Committed
  → Aggregate → cube matches directory
```

| Operation | Proof command |
| --- | --- |
| Account create (refresh) | `ldapsearch … '(uid=<user>)'` |
| Group member add/remove | `ldapsearch … '(cn=<group>)' member` |
| ACL denial | PT / bind / insufficient access error text |

| Term | Plain English |
| --- | --- |
| **groupOfNames** | LDAP group object that stores `member` DNs |
| **ACL** | Who can write which attributes on the directory |
| **Drift** | IIQ cube ≠ directory after a write |
| **Create Field scripts** | Already required for joiner create (216 Task 1d) — not re-taught here |

- **Wrong way:** “Fixing” ACL denial by disabling provisioning in IIQ — hides the gap.
- **Wrong way:** Re-doing only account create and calling the stretch done — 217 already owns create.
- **Wrong way:** Anonymous `ldapsearch` when proving writes — bind as admin for ground truth.

## Intent

- Provision OpenLDAP **group member add** and **remove**; confirm both with `ldapsearch`.
- Trigger an ACL / bind denial; fix the directory side; retry to Committed.
- Re-aggregate; confirm no drift.
- Leave create-path as known (216–217); document if Create scripts are still missing.

## Before you start

- [ ] `MNB-OpenLDAP` aggregating; Lesson 230 triage card idea familiar
- [ ] Admin bind: `cn=admin,dc=meridiannb,dc=com` / `admin`
- [ ] A user with an OpenLDAP link (Helen, Priya, or disposable joiner from 217)
- [ ] Entitlement Catalog has an OpenLDAP group (e.g. `all-employees`) — run Group Aggregation if empty (Lesson 216)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/235
```

## Do this

### Task 1 — Confirm create path already works (baseline, don’t rebuild)

Pick a user who **already** has an OpenLDAP account from birthright/joiner:

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b ou=people,dc=meridiannb,dc=com \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin \
  '(uid=helen.ross)'
```

- **Why:** this lesson stretches membership/ACL — if create is broken, finish 216 Task 1d / 217 first.
- **Expect:** entry exists. If not, stop and repair create before membership drills.

### Task 2 — Ensure a group entitlement exists

1. Confirm Group Aggregation has run for `MNB-OpenLDAP`  
2. Find `all-employees` (or create a lab `groupOfNames` under `ou=groups,dc=meridiannb,dc=com` if you need a disposable group)  

Minimal create if needed (seed admin as first member — `groupOfNames` requires ≥1 member):

```bash
# Only if you need a disposable group — adjust DNs to your tree
ldapadd -x -H ldap://localhost:389 \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin <<'EOF'
dn: cn=mnb-lab-stretch,ou=groups,dc=meridiannb,dc=com
objectClass: groupOfNames
cn: mnb-lab-stretch
member: cn=admin,dc=meridiannb,dc=com
EOF
```

Then aggregate groups and mark the entitlement requestable / wrap in a small IT Bundle.

- **Expect:** group visible for assignment.

### Task 3 — Provision member ADD

Assign the OpenLDAP group entitlement to a user who is **not** already a member (or use Priya on a disposable group).

Approve/provision (Lesson 222 path if requestable).

- **Expect:** PT **Committed**.

### Task 4 — Prove ADD with ldapsearch

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b ou=groups,dc=meridiannb,dc=com \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin \
  '(cn=all-employees)' member
```

(Use `cn=mnb-lab-stretch` if you created the disposable group.)

- **Expect:** user’s DN listed under `member`.

Save output as `member-add.txt`.

### Task 5 — Provision member REMOVE

1. Remove the assignment in IIQ  
2. Refresh with **provisioning**  
3. Re-run the same `ldapsearch`  

- **Expect:** member entry **gone**.

Save as `member-remove.txt`.

> **Tip:** Same failure class as Lessons 218/223/234 — role gone in IIQ but member still present means provisioning/re-agg skipped.

### Task 6 — Trigger an ACL / bind denial

1. **Applications → MNB-OpenLDAP**  
2. Change bind password to a **wrong** value (or a known read-only bind if you have one)  
3. **Save**  
4. Attempt another membership write  

- **Expect:** Failed PT with bind / insufficient-access language — copy exact text to `acl-denial.txt`.

> **Watch out:** You are breaking the connector on purpose — restore before you leave (Lesson 230 hygiene).

### Task 7 — Fix at the directory / bind, not by disabling provisioning

1. Restore `cn=admin` bind password (or repair `olcAccess` / ACL inside the OpenLDAP container if you used a read-only DN)  
2. **Test Connection** green  
3. Retry the write  

- **Why:** disabling `PROVISIONING` in IIQ only hides the control gap.
- **Expect:** Committed after fix.

If Test Connection is green but retry fails, recycle connector cache (Lesson 230) then retry.

### Task 8 — Re-aggregate and check drift

1. Aggregate `MNB-OpenLDAP`  
2. Open the identity → Application Accounts / Entitlements  
3. Confirm IIQ matches `ldapsearch`  

- **Expect:** no drift between cube and directory.

### Task 9 — Evidence pack

Save under `~/iiq-lab-evidence/sandbox/235/`:

- `member-add.txt` / `member-remove.txt`  
- `acl-denial.txt` + note of restore  
- Drift check screenshot  

## If it fails

| Symptom | Fix |
| --- | --- |
| Create missing for joiner | Lesson 216 Create Field scripts / 217 — not this stretch’s primary path |
| Group entry malformed | `groupOfNames` needs ≥1 `member` at create — seed admin DN |
| ADD succeeds in UI, ldapsearch empty | Bind as admin; confirm base DN `ou=groups,…` |
| ACL fix ignored | Restart slapd / `ldapmodify` cn=config; read `docker logs` for OpenLDAP |
| Lab left broken | Restore admin bind; Test Connection green before Lesson 236 |

## You are done when

- [ ] Group member **add** and **remove** proved with `ldapsearch`  
- [ ] ACL/bind denial captured and fixed without disabling provisioning  
- [ ] Cube matches directory after re-agg  
- [ ] Connectors green again  

## Control note

- **Control:** Directory write-path proof (membership + ACL hygiene)  
- **Owner:** IAM Engineering / Directory Ops  
- **SLA (lab):** ACL denials fixed at the source, never bypassed in IIQ  
- **Evidence:** `~/iiq-lab-evidence/sandbox/235/` — add/remove ldapsearch; ACL error + fix  

## Quick check

1. What does this stretch add beyond Lesson 217? → Group member add/remove + ACL denial/fix  
2. What proves a write? → `ldapsearch` against the live server  
3. Wrong fix for ACL denial? → Disabling provisioning in IIQ  
4. Why does `groupOfNames` need a member at create? → Schema requires ≥1 `member`  

## Feedback

Could you separate “joiner create failed” from “membership remove failed” without this page? If remove left the member in LDAP, note whether the PT was Committed — Committed + still present is drift/wrong group DN, not “IIQ ignored you.”

## Navigate

- Previous: [Lesson 234](234-ad-groups-ous-live.md)
- Next: [Lesson 236](236-jdbc-provision-policies.md)
- Theory: [Lesson 258 — LDIF Offline Evidence](258-ldif-offline-evidence-theory.md) (offline directory dump vs this live bind path)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
