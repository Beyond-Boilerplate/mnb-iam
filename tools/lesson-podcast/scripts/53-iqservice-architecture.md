---
title: "Lesson 53 — IQService Architecture"
stem: 53-iqservice-architecture
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
source: auto-draft
---

## cold-open

Hey — welcome back to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson 53: IQService Architecture.

This is a theory companion. Listen for the ideas and the control story, then use the written lesson for any binder sketches or design tasks.

Grab a notebook.

By the end of this lesson, you will be able to: Explain why Active Directory Direct depends on a Windows IQService agent and what the IIQ JVM cannot do alone; Sketch Meridian’s IQService placement (near DCs, TLS, ports, forest/domain trust assumptions); Complete the enterprise IQService install/config worksheet and checklist without a live domain; Document SPN/cert, least-privilege service account, and OU/group/Exchange scope decisions; Separate IIQ server duties from IQService host duties for runbooks and examiner questions.

## why-this-matters

Business. IdentityIQ often runs on Linux or containers. Meridian’s Corporate AD provisioning — password set, enable/disable, many Exchange mailbox operations — does not complete inside the IIQ JVM alone. Those operations execute on a Windows host running IQService, talking to domain controllers near the AD site. When IQService was mis-placed across a WAN last year, password resets for amelia.brooks timed out during a Monday morning helpdesk surge, and the business blamed “SailPoint” instead of network design.

Control / audit. Network diagrams, TLS evidence, and least-privilege service-account documentation are examiner artifacts. “We configured the AD application” without IQService architecture is incomplete. The OCC-style question is: Where does IdentityIQ terminate TLS to perform AD password reset, and who owns that Windows host?

---

## concepts-why-a-windows-agent-exists

Why a Windows agent exists.

The Active Directory - Direct connector is designed so that directory-mutating and Windows-security operations run where Windows APIs and AD admin protocols are native. IQService is that agent:

Concern: Password set / change; Without IQService (naive): IIQ Linux process tries remote Windows crypto/RPC — fragile or unsupported for Meridian’s pattern; With IQService (Meridian design): IQService executes password ops near the DC. Concern: Enable / disable; Without IQService (naive): May partially work via LDAP modify depending on build/path — not the enterprise pattern Meridian standardizes; With IQService (Meridian design): IQService path for consistent ENABLE ops. Concern: Exchange / mailbox; Without IQService (naive): Needs Windows/Exchange management surface; With IQService (Meridian design): IQService host in scope when Exchange = yes. Concern: Network blast radius; Without IQService (naive): IIQ tier opened wide to every DC; With IQService (Meridian design): IIQ → IQService (TLS) only; IQService → DC.

Real-life Meridian example. A contractor proposed “just open LDAPS from the IIQ pod CIDR to every DC in meridiannb.com.” Security rejected it: the IIQ tier would hold broad directory reach, and password operations still needed a Windows execution host. The approved pattern: narrow allowlist IIQ → IQService, IQService adjacent to DCs, TLS on the IQService listener, service account least privilege — not Domain Admin.

## concepts-tls-ports-and-trust

TLS, ports, and trust.

Item: Listener TLS; What to decide: IQService must not run cleartext in production; Meridian lab default (document, then confirm in install guide): TLS enabled; cert CN/SAN matches hostname. Item: Port; What to decide: Build-specific — never hardcode without checking; Meridian lab default (document, then confirm in install guide): Common lab placeholder :5050 — confirm in your IQService install guide. Item: Trust; What to decide: IIQ must trust the IQService cert (or private CA); Meridian lab default (document, then confirm in install guide): Import issuing CA into IIQ trust store. Item: Forest / domain; What to decide: Single forest vs multi-domain; Meridian lab default (document, then confirm in install guide): Lab: meridiannb.com; production: document GC usage. Item: Forest trust; What to decide: Cross-forest accounts?; Meridian lab default (document, then confirm in install guide): If Meridian acquires a bank with a separate forest, IQService placement and trust path become a project — do not assume one IQService sees everything.

Cleartext IQService on the corporate network is a finding. Treat the IQService credential and TLS private key like domain-admin-adjacent secrets: vault them, rotate them, never commit them.

## concepts-least-privilege-and-the-service

Least privilege and the service account.

The IQService Windows service (and the AD account used for connector operations) must be documented least privilege, not Domain Admin:

Create/modify/disable users in scoped OUs (employees vs contractors)
Manage membership of security groups in scope
Password reset rights only where helpdesk/JML requires them
Exchange rights only if mailbox provisioning is in scope

Wrong way: “Give it Domain Admin so Test Connection works.” That passes a lab demo and fails every bank audit. Record the rights model in the worksheet even when the lab has no live DC.

## concepts-what-the-meridian-checklist-cov

What the Meridian checklist covers.

The repo checklist (ad/iqservice-checklist.md) is the enterprise punch list:

Domain-join / install account with least privilege documented
IQService on Windows host near DCs, TLS enabled
Service account + SPN / cert plan
Application type: Active Directory - Direct
Forest/domain; GC usage
Account OU search DNs (employees vs contractors)
Group aggregation scope (security groups only?)
Exchange / mailbox required? Password Interceptor in scope?
Provisioning policies: create, enable, disable, move OU on leaver
Correlation: sAMAccountName ↔ userName, employeeID ↔ employeeId
Test plan: aggregate → correlate → create → disable → delete (lab only)

---

## how-it-works

Component: IdentityIQ; Duty: Orchestrates plans, stores Application config, schedules aggregation, stores Task Results; Not responsible for: Native Windows password API execution. Component: IQService; Duty: Executes AD/Windows connector operations securely near DCs; Not responsible for: Being the identity source of truth. Component: DC / GC; Duty: Directory source of truth for accounts/groups; Not responsible for: Running IIQ workflows. Component: Service account; Duty: Authenticated principal for directory ops; Not responsible for: Interactive human login / Domain Admin.

Traffic intent for Meridian (document actual ports from your build):

```text
 [IIQ pods / VM :8080]

TLS :5050 (example — confirm in install guide)

[Windows IQService — site-adjacent to DCs]

[DC / GC — meridiannb.com]
```

Firewall story examiners like: allowlist IIQ → IQService only; do not open IIQ → every DC for the Direct+IQService pattern unless your build’s documentation explicitly requires additional LDAP paths — and if it does, document them.

---

## close

AD Direct at Meridian implies IQService architecture — placement, TLS, and least privilege — not only an Application form.
Real-world setup is an install/config worksheet Windows ops and IAM share before Lesson 56 builds the app.
Live DC optional; checklist + network + install card + failure modes are mandatory evidence.

---

Previous: Lesson 52 — Connector Selection for Meridian 
Next: Lesson 54 — Aggregation Patterns Advanced

When you’re ready, open the written lesson for binder work, then move on in the Academy. That’s your briefing for Lesson 53.
