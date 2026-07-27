# Lesson 51 — Connector Landscape & Registry

**Level:** Intermediate  
**Track:** Connectors  
**Time:** 75–90 min  
**Prereq:** Lesson 50 — Capstone Exam Readiness; Applications `MNB-HR`, `MNB-IT-Access` exist  

**Lab data:**
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/connector-selection-matrix.csv`
- Repo: `lab-data/connectors/README.md`
- Homelab copy: `~/iiq-lab-data/connectors/`

---

## Learning objectives

You will be able to:

- Locate and read `ConnectorRegistry` entries for OOTB connector types in Debug
- Decode `featuresString` values before promising Risk a control capability
- Decide when Meridian should use **DelimitedFile** vs a **Direct** connector vs **Web Services / SCIM**
- Distinguish template applications from production `MNB-*` apps
- Map Meridian systems from the selection matrix to connector families
- Produce a registry worksheet and examiner-ready statement without a live target

---

## Why this matters

**Business.** Meridian National Bank’s IAM team cannot pick connectors by marketing name. Corporate AD, Core Banking DB, Wire Portal, Google Workspace, and the HR extract each need a different connector *family*. Choosing LDAP for AD password reset, or DelimitedFile for a live SAP security model, means `priya.wire` still has wire access after termination because the “disable” you promised Risk never executes.

**Control / audit.** Control owners ask: *“Can IIQ disable this account within SLA?”* The honest answer comes from `ConnectorRegistry` → `featuresString` (`ENABLE`, `PROVISIONING`), not from a vendor slide. Registry evidence belongs in the training binder **before** any go-live. Examiners ask where IIQ *declares* that capability — a screenshot of the registry (or Application type XML) beats a PowerPoint every time.

---

## Concepts

### What ConnectorRegistry actually is

IdentityIQ ships **connector types** registered in an object called **`ConnectorRegistry`**. Think of it as the catalog of engines the product knows how to start: Active Directory - Direct, JDBC, DelimitedFile, Web Services, SCIM 2.0, SAP - Direct, and dozens more. Each type declares:

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Connector type** | OOTB (or custom) class wired in the registry | `Active Directory - Direct` |
| **`featuresString`** | Comma-separated capabilities the framework may invoke | `PROVISIONING,ENABLE,PASSWORD,UNLOCK,…` |
| **Template application** | Starter Application object for that type | Blank AD Direct app with default schema |
| **Application** | Meridian’s owned instance bound to a type | `MNB-ActiveDirectory` with host, schema, policies, owner |

The naive mistake: treat the Applications list as the catalog of what IIQ *can* do. Templates and `MNB-*` apps inherit features from the type — if the type does not declare `PASSWORD`, no amount of UI clicking invents password reset.

### DelimitedFile vs Direct vs Web Services

Meridian uses three broad families. Knowing when each is honest is the core of this lesson:

| Family | When it is the right answer | When it is the wrong answer | Meridian systems |
| --- | --- | --- | --- |
| **DelimitedFile** | Authoritative file drops; no API; teaching governance mechanics; temporary bridge | You need live disable, password, or real-time create | `MNB-HR` (HRIS extract), early inventory apps |
| **Direct** | Vendor/directory has a first-class IIQ connector (AD, OpenLDAP, Oracle DB, SAP, AWS IAM…) | You force LDAP/JDBC generics to fake features the Direct type already owns | Corporate AD, Core banking (JDBC / MSSQL Direct), OpenLDAP lab |
| **Web Services / SCIM** | Custom bank REST, or SaaS with OpenAPI / SCIM | You invent fragile file dumps for a system that already has an API | Wire Portal API, SCIM-compliant SaaS |

**Real-life Meridian example.** Last year a project proposed “just drop a nightly CSV from Wire Portal.” That would have made `MNB-WirePortal` look like `MNB-IT-Access` — inventory only. When `samir.hassan` left, Risk expected disable within the leaver SLA. A file connector cannot flip `active=false` in the Wire Portal API. The correct family was **Web Services** (alternate: SCIM 2.0 if the portal ever exposes it). Lesson 52 turns this into signed selection records; this lesson teaches you to *see* the family choice in the registry first.

### Why featuresString is a promise to Risk

Read the glossary before you open Debug. These are the tokens examiners care about:

| Feature | Promise to Risk | What fails if you fake it |
| --- | --- | --- |
| `PROVISIONING` | Create / modify / delete accounts | Joiner create “succeeds” in IIQ but never hits the target |
| `ENABLE` | Enable / disable | Leaver SLA breach; account stays active |
| `PASSWORD` | Password set / change | Helpdesk catalog lies; tickets bounce |
| `UNLOCK` | Unlock locked accounts | Helpdesk unlock does nothing |
| `SEARCH` | Random access / search accounts | Targeted lookup and some ops patterns unavailable |
| `NO_RANDOM_ACCESS` | Iterate-only (file / LDIF typical) | Do not design “get one account by DN” workflows |
| `DISCOVER_SCHEMA` | Schema discovery from target | Manual schema mapping required |
| `SYNC_PROVISIONING` | Synchronous plan execution | You assumed sync; got async + retry instead |

Source of truth for training: `lab-data/connectors/features-string-glossary.md`.

### Template vs MNB-* — the bank’s naming contract

A **template** is a type starter. A **`MNB-*` Application** is Meridian’s owned instance: connection parameters, schema decisions, correlation, create-identities setting, owner (`helen.ross` for many IAM apps), and Account Aggregation tasks. Templates are not in the runbook. Only `MNB-*` apps with owners and scheduled tasks are in scope for examiners.

> **Production reality.** Lessons 09–16 used DelimitedFile deliberately to teach correlation, roles, and certs. That was pedagogy, not architecture. From Lesson 51 forward, the native connector is the primary path; file mocks are a labeled fallback when no tenant/DC exists.

---

## How it works

```text
  ConnectorRegistry
  (type name + connector class + featuresString)
           │
           ▼
  Template Application  ─── inherits features from type
           │
           ▼
  MNB-* Application     ─── host/schema/policies/owner/tasks
           │
           ├── Account Aggregation  → inventory / evidence
           └── Provisioning plans   → only if features allow
```

| Layer | What you inspect | What you record for Risk |
| --- | --- | --- |
| Registry type | `featuresString` in Debug | Capability ceiling |
| Template | Default schema / feature inheritance | “Type baseline” |
| `MNB-*` app | Connection, schema, create-identities OFF/ON | Runbook scope |
| Task Results | Accounts scanned, errors | Continuous control evidence |

Data flow for a typical Meridian build:

```text
  Architecture picks family (this lesson + Lesson 52)
        → IAM creates MNB-* Application of that type
        → Schema + correlation configured
        → Account Aggregation proves inventory
        → featuresString gates which JML ops go live (Lesson 55)
```

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin` (homelab URL alternate OK)
- [ ] Lab fixtures copied: `cp -R lab-data/connectors ~/iiq-lab-data/connectors` if missing
- [ ] `features-string-glossary.md` and `connector-selection-matrix.csv` readable under `~/iiq-lab-data/connectors/`
- [ ] `MNB-HR` and `MNB-IT-Access` exist from earlier lessons
- [ ] Debug pages accessible as `spadmin`

---

## Lab procedure

### Task 1 — Inventory Meridian systems vs connector families

Before opening Debug, ground yourself in Meridian’s portfolio. The matrix is the contract Architecture already drafted; you are learning to *read* it against registry reality.

1. Open `~/iiq-lab-data/connectors/README.md` and skim the fixture table.
2. Open `connector-selection-matrix.csv` (preview for Lesson 52 — do not invent rows).
3. List at least five Meridian systems you already know: HR extract, IT inventory, Corporate AD, Core Banking, Wire Portal — and add two from the matrix (e.g. AWS IAM, Okta, or Google/Office 365 if present in later lessons).
4. For each, write the **family only** (DelimitedFile, AD Direct, JDBC, Web Services, SCIM, AWS IAM…) — not full connection config.

**Expected result:** Notebook table with ≥7 systems and a connector family each, aligned to the CSV preferred column.

**If it fails:** If matrix missing, copy from repo `lab-data/connectors/`.

### Task 2 — Read the glossary before Debug

Engineers who skip the glossary invent meanings for `NO_RANDOM_ACCESS` and then design broken helpdesk flows. Spend five minutes here.

1. Open `~/iiq-lab-data/connectors/features-string-glossary.md`.
2. Write a one-line plain-English gloss for: `PROVISIONING`, `ENABLE`, `PASSWORD`, `UNLOCK`, `SEARCH`, `NO_RANDOM_ACCESS`, `SYNC_PROVISIONING`.
3. Star the three features that matter most for Meridian leaver SLA (`ENABLE`, `PROVISIONING`) and helpdesk (`PASSWORD` / `UNLOCK`).

**Expected result:** Personal gloss notes; starred leaver/helpdesk features.

### Task 3 — Open ConnectorRegistry in Debug

This is where IIQ *declares* capabilities. You are collecting evidence, not configuring apps yet.

1. Log in as `spadmin`.
2. Navigate **Debug** → object browser (or equivalent Debug menu path).
3. Search / open **ConnectorRegistry** (or list Connector objects if your build labels them separately).
4. Locate entries for at least: **DelimitedFile**, **JDBC**, **LDAP / OpenLDAP**, **Active Directory - Direct**, **Web Services** (add **SCIM 2.0** if present).
5. For each, copy the `featuresString` into your notebook.

**Expected result:** Five (or six) feature strings transcribed. DelimitedFile shows iterate-style features (often includes `NO_RANDOM_ACCESS`); AD Direct / JDBC show richer provisioning features when present.

**If it fails:** If Debug UI differs, export Application template XML for those types and read `featuresString` from XML. Still acceptable evidence.

### Task 4 — Lab without live target — features worksheet

Translate registry tokens into Meridian control asks. Mark gaps honestly — inventing support is how SLAs get signed for ops that cannot run.

1. Using only the glossary and your registry notes, complete:

| Control ask | Required features | Candidate type |
| --- | --- | --- |
| Disable AD on leaver same day | `ENABLE` (+ `PROVISIONING`) | AD Direct |
| Reset Wire Portal password | `PASSWORD` | Web Services / SCIM (if API supports) |
| Certify DB roles on Core Banking | Aggregate + entitlements (`SEARCH` or iterate) | JDBC / MSSQL Direct |
| Nightly HR load, no random search | Iterate OK (`NO_RANDOM_ACCESS` fine) | DelimitedFile |
| Unlock `marcus.approve` after lockout | `UNLOCK` | AD Direct (typical) |

2. Mark any ask where features are **missing** or **Unknown** — do not invent support.
3. Save as `~/iiq-lab-data/connectors/MNB-features-worksheet-51.txt`.

**Expected result:** Worksheet file exists; at least one row notes a gap, alternate connector, or “confirm API.”

**If it fails:** Leave Unknown rather than guessing Y.

### Task 5 — Compare template vs MNB application

Feel the difference between a type starter and a bank-owned app.

1. Applications → open `MNB-HR` (DelimitedFile).
2. Note type, schema, create-identities, file path — no live “target host.”
3. Applications → Add New → pick a **template** type you will use later (e.g. JDBC or LDAP). Create draft name `MNB-Registry-Scratch` **or** cancel without save if policy forbids scratch apps.
4. If created: record default features inherited from type; delete or rename with `-Scratch` suffix per Lesson 03 hygiene.

**Expected result:** Written note: “Template defines features; `MNB-*` adds connection, schema, policies, owner, and tasks.”

**If it fails:** Skip create; document from an existing app’s type string only.

### Task 6 — Map features to Meridian SLAs

Risk signs SLAs against features, not hopes. Close the loop.

1. For each control SLA below, cite the feature that must be Y before Risk signs:

| SLA | Required feature |
| --- | --- |
| Disable AD within 4h of HR leaver | `ENABLE` |
| Helpdesk password reset on AD | `PASSWORD` |
| Unlock after lockout | `UNLOCK` |
| Certify DB entitlements after nightly load | Aggregate + entitlement schema (`SEARCH` or iterate) |
| Authoritative HR identities before 07:00 | Aggregation on DelimitedFile (features do not need `ENABLE`) |

2. Append the SLA↔feature table to `MNB-features-worksheet-51.txt`.

**Expected result:** SLA table filled from glossary/registry; gaps marked, not invented.

### Task 7 — Examiner-ready registry statement

Write the paragraph you would hand an examiner or Architecture review.

1. Draft:

> Meridian selects connectors by ConnectorRegistry `featuresString`. We do not promise ENABLE/PASSWORD unless the registered type declares them. Template apps are not production; only `MNB-*` applications with owners and runbook tasks are in scope. DelimitedFile is for authoritative extracts and inventory bridges; Direct and Web Services/SCIM are for live target control.

2. Attach the Task 4 worksheet path and your systems↔family table.
3. Optional: note that Lesson 52 will produce signed selection records per system.

**Expected result:** Binder paragraph + worksheet path ready for Lesson 52.

---

## Acceptance criteria

- [ ] Glossary read; ≥5 feature strings transcribed from registry/templates
- [ ] Meridian systems↔family table complete (≥7 rows, matrix-aligned)
- [ ] Lab-without-live-target worksheet saved under `~/iiq-lab-data/connectors/`
- [ ] Template vs `MNB-*` distinction documented
- [ ] SLA↔feature table completed
- [ ] Examiner paragraph drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Cannot find ConnectorRegistry | Capability / menu path | Use Debug as `spadmin`; or read type from Application XML |
| `featuresString` empty in UI | Custom/old type | Check Debug XML attribute |
| Lab files missing | Not copied | `cp -R lab-data/connectors ~/iiq-lab-data/` |
| Scratch app clutter | Naming hygiene | Prefix `MNB-` + `-Scratch`; delete after lesson |
| Over-promised `PASSWORD` | Ignored glossary | Re-check registry before Risk sign-off |
| “CSV is fine for Wire Portal” | Wrong family | Require Web Services/SCIM for live disable |

---

## Training binder evidence

- Screenshot: ConnectorRegistry or Application type showing `featuresString` for AD Direct or JDBC
- File: `MNB-features-worksheet-51.txt`
- Note: Meridian systems mapped to families (≥7)
- Examiner paragraph from Task 7

**Examiner question:** “Show me where IIQ declares that this application can disable accounts — not a slide deck.”

---

## Knowledge check

1. What object holds OOTB connector feature declarations?
2. Name three `featuresString` values and what they mean for Risk.
3. When is DelimitedFile the *right* Meridian answer, and when is it wrong?
4. What is the difference between a template application and `MNB-ActiveDirectory`?
5. Which feature often appears on file/LDIF connectors that lack random search?
6. Why must Risk not rely on connector marketing names alone?

### Answers

1. `ConnectorRegistry` (or the registered connector type metadata readable via Debug / Application XML).
2. Examples: `PROVISIONING` = create/modify/delete; `ENABLE` = enable/disable; `PASSWORD` = password ops; `UNLOCK` = unlock; `NO_RANDOM_ACCESS` = iterate-only.
3. Right: authoritative file extracts (HR) and temporary inventory bridges. Wrong: any system where you promised live disable, password, or API-driven create (e.g. Wire Portal, AD).
4. Template is the type starter; `MNB-*` is Meridian’s owned instance with connection, schema, policies, owner, and tasks.
5. `NO_RANDOM_ACCESS`.
6. Features are declared per type; promising controls the connector cannot execute fails audits and SLAs.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “ConnectorRegistry” and “connector featuresString” for your IIQ version; this is the authoritative list of declared capabilities.
- [SailPoint Community (Compass)](https://community.sailpoint.com/) — search “featuresString PROVISIONING ENABLE” for real-world threads on what a type actually supports after upgrade.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — connector selection and custom OpenConnector discussions when OOTB types do not fit.
- [NIST SP 800-53 Rev. 5 — AC / AU families](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — why “disable within SLA” and evidence of capability matter as access-control and audit requirements, not just IAM preferences.
- [FFIEC Information Security booklet](https://www.ffiec.gov/press/pr110622.htm) — banking examiner lens on access management and vendor/system inventory completeness (search current FFIEC IS booklet).

---

## Stretch lab

- Export one Application XML and highlight the connector class / type attributes and `featuresString`.
- Cross-walk `features-string-glossary.md` to every row you will complete in Lesson 52’s matrix.
- List which Meridian apps from Lessons 09–20 were DelimitedFile and which controls they therefore cannot do live (e.g. remote password, remote disable).

---

## Summary

- Connector choice starts at `ConnectorRegistry` and `featuresString`, not vendor glossaries alone.
- DelimitedFile, Direct, and Web Services/SCIM are different honesty levels — map Meridian systems to the right family before build.
- Template apps seed types; only `MNB-*` apps with owners and tasks enter the runbook and the examiner conversation.

---

**Previous:** [Lesson 50 — Capstone Exam Readiness](50-capstone-exam-readiness.md)  
**Next:** [Lesson 52 — Connector Selection for Meridian](52-connector-selection-for-meridian.md)
