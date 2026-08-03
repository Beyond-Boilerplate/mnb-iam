---
title: "Lesson 55 — Provisioning Feature Matrix"
stem: 55-provisioning-feature-matrix
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 55: Provisioning Feature Matrix.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Read a connector’s featuresString and translate each flag into a concrete JML capability; Build Meridian’s provisioning feature matrix for eight applications with evidence-backed Y / N / Unknown; Write test cases (Expected result / If it fails) for ENABLE, PASSWORD, UNLOCK, and CRUD before any connector build; Align leaver disable scope to apps where ENABLE is proven — not assumed; Hand Risk a signed capability matrix that survives examiner comparison to IdentityRequest outcomes.

## why-this-matters

Business. Last year Meridian’s joiner playbook promised “disable every account within one hour of termination.” The Wire Portal SCIM path could flip active=false, but the helpdesk catalog still offered Unlock for a SaaS product that never declared UNLOCK. When samir.hassan left Commercial Lending, ops burned ninety minutes retrying unlocks that could never succeed — and meanwhile his wire entitlements stayed live until someone noticed. Impossible promises are worse than honest gaps.

Control / audit. Examiners compare the leaver control statement to what IdentityIQ can actually do. The feature matrix is the contract: these apps have ENABLE; those are inventory-only. Without it, every failed IdentityRequest looks like a connector bug when it is often a configuration lie.

---

## concepts-what-featuresstring-actually-me

What featuresString actually means.

IdentityIQ connectors advertise capabilities as a space-delimited featuresString on the connector registry entry (Debug → ConnectorRegistry). The glossary in features-string-glossary.md is your dictionary; the registry is the source of truth for this build.

Feature: PROVISIONING; Plain English: Connector can create / modify / delete accounts; JML / ops use at Meridian: Joiner create, entitlement grant/revoke. Feature: SYNC_PROVISIONING; Plain English: Plan can execute synchronously; JML / ops use at Meridian: Wire apps when Risk wants immediate confirm. Feature: ENABLE; Plain English: Enable / disable account; JML / ops use at Meridian: Leaver disable SLA. Feature: PASSWORD; Plain English: Password set / change; JML / ops use at Meridian: Helpdesk reset (AD needs IQService). Feature: UNLOCK; Plain English: Unlock locked accounts; JML / ops use at Meridian: Helpdesk unlock catalog. Feature: CURRENT_PASSWORD; Plain English: Change requires old password; JML / ops use at Meridian: Self-service policy constraint. Feature: SEARCH; Plain English: Random-access get by native id; JML / ops use at Meridian: Single-account refresh. Feature: NO_RANDOM_ACCESS; Plain English: Iterate-only; JML / ops use at Meridian: Typical delimited / bulk inventory.

The naive mistake: marking every cell Y because “IIQ provisions everything.” At a bank under exam, a false Y becomes a finding the moment disable fails and your matrix said it should work.

## concepts-features-vs-policies-vs-promise

Features vs policies vs promises.

Three different layers get confused:

Feature — the connector can do the operation (registry).
Policy — you configured create/disable SQL, AD enable, SCIM PATCH, etc.
Promise — Risk / runbooks obligate Meridian to do it within an SLA.

All three must align. Feature without policy = green Test Connection, red IdentityRequest. Policy without feature = you wrote SQL the connector never calls. Promise without either = examiner finding.

## concepts-meridian-application-set-this-l

Meridian application set (this lesson).

Application: MNB-HR; Type (matrix / track): DelimitedFile (authoritative); Why it is on the matrix: Inbound truth — not a disable target. Application: MNB-IT-Access; Type (matrix / track): DelimitedFile; Why it is on the matrix: Inventory / birthright evidence. Application: MNB-ActiveDirectory; Type (matrix / track): AD Direct; Why it is on the matrix: Primary ENABLE / PASSWORD / UNLOCK. Application: MNB-OpenLDAP; Type (matrix / track): OpenLDAP Direct; Why it is on the matrix: Directory alternate. Application: MNB-CoreBanking-JDBC; Type (matrix / track): JDBC; Why it is on the matrix: Status-based ENABLE via SQL/procs. Application: MNB-WirePortal-WS; Type (matrix / track): Web Services; Why it is on the matrix: API-dependent features. Application: MNB-EntraID; Type (matrix / track): Azure AD; Why it is on the matrix: Cloud directory disable. Application: MNB-MSSQL-Reporting; Type (matrix / track): MSSQL Direct; Why it is on the matrix: Login disable / roles.

---

## how-it-works

When a provisioning plan includes Disable, IIQ checks whether the Application’s connector supports ENABLE, then routes through the connector’s enable/disable implementation (AD attribute, JDBC status SQL, SCIM active, etc.). If the feature is absent, the plan fails or no-ops depending on configuration — either way, your matrix should have predicted it.

Matrix cell: Y; Meaning for Meridian: Registry (or proven API) supports it; policy will be built. Matrix cell: N; Meaning for Meridian: Do not promise; remove from helpdesk / leaver scope. Matrix cell: Unknown; Meaning for Meridian: Confirm in build lesson; do not sign as Y yet.

---

## close

Feature matrices prevent impossible JML promises; every Y needs registry or API evidence.
ENABLE scope drives leaver SLAs; PASSWORD/UNLOCK drive helpdesk catalogs; Unknown is honest.
Test cases with Expected result / If it fails become the build QA script for Lessons 56+.

---

Previous: Lesson 54 — Aggregation Patterns Advanced 
Next: Lesson 56 — Active Directory Connector

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 55.
