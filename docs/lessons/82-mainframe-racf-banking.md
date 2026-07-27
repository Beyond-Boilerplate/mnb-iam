# Lesson 82 — Mainframe RACF for Banking

**Level:** Intermediate  
**Track:** Connectors — ERP / HR / Banking  
**Time:** 60–90 min  
**Prereq:** Lesson 81 — Oracle E-Business Suite Connector  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (row: Mainframe RACF)
- Repo: `lab-data/apps/MNB-CoreBanking.csv` (business context for core accounts)
- Runtime: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Explain why **RACF** is Meridian’s privileged control plane for mainframe / core banking security
- Select **RACF - Full** vs RACF LDAP per the connector matrix
- Build Application shell `MNB-RACF-Core` with user, group, and dataset/profile entitlement model (offline)
- Document joiner/mover/leaver expectations for mainframe IDs used by core banking operations
- Produce an audit evidence pack answering “who can alter production CICS/DB2 security?”

---

## Why this matters

**Business.** Core banking batches, CICS transactions, and settlement jobs still run on mainframe platforms at many banks. Wrong RACF permit = fraud or outage.

**Control / audit.** Regulators treat mainframe security as critical infrastructure. Saying “we have CoreBanking CSV in IIQ” is insufficient if RACF groups that gate production regions are unmanaged. This lesson connects IdentityIQ governance to RACF without requiring a live LPAR.

---

## Concepts

From `connector-selection-matrix.csv`:

| system | preferredConnector | alternate | notes |
| --- | --- | --- | --- |
| Mainframe RACF | RACF - Full | RACF LDAP | Banking core security |

```
HR / contractor cube
        │
        ▼
 MNB-RACF-Core (USERID)
        │
        ├── GROUPS (entitlements)
        ├── DATASET / FACILITY profiles (optional model)
        └── Connect to core apps (CICS, DB2, batch) outside IIQ
```

| Term | Meaning in Meridian lab |
| --- | --- |
| USERID | RACF user; often tied to `employeeId` or dedicated ops ID |
| GROUP | Connect group used as IIQ entitlement |
| SPECIAL / OPERATIONS | Privileged RACF attributes — treat like break-glass |
| Revoke | Remove group connect + revoke when leaver |

**Lab-without-live-target:** Application shell, attribute maps, group catalog stub, provisioning policy forms, and network/security worksheet. No live RACF commands required.

Distinguish `MNB-CoreBanking` (business app extract) from `MNB-RACF-Core` (security plane).

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq`
- [ ] Matrix CSV available under `~/iiq-lab-data/connectors/`
- [ ] Skim `lab-data/apps/MNB-CoreBanking.csv` for business account context
- [ ] Privileged access lesson notes (Lesson 28) available for SPECIAL handling
- [ ] Binder: `connectors/racf/`

---

## Lab procedure

### Task 1 — Matrix and architecture worksheet

1. Open the connector selection matrix; copy the Mainframe RACF row into binder.
2. Decide Meridian standard: **RACF - Full** preferred; **RACF LDAP** only if directory projection is the approved integration.
3. Draw ASCII: LPAR → RACF → CICS/DB2/batch; mark where IIQ sits (governance, not substitute for RACF admin).
4. List control owners: Mainframe Security + Platform Ops; IAM is governance owner.

**Expected result:** One-page architecture worksheet with preferred connector named.

**If it fails:** Default to RACF - Full per matrix; document LDAP as alternate only.

---

### Task 2 — Create `MNB-RACF-Core` shell

1. Applications → Add New → select **RACF** / **RACF - Full** template if available.
2. If template missing: create Application `MNB-RACF-Core`, set connector type in Description to “RACF - Full (lab shell).”
3. Owner: Technology Director persona or `spadmin` with transfer note; Secondary: Mainframe Security group.
4. Not authoritative.
5. Save.

**Expected result:** `MNB-RACF-Core` visible in Applications list.

**If it fails:** Exact name required for Capstone blueprint references.

---

### Task 3 — Offline schema and group catalog

1. Account attributes to document: `USERID`, `NAME`, `OWNER`, `DFLTGRP`, `SPECIAL`, `OPERATIONS`, `REVOKE`, `PASSWORD` (flag only—do not store secrets).
2. Entitlement type: **Group** (connect groups). Seed Meridian catalog stubs:
   - `MNB_CICS_PROD_RO`
   - `MNB_CICS_PROD_UPDATE`
   - `MNB_DB2_SETTLE`
   - `MNB_BATCH_OPS`
3. Mark `MNB_CICS_PROD_UPDATE` and any SPECIAL-capable access as **privileged / request-only**.
4. Correlation: `USERID` ↔ `userName` or dedicated `mainframeId` identity attribute (document choice).

**Expected result:** Schema + group catalog table with privilege flags.

**If it fails:** Keep catalog in CSV under `~/iiq-lab-data/connectors/racf-groups-stub.csv`.

---

### Task 4 — Provisioning policies and leaver

1. Create policy stubs: Create user, Add/Remove group, Revoke/Resume.
2. Leaver rule of engagement (document, do not code yet):
   - Set REVOKE on USERID same day
   - Remove connect groups for production
   - Ticket to Mainframe Security for SPECIAL users within 1 hour SLA
3. Map personas: `jordan.reed` (ops) may need batch groups; `kai.nguyen` (engineer) should not receive PROD UPDATE by birthright.
4. Save redacted policy screenshots.

**Expected result:** Create / group modify / revoke policy stubs + leaver SLA note.

**If it fails:** Empty policy objects named `MNB-RACF-Create`, `MNB-RACF-Modify` via Debug.

---

### Task 5 — Lab-without-live-target aggregation path

1. Build proxy CSV `~/iiq-lab-data/apps/MNB-RACF-Core-proxy.csv` with columns `userid,employeeId,groups,revoke`.
2. Include `helen.ross` (read-only group), `jordan.reed` (batch), and one revoked row for drill.
3. Optional: Delimited proxy app for Account Aggregation practice—Description must say proxy.
4. Or complete connection worksheet: host/port, TLS, service userid, firewall owners—without live test.

**Expected result:** Proxy Task Result **or** completed connection worksheet signed in binder.

**If it fails:** Worksheet alone satisfies lab-without-live-target for this lesson.

---

### Task 6 — Examiner Q&A card

Answer in writing:

1. How do you prove a leaver’s RACF USERID is REVOKEd?
2. Who approves `MNB_CICS_PROD_UPDATE`?
3. How is RACF different from `MNB-CoreBanking` CSV governance?

**Expected result:** Three written answers with evidence pointers (Task Results, tickets, cert campaigns).

---

## Acceptance criteria

- [ ] Matrix row applied; RACF - Full preferred documented
- [ ] `MNB-RACF-Core` application shell exists
- [ ] Group catalog with at least four Meridian groups and privilege flags
- [ ] Provisioning + leaver SLA notes complete
- [ ] Lab-without-live-target path done (proxy or worksheet)
- [ ] Examiner Q&A card complete

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Confusing CoreBanking CSV with RACF | Two different planes | Separate apps; link in architecture diagram |
| No RACF connector licensed | Product pack missing | Document LDAP/alternate; escalate |
| SPECIAL users in birthright | Role mistake | Move to privileged request path (Lesson 28) |
| Correlation orphans | Dedicated ops IDs | Identity attribute `mainframeId` + manual correlate |
| Live test blocked | Network/LPAR | Use worksheet path; do not force unsafe access |

---

## Training binder evidence

- Matrix excerpt + architecture diagram
- `MNB-RACF-Core` screenshot
- Group catalog with privilege flags
- Leaver SLA note
- Proxy aggregation or connection worksheet
- Examiner Q&A card

---

## Knowledge check

1. Preferred connector for Mainframe RACF per Meridian matrix?
2. Alternate connector?
3. Name the Meridian RACF application object.
4. What leaver action is mandatory for a USERID?
5. Why is `MNB-CoreBanking` not sufficient alone?

### Answers

1. RACF - Full.  
2. RACF LDAP.  
3. `MNB-RACF-Core`.  
4. REVOKE (plus remove production group connects; escalate SPECIAL).  
5. CoreBanking CSV models business accounts; RACF is the mainframe security plane that gates production regions.

---

## Stretch lab

Map `MNB_CICS_PROD_UPDATE` into a monthly privileged certification population and draft inclusion rule text (no need to run campaign yet).

---

## Summary

- RACF is Meridian’s mainframe security connector, preferred as RACF - Full.
- Govern USERID + groups separately from core banking business extracts.
- Complete training with shell, catalog, policies, and worksheet when no LPAR is available.

---

**Previous:** [Lesson 81 — Oracle E-Business Suite Connector](81-oracle-ebs-connector.md)  
**Next:** [Lesson 83 — Linux / Unix Connector](83-linux-unix-connector.md)
