# Meridian IAM Audio — show continuity

Agents append per-episode must-cover / do-not-repeat seeds here so the blender
can compress repeated foundations across the show.

### E01 — What IAM Actually Is (At a Bank)
**Must-cover:**
- IAM = Identity and Access Management: governance and proof, not password resets.
- IIQ = SailPoint IdentityIQ: governance platform that connects to AD, SAP, wire portal, AWS.
- Six core constructs: identity, account, entitlement, application, role, policy.
- Identity Governance squad reports under Information Security (SEC).
- Control owners: wires, finance, cloud, core, IAM.
- Risk language: birthright, requestable, privileged, break-glass, SoD.
- Populations = reusable saved searches, not one-off filters.
- Entitlement risk tiers: medium, high, critical — drives certification priority.
- NIST SP 800-53 AC-2 / AC-5, FFIEC, SOX — examiner expectations.
- Personas: helen.ross, priya.wire, jordan.reed.

**Do-not-repeat seeds:**
- Identity cube definition and XML-backed structure (covered in Lesson 01).
- Four IIQ surfaces: Identities, Applications, Tasks, Work Items (Lesson 01).
- Detailed job-code to entitlement mapping mechanics (Lesson 02).
- Full SoD matrix and toxic pair examples beyond wire dual control (Lesson 02).
- Lab URL and spadmin credentials (Lesson 01).
- Debug page and navigation click-paths (Lesson 01).

### E02 — The Language of Access — Identity, Account, Entitlement
**Must-cover:**
- (none extracted)

**Do-not-repeat seeds:**
- (none)

### E03 — HR as Source of Truth — Authoritative Identity
**Must-cover:**
- Authoritative source definition and why HRIS wins at Meridian  
- employeeId as the stable correlation key between HR and IT systems  
- The difference between identity cubes (people) and links (accounts)  
- What makes an account an orphan and why that’s a control failure  
- Three dispositions for uncorrelated accounts: correlate, disable, accept with ticket  
- FFIEC and NIST expectations for authoritative identity sources  
- Why display name matching is an anti‑pattern  
- The create‑identities flag belongs on the authoritative app, not target apps

**Do-not-repeat seeds:**
- Detailed lab instructions for creating Delimited File applications  
- Click-paths for Account Aggregation tasks or Identity Refresh jobs  
- File paths like `/opt/iiq-lab-data/HRApplications.txt` or Docker volume locations  
- Menu navigation in IdentityIQ interface  
- Specific role names like MNB-On-Leave or population rules  
- Termination vs leave-of-absence flag distinctions (covered in attribute design lesson)  
- Manager correlation via managersAssociateID (covered in attribute design lesson)

### E09 — SailPoint IdentityIQ Essentials — What the Platform Actually Does
**Must-cover:**
- Identity cube definition and purpose (Helen Ross example)  
- Aggregation vs. Refresh (attribute and manager) – separate tasks, ordered pipeline  
- Task vs. Work Item – automated job vs. human approval record  
- Nightly pipeline order: HR aggregation → purpose-built refreshes → role/policy certifications  
- Task Results literacy (counts, failures, persona spot-checks)  
- Meridian personas (helen.ross, priya.wire) and their cube states  
- Audit evidence: documented job sequence, schedules, and failure handling

**Do-not-repeat seeds:**
- Detailed “mega refresh” configuration steps (already covered in Lesson 06)  
- Exact UI navigation of Identity, Applications, Tasks, Work Items (Lesson 01) – only concept, not click-path  
- Re-explaining the six core constructs (identity, account, entitlement, etc.) – already introduced in Lesson 01  
- Re-telling the Helen Ross vs. Priya Wire story without linking to aggregation/refresh sequencing – keep the narrative focused on the mental model, not the UI screenshots.

