---
title: "Lesson 52 — Connector Selection for Meridian"
stem: 52-connector-selection-for-meridian
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 52: Connector Selection for Meridian.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Read and extend Meridian’s connector selection matrix CSV as an Architecture contract; Apply decision criteria: authoritative vs target, featuresString, network path, IQService dependency; Map every priority Meridian system to preferred and alternate connectors with reject reasons; Justify AD Direct vs LDAP, JDBC vs MSSQL Direct, SCIM vs Web Services; Produce signed selection records for Risk / Architecture without a live target.

## why-this-matters

Business. Banks fail connector projects when Architecture picks “LDAP for everything” or “REST for everything.” Meridian’s matrix is the single source of preferred connectors: Corporate AD → Active Directory Direct, Core banking DB → JDBC (or MSSQL Direct), Wire Portal → Web Services. When jordan.reed’s team onboarded a new payments API last year using a generic LDAP assumption, password and disable never worked — three weeks of rework before helen.ross could sign the go-live.

Control / audit. Examiners ask who approved the connector type and whether an alternate was considered. Your completed matrix row plus a selection record (preferred, alternate, reject reason, owner, SLA) is that evidence. “We used what the implementer liked” fails the conversation.

---

## concepts-decision-criteria-meridian-actu

Decision criteria Meridian actually uses.

Selection is not a popularity contest. Walk every system through the same criteria:

Criterion: Authoritative vs target; Question: Does this system create identities or receive accounts?; Meridian implication: Only MNB-HR (and SAP HR / Workday if used) is authoritative; everything else has create-identities OFF. Criterion: featuresString; Question: Do we need ENABLE / PASSWORD / UNLOCK / PROVISIONING?; Meridian implication: If yes, DelimitedFile is almost never enough. Criterion: Network path; Question: Can IIQ reach the API/DB/directory from the IIQ tier?; Meridian implication: Wire Portal and cloud SaaS need egress + secrets; AD Direct needs IQService near DCs. Criterion: IQService; Question: Is this Windows/AD/Exchange ops?; Meridian implication: Corporate AD → plan Windows host, TLS, least-privilege account (Lesson 53). Criterion: Native vs generic; Question: Is there an OOTB Direct/SaaS connector?; Meridian implication: Prefer Salesforce / Okta / AWS IAM native over generic Web Services when available. Criterion: Provisioning shape; Question: Stored-proc, SCIM, or raw REST/SQL?; Meridian implication: Core banking prefers stored-proc — raw UPDATE is an examiner finding waiting to happen.

Real-life Meridian example. Core Banking was almost wired with ad-hoc JDBC UPDATE mnb_app_accounts SET status=…. Payments risk (marcus.approve’s org) rejected it: account state changes must go through the bank’s stored procedures so audit triggers fire. Preferred connector stayed JDBC; the provisioning pattern became “call proc,” not “run naked SQL.” That decision belongs in the selection record, not in a forgotten Slack thread.

## concepts-authoritative-vs-target-the-cre

Authoritative vs target — the create-identities trap.

Role: Authoritative; Meridian apps: MNB-HR (HRIS extract); future SAP HR / Workday; create-identities: ON (or HR-only pipeline); Why: Identities are born here. Role: Target; Meridian apps: AD, Entra, Core Banking, Wire Portal, AWS, Google, SAP security; create-identities: OFF; Why: Accounts correlate to existing cubes; never spawn duplicate people.

The wrong way: turn create-identities on for AD because “we saw empty cubes.” That creates shadow identities on every uncorrelated account and poisons certifications. Fix correlation (Lessons 17–19); do not invent people from targets.

## concepts-preferred-vs-alternate-always-d

Preferred vs alternate — always document the reject.

Every matrix row has a preferred and an alternate. Selection records must say why the alternate lost:

System: Corporate AD; Preferred: Active Directory - Direct; Alternate: LDAP; Typical reject reason: LDAP lacks first-class IQService password / Exchange patterns Meridian requires. System: Core banking DB; Preferred: JDBC; Alternate: Microsoft SQL Server - Direct; Typical reject reason: Either can work; Meridian standardizes on JDBC + stored-proc unless MSSQL Direct is mandated. System: Wire Portal API; Preferred: Web Services; Alternate: SCIM 2.0; Typical reject reason: Portal is custom REST today; SCIM wins if vendor later ships standards-compliant SCIM. System: SCIM-compliant SaaS; Preferred: SCIM 2.0; Alternate: Web Services; Typical reject reason: Prefer SCIM when vendor supports it — less mapping debt. System: OpenLDAP; Preferred: OpenLDAP - Direct; Alternate: LDAP; Typical reject reason: Lab/generic RFC directory — Direct type when available.

## concepts-meridian-portfolio-snapshot-fro

Meridian portfolio snapshot (from the matrix).

System (matrix): Corporate AD; Preferred: Active Directory - Direct; Alternate: LDAP; Meridian note: Requires IQService for password/enable/Exchange. System (matrix): Entra ID / Azure AD; Preferred: Azure Active Directory; Alternate: SCIM 2.0; Meridian note: Cloud directory + SaaS SSO. System (matrix): OpenLDAP / FreeIPA; Preferred: OpenLDAP - Direct; Alternate: LDAP; Meridian note: Lab directory. System (matrix): HRIS extract; Preferred: DelimitedFile; Alternate: JDBC; Meridian note: Authoritative file still valid. System (matrix): Core banking DB; Preferred: JDBC; Alternate: Microsoft SQL Server - Direct; Meridian note: Prefer stored-proc provisioning. System (matrix): Wire Portal API; Preferred: Web Services; Alternate: SCIM 2.0; Meridian note: Custom bank REST. System (matrix): Salesforce CRM; Preferred: Salesforce; Alternate: Web Services; Meridian note: Native SFDC connector. System (matrix): SAP ECC security; Preferred: SAP - Direct; Alternate: SAP HR/HCM; Meridian note: App security vs HR authoritative.

---

## how-it-works

Artifact: connector-selection-matrix.csv; Owner: Architecture / IAM; Purpose: System → connector contract. Artifact: Selection record (MNB-connector-selection-record-52.md); Owner: IAM lead (helen.ross); Purpose: Preferred, alternate, reject, SLA, live-target flag. Artifact: Lesson 51 features worksheet; Owner: IAM engineer; Purpose: Capability ceiling per type. Artifact: Application object; Owner: IAM build; Purpose: Implements the signed choice.

---

## close

Meridian’s connector-selection-matrix.csv is the system→connector contract; selection records add reject reasons, features, SLAs, and IQService flags.
Decision criteria (auth vs target, featuresString, network, IQService) prevent “LDAP for everything” failures.
Live targets are optional; signed records unlock later connector labs without promising impossible controls.

---

Previous: Lesson 51 — Connector Landscape & Registry 
Next: Lesson 53 — IQService Architecture

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 52.
