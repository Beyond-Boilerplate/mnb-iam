---
title: "Lesson 51 — Connector Landscape & Registry"
stem: 51-connector-landscape-and-registry
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 51: Connector Landscape & Registry.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Locate and read ConnectorRegistry entries for OOTB connector types in Debug; Decode featuresString values before promising Risk a control capability; Decide when Meridian should use DelimitedFile vs a Direct connector vs Web Services / SCIM; Distinguish template applications from production MNB-* apps; Map Meridian systems from the selection matrix to connector families.

## why-this-matters

Business. Meridian National Bank’s IAM team cannot pick connectors by marketing name. Corporate AD, Core Banking DB, Wire Portal, Google Workspace, and the HR extract each need a different connector family. Choosing LDAP for AD password reset, or DelimitedFile for a live SAP security model, means priya.wire still has wire access after termination because the “disable” you promised Risk never executes.

Control / audit. Control owners ask: “Can IIQ disable this account within SLA?” The honest answer comes from ConnectorRegistry → featuresString (ENABLE, PROVISIONING), not from a vendor slide. Registry evidence belongs in the training binder before any go-live. Examiners ask where IIQ declares that capability — a screenshot of the registry (or Application type XML) beats a PowerPoint every time.

---

## concepts-what-connectorregistry-actually

What ConnectorRegistry actually is.

IdentityIQ ships connector types registered in an object called ConnectorRegistry. Think of it as the catalog of engines the product knows how to start: Active Directory - Direct, JDBC, DelimitedFile, Web Services, SCIM 2.0, SAP - Direct, and dozens more. Each type declares:

Term: Connector type; Plain English: OOTB (or custom) class wired in the registry; Meridian example: Active Directory - Direct. Term: featuresString; Plain English: Comma-separated capabilities the framework may invoke; Meridian example: PROVISIONING,ENABLE,PASSWORD,UNLOCK,…. Term: Template application; Plain English: Starter Application object for that type; Meridian example: Blank AD Direct app with default schema. Term: Application; Plain English: Meridian’s owned instance bound to a type; Meridian example: MNB-ActiveDirectory with host, schema, policies, owner.

The naive mistake: treat the Applications list as the catalog of what IIQ can do. Templates and MNB-* apps inherit features from the type — if the type does not declare PASSWORD, no amount of UI clicking invents password reset.

## concepts-delimitedfile-vs-direct-vs-web-

DelimitedFile vs Direct vs Web Services.

Meridian uses three broad families. Knowing when each is honest is the core of this lesson:

Family: DelimitedFile; When it is the right answer: Authoritative file drops; no API; teaching governance mechanics; temporary bridge; When it is the wrong answer: You need live disable, password, or real-time create; Meridian systems: MNB-HR (HRIS extract), early inventory apps. Family: Direct; When it is the right answer: Vendor/directory has a first-class IIQ connector (AD, OpenLDAP, Oracle DB, SAP, AWS IAM…); When it is the wrong answer: You force LDAP/JDBC generics to fake features the Direct type already owns; Meridian systems: Corporate AD, Core banking (JDBC / MSSQL Direct), OpenLDAP lab. Family: Web Services / SCIM; When it is the right answer: Custom bank REST, or SaaS with OpenAPI / SCIM; When it is the wrong answer: You invent fragile file dumps for a system that already has an API; Meridian systems: Wire Portal API, SCIM-compliant SaaS.

Real-life Meridian example. Last year a project proposed “just drop a nightly CSV from Wire Portal.” That would have made MNB-WirePortal look like MNB-IT-Access — inventory only. When samir.hassan left, Risk expected disable within the leaver SLA. A file connector cannot flip active=false in the Wire Portal API. The correct family was Web Services (alternate: SCIM 2.0 if the portal ever exposes it). Lesson 52 turns this into signed selection records; this lesson teaches you to see the family choice in the registry first.

## concepts-why-featuresstring-is-a-promise

Why featuresString is a promise to Risk.

Read the glossary before you open Debug. These are the tokens examiners care about:

Feature: PROVISIONING; Promise to Risk: Create / modify / delete accounts; What fails if you fake it: Joiner create “succeeds” in IIQ but never hits the target. Feature: ENABLE; Promise to Risk: Enable / disable; What fails if you fake it: Leaver SLA breach; account stays active. Feature: PASSWORD; Promise to Risk: Password set / change; What fails if you fake it: Helpdesk catalog lies; tickets bounce. Feature: UNLOCK; Promise to Risk: Unlock locked accounts; What fails if you fake it: Helpdesk unlock does nothing. Feature: SEARCH; Promise to Risk: Random access / search accounts; What fails if you fake it: Targeted lookup and some ops patterns unavailable. Feature: NO_RANDOM_ACCESS; Promise to Risk: Iterate-only (file / LDIF typical); What fails if you fake it: Do not design “get one account by DN” workflows. Feature: DISCOVER_SCHEMA; Promise to Risk: Schema discovery from target; What fails if you fake it: Manual schema mapping required. Feature: SYNC_PROVISIONING; Promise to Risk: Synchronous plan execution; What fails if you fake it: You assumed sync; got async + retry instead.

Source of truth for training: lab-data/connectors/features-string-glossary.md.

## concepts-template-vs-mnb-the-bank-s-nami

Template vs MNB-* — the bank’s naming contract.

A template is a type starter. A **MNB-* Application** is Meridian’s owned instance: connection parameters, schema decisions, correlation, create-identities setting, owner (helen.ross for many IAM apps), and Account Aggregation tasks. Templates are not in the runbook. Only MNB-* apps with owners and scheduled tasks are in scope for examiners.

Production reality. Lessons 09–16 used DelimitedFile deliberately to teach correlation, roles, and certs. That was pedagogy, not architecture. From Lesson 51 forward, the native connector is the primary path; file mocks are a labeled fallback when no tenant/DC exists.

---

## how-it-works

Layer: Registry type; What you inspect: featuresString in Debug; What you record for Risk: Capability ceiling. Layer: Template; What you inspect: Default schema / feature inheritance; What you record for Risk: “Type baseline”. Layer: MNB-* app; What you inspect: Connection, schema, create-identities OFF/ON; What you record for Risk: Runbook scope. Layer: Task Results; What you inspect: Accounts scanned, errors; What you record for Risk: Continuous control evidence.

Data flow for a typical Meridian build:

 

---

## close

Connector choice starts at ConnectorRegistry and featuresString, not vendor glossaries alone.
DelimitedFile, Direct, and Web Services/SCIM are different honesty levels — map Meridian systems to the right family before build.
Template apps seed types; only MNB-* apps with owners and tasks enter the runbook and the examiner conversation.

---

Previous: Lesson 50 — Capstone Exam Readiness 
Next: Lesson 52 — Connector Selection for Meridian

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 51.
