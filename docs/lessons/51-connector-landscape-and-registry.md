# Lesson 51 — Connector Landscape & Registry

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Connectors |
| **Time** | 60–75 minutes |
| **Prereq** | Lesson 50; Applications `MNB-HR`, `MNB-IT-Access` exist |
| **Lab data** | `~/iiq-lab-data/connectors/features-string-glossary.md`; `lab-data/connectors/README.md` |

## Learning objectives

You will be able to:

- Locate and read `ConnectorRegistry` entries for OOTB connector types
- Decode `featuresString` values before promising Risk a control capability
- Distinguish template applications from Meridian production `MNB-*` apps
- Document which Meridian systems map to which connector families
- Complete a registry worksheet without a live target system

## Why this matters

Meridian National Bank’s IAM team cannot pick connectors by marketing name. Wire Portal, Core Banking DB, Corporate AD, and Entra ID each require different feature sets. Choosing LDAP for AD password reset, or DelimitedFile for a live SAP security model, creates examiner findings when controls fail.

**Control / audit:** Control owners ask “Can IIQ disable this account within SLA?” Answer from `featuresString` (ENABLE, PROVISIONING), not from hope. Registry evidence belongs in the training binder before any go-live.

## Concepts

IdentityIQ ships **connector types** registered in `ConnectorRegistry`. Each type declares a **featuresString**—comma-separated capabilities the connector framework can invoke.

| Term | Meaning |
| --- | --- |
| Connector type | OOTB or custom class wired in registry (e.g. Active Directory - Direct) |
| Template application | Starter Application object for that type |
| `featuresString` | Declared capabilities (PROVISIONING, ENABLE, PASSWORD, …) |
| Application | Meridian instance (`MNB-ActiveDirectory`) bound to a type |

```text
  ConnectorRegistry (type + featuresString)
           |
           v
  Template Application
           |
           v
  MNB-* Application (host, schema, policies)
           |
           v
  Aggregation / Provisioning tasks
```

Read the glossary first:

| Feature | Promise to Risk |
| --- | --- |
| `PROVISIONING` | Create/modify/delete accounts |
| `ENABLE` | Enable/disable |
| `PASSWORD` | Password set/change |
| `UNLOCK` | Unlock locked accounts |
| `DISCOVER_SCHEMA` | Schema discovery from target |
| `NO_RANDOM_ACCESS` | Iterate-only (file/LDIF typical) |
| `SEARCH` | Random access / search accounts |

Source: `lab-data/connectors/features-string-glossary.md`.

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` (homelab URL alternate OK)
- [ ] Lab fixtures copied: `cp -R lab-data/connectors ~/iiq-lab-data/connectors` if missing
- [ ] `features-string-glossary.md` readable under `~/iiq-lab-data/connectors/`
- [ ] Debug pages accessible as `spadmin` (lab)

## Lab procedure

### Task 1 — Inventory Meridian systems vs connector families

1. Open `~/iiq-lab-data/connectors/README.md` and skim the fixture table.
2. Open `connector-selection-matrix.csv` (preview for Lesson 52).
3. List five Meridian systems you already know from earlier lessons: HR extract, IT inventory, AD, Core Banking, Wire Portal.
4. For each, write the *family* only (DelimitedFile, AD Direct, JDBC, Web Services)—not full config.

**Expected result:** Notebook table with ≥5 systems and a connector family each.

**If it fails:** If matrix missing, copy from repo `lab-data/connectors/`.

### Task 2 — Open ConnectorRegistry in Debug

1. Log in as `spadmin`.
2. Navigate **Debug** → object browser (or equivalent Debug menu path).
3. Search / open **ConnectorRegistry** (or list Connector objects if your build labels them separately).
4. Locate entries for: DelimitedFile, JDBC, LDAP / OpenLDAP, Active Directory - Direct, Web Services.
5. For each, copy the `featuresString` into your notebook.

**Expected result:** Five feature strings transcribed; DelimitedFile shows iterate-style features (often includes `NO_RANDOM_ACCESS`); AD/JDBC show richer provisioning features when present.

**If it fails:** If Debug UI differs, export Application template XML for those types and read `featuresString` from XML.

### Task 3 — Lab without live target — features worksheet

1. Using only `features-string-glossary.md` and your registry notes, complete this Meridian worksheet:

| Control ask | Required features | Candidate type |
| --- | --- | --- |
| Disable AD on leaver same day | ENABLE (+ PROVISIONING) | AD Direct |
| Reset Wire Portal password | PASSWORD | Web Services / SCIM |
| Certify DB roles on Core Banking | SEARCH or aggregate + entitlements | JDBC / MSSQL Direct |
| Nightly HR load, no random search | Aggregate iterate OK | DelimitedFile |

2. Mark any ask where features are **missing**—do not invent support.
3. Save worksheet as `~/iiq-lab-data/connectors/MNB-features-worksheet-51.txt`.

**Expected result:** Worksheet file exists; at least one row notes a gap or alternate connector.

### Task 4 — Compare template vs MNB application

1. Applications → open `MNB-HR` (DelimitedFile).
2. Note type, schema, create-identities, path—no live “target host.”
3. Applications → Add New → pick a **template** type you will use later (e.g. JDBC or LDAP)—create draft name `MNB-Registry-Scratch` **or** cancel without save if policy forbids scratch apps.
4. If created: record default features inherited from type; delete or rename with `-Scratch` suffix per Lesson 03 hygiene.

**Expected result:** Written note: “Template defines features; `MNB-*` adds connection, schema, policies.”

**If it fails:** Skip create; document from an existing app’s type string only.

### Task 5 — Map features to Meridian SLAs

1. For each control SLA below, cite the feature that must be Y before Risk signs:

| SLA | Required feature |
| --- | --- |
| Disable AD within 4h of HR leaver | `ENABLE` |
| Helpdesk password reset on AD | `PASSWORD` |
| Unlock after lockout | `UNLOCK` |
| Certify DB entitlements after nightly load | Aggregate + entitlement schema (`SEARCH` or iterate) |

2. Expected result: SLA table filled from glossary. If it fails: leave gap marked—do not invent features.

**Expected result:** SLA↔feature table in worksheet file.

### Task 6 — Examiner-ready registry statement

1. Draft one paragraph for the training binder:

> Meridian selects connectors by ConnectorRegistry `featuresString`. We do not promise ENABLE/PASSWORD unless the registered type declares them. Template apps are not production; only `MNB-*` applications with owners and runbook tasks are in scope.

2. Attach the Task 3 worksheet path.

**Expected result:** Binder paragraph + worksheet path ready for Lesson 52.

## Acceptance criteria

- [ ] Glossary read; five feature strings transcribed from registry/templates
- [ ] Meridian systems↔family table complete
- [ ] Lab-without-live-target worksheet saved under `~/iiq-lab-data/connectors/`
- [ ] Template vs `MNB-*` distinction documented
- [ ] SLA↔feature table completed
- [ ] Examiner paragraph drafted

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Cannot find ConnectorRegistry | Capability / menu path | Use Debug as spadmin; or read type from Application XML |
| featuresString empty in UI | Custom/old type | Check Debug XML attribute |
| Lab files missing | Not copied | `cp -R lab-data/connectors ~/iiq-lab-data/` |
| Scratch app clutter | Naming hygiene | Prefix `MNB-` + `-Scratch`; delete after lesson |
| Over-promised PASSWORD | Ignored glossary | Re-check registry before Risk sign-off |

## Training binder evidence

- Screenshot: ConnectorRegistry or Application type showing `featuresString` for AD Direct or JDBC
- File: `MNB-features-worksheet-51.txt`
- Note: five Meridian systems mapped to families

**Examiner question:** “Show me where IIQ declares that this application can disable accounts—not a slide deck.”

## Knowledge check

1. What object holds OOTB connector feature declarations?
2. Name three `featuresString` values and what they mean.
3. Why must Risk not rely on connector marketing names alone?
4. What is the difference between a template application and `MNB-ActiveDirectory`?
5. Which feature often appears on file/LDIF connectors that lack random search?

### Answers

1. `ConnectorRegistry` (or the registered connector type metadata readable via Debug).
2. Examples: `PROVISIONING` = create/modify/delete; `ENABLE` = enable/disable; `PASSWORD` = password ops; `UNLOCK` = unlock; `NO_RANDOM_ACCESS` = iterate-only.
3. Features are declared per type; promising controls the connector cannot execute fails audits and SLAs.
4. Template is the type starter; `MNB-*` is Meridian’s owned instance with connection, schema, policies, and tasks.
5. `NO_RANDOM_ACCESS`.

## Stretch lab

- Export one Application XML and highlight the connector class / type attributes.
- Cross-walk `features-string-glossary.md` to every row you will complete in Lesson 52’s matrix.
- List which Meridian apps from Lessons 09–20 were DelimitedFile and which controls they therefore cannot do live (e.g. remote password).

## Summary

- Connector choice starts at `ConnectorRegistry` and `featuresString`, not vendor glossaries alone.
- Meridian worksheets record what IIQ can actually do before build.
- Template apps seed types; only `MNB-*` apps enter the runbook.

---

**Previous:** [Lesson 50 — Capstone Exam Readiness](50-capstone-exam-readiness.md)  
**Next:** [Lesson 52 — Connector Selection for Meridian](52-connector-selection-for-meridian.md)
