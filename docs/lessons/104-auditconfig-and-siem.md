# Lesson 104 — AuditConfig & SIEM

**Level:** Intermediate  
**Track:** Enterprise Hardening & Mastery  
**Time:** 60–90 min  
**Prereq:** Lesson 103 — UI Customization & Branding; Lesson 48 reporting awareness  

**Lab data:**
- AuditConfig via Debug
- Assurance pack naming from Lesson 48
- API account from Lesson 100 (`mnb.api.lab`)

---

## Learning objectives

You will be able to:

- Open and interpret **AuditConfig** action enablement in IdentityIQ
- Enable Meridian-critical audit actions (login, provisioning, capability changes, imports)
- Generate sample audit events and locate them in Advanced Analytics / Audit search
- Design a SIEM feed contract (fields, retention, owners) for Meridian SOC
- Tie audit evidence to examiner questions on privileged activity
- Schedule a privileged weekly extract aligned to Lesson 48 assurance naming

---

## Why this matters

**Business.** If AuditConfig leaves provisioning or admin changes off, your certifications and SoD reports cannot explain *who changed what*. When `helen.ross` investigates a Wire entitlement grant, silent IAM is a dead end. SIEM without IIQ events creates a blind spot around the IAM control plane itself — exactly where insider risk concentrates.

**Control / audit.** Banking examiners expect privileged IAM actions to be immutable, time-synced, and reviewable. AuditConfig is the switchboard; SIEM is long-term detection and retention. When the OCC asks *"show the last capability change and the last failed API authentication,"* you answer with Audit search + SIEM retention — not “we think logging is on.”

---

## Concepts

### Core terms

| Term | Meaning |
| --- | --- |
| **AuditConfig** | IIQ object controlling which actions emit audit events |
| **AuditEvent** | Recorded action with actor, source, target, attributes |
| **SIEM feed** | Forwarded events (syslog/CEF/API) to Splunk/QRadar/etc. |

### Meridian minimum enable set (lab)

| Action category | Why |
| --- | --- |
| Authentication success/failure | API & admin monitoring (`spadmin`, `mnb.api.*`) |
| Provisioning | Joiner/mover/leaver evidence |
| Capability / workgroup changes | Privileged IAM drift |
| Import / console-sensitive ops | Change tracking (Lesson 99/101) |
| Certification decisions | Exam support (as available in your version) |

**Retention:** Hot in IIQ DB per ops policy; cold in SIEM ≥ exam cycle (often 1–3+ years — follow bank records schedule).

### Event quality standard

Every privileged event should answer: Who? What? When (UTC)? Against which identity/app? Success or fail? From which host/API account?

If fields are empty, fix configuration before promising SIEM value.

### Real-life Meridian example

A contractor API account `mnb.api.lab` was brute-forced overnight. Nobody noticed because failed authentication actions were disabled in AuditConfig. Enabling auth failure + SIEM rule would have paged SOC. This lesson turns that switchboard on deliberately.

### Wrong way vs Meridian way

| Wrong way | Why it fails | Meridian way |
| --- | --- | --- |
| Enable everything | DB flood; no SIEM capacity | Critical set first; tune noise |
| SIEM without field contract | Useless detections | Written field list + RACI |
| Trust IIQ DB alone for years | Tablespace / purge risk | SIEM cold retention |
| Skip capability-change audit | Silent privilege drift | Mandatory for admin hardening (109) |

---

## How it works

```
  Operator / API / Task
        │
        ▼
  IIQ action (provision, login, import, capability grant)
        │
        ▼
  AuditConfig enabled? --no--> silent (BAD for critical actions)
        │
       yes
        ▼
  AuditEvent store --> Analytics / export --> SIEM / SOC
        │
        ▼
  Weekly privileged extract --> helen.ross (+ Risk CC)
```

| Role | Owns | Lesson tie |
| --- | --- | --- |
| IIQ admin / IAM | AuditConfig enablement + event quality | 104 |
| SOC | Detection rules / alerting | SIEM contract |
| IAM | Response playbooks | 109 break-glass |
| Platform | Clock sync (NTP) across nodes | 105 |

Custom service action `MNB_SOD_WATCH_RUN` (Lesson 102) should be mapped into AuditConfig / logging design where supported.

---

## Real-world setup (audit as examiner evidence)

### Step 1 — Baseline before hardening

1. Export AuditConfig dated baseline.
2. Diff later; never “flip switches” without artifacts.

### Step 2 — Enable critical set

1. Auth, provisioning, capability/workgroup, import/console.
2. Note noisy actions deferred until SIEM capacity exists.

### Step 3 — Prove with generated events

1. Login, provision/update, capability/workgroup tweak, failed API auth.
2. Search and export samples.

### Step 4 — SIEM contract + weekly assurance

1. Field list, transport, RACI, retention.
2. Mock drop in lab; weekly privileged extract naming from Lesson 48.

---

## Before you start

- [ ] `spadmin` access to Debug
- [ ] Know SOC contact / lab SIEM proxy (even if “file export mock”)
- [ ] API identity `mnb.api.lab` exists (Lesson 100) for failure test
- [ ] Clock sync awareness (NTP) noted for multi-host later (Lesson 105)
- [ ] Binder: `audit/`

---

## Lab procedure

### Task 1 — Export AuditConfig baseline

You need a before state for change control.

1. Debug → select **AuditConfig** (or Configuration named AuditConfig).
2. Export/view XML or UI editor of enabled actions.
3. Save baseline as `~/iiq-lab-data/audit/MNB-AuditConfig-baseline-YYYY-MM-DD.xml`.

**Expected result:** Dated baseline file before changes.

**If it fails:** Screenshot the audit configuration UI checklist instead.

### Task 2 — Enable Meridian-critical actions

1. Enable missing actions from the minimum set above (lab-safe).
2. Avoid enabling ultra-noisy actions that flood DB without SIEM capacity — note tradeoffs in binder.
3. Save AuditConfig.
4. Export post-change copy `MNB-AuditConfig-hardened-YYYY-MM-DD.xml`.

**Expected result:** Diffable before/after AuditConfig artifacts.

**If it fails:** Enable at least login + provisioning; document residual gaps as risks (`RR-AUDIT-*`).

### Task 3 — Generate events

1. Log out/in as `helen.ross`.
2. Perform a low-risk provisioning or identity attribute update on a lab persona (or run a small refresh).
3. As `spadmin`, grant/revoke a non-prod capability on a test identity (or add comment to workgroup membership).
4. Attempt failed login with wrong password for `mnb.api.lab` (do not lock shared accounts repeatedly).

**Expected result:** Four intentional event categories generated.

### Task 4 — Search audit

1. Open Advanced Analytics → Audit / Audit Search (or equivalent).
2. Filter on recent time window; find your login and change events.
3. Export results as `MNB-Audit-Sample-YYYY-MM-DD`.
4. Confirm actor, timestamp, action, target identity/application fields populated.

**Expected result:** Sample extract proving enablement works.

**If it fails:** Wait for indexing; verify AuditConfig save; check DB connectivity.

### Task 5 — SIEM contract (design)

1. Draft fields Meridian SOC needs: timestamp (UTC), actor, src_ip if available, action, target, app, result, correlationId/requestId.
2. Transport options: syslog CEF, flat file pickup, API pull — pick one for lab mock.
3. RACI: IIQ admin enables AuditConfig; SOC owns detection rules; IAM owns response playbooks.
4. Create mock forward: copy sample export into `~/iiq-lab-data/audit/siem-drop/`.

**Expected result:** SIEM contract page + mock drop file.

### Task 6 — Examiner Q&A card

1. Write answers:
   - “Show last capability change.”
   - “Show failed API authentications.”
   - “Show provisioning for `jordan.reed` leaver window.”
2. Point each to Audit search + SIEM retention.

**Expected result:** Three Q&A cards in binder.

### Task 7 — Weekly audit assurance extract

1. Schedule or manually produce `MNB-Audit-Priv-YYYY-MM-DD` filtered to capability changes + spadmin logins + imports.
2. Send to IAM lead inbox pattern (`helen.ross@meridiannb.com`) with Risk CC.
3. Tie filename to Lesson 48 assurance pack naming.

**Expected result:** One privileged audit extract in assurance folder.

### Task 8 — Correlation with certifications + custom services

1. If AuditConfig lacks cert actions in your version, compensate with certification reports + Task Results and document residual (`RR-AUDIT-CERT-01` for Lesson 110).
2. Map `MNB_SOD_WATCH_RUN` (Lesson 102) into enablement/logging design.

**Expected result:** Residual note + custom action mapping.

---

## Acceptance criteria

- [ ] Baseline + hardened AuditConfig saved
- [ ] Critical actions enabled (or gaps risk-accepted)
- [ ] Sample audit extract produced
- [ ] Failed auth or privileged change visible in search
- [ ] SIEM contract drafted with RACI
- [ ] Examiner Q&A cards written
- [ ] Weekly privileged extract produced or scheduled
- [ ] Cert/custom-action residual noted if needed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No events | Action disabled | Re-check AuditConfig |
| Events delayed | Async flush | Widen time window |
| DB growth | Over-enabled noise | Tune actions; archive/SIEM offload |
| Missing actor | Service account context | Ensure auth context on API calls |
| SIEM gaps | Clock skew | NTP; Lesson 105 multi-host |
| Empty required fields | Poor event quality | Fix config before SOC onboarding |

---

## Training binder evidence

- Baseline + hardened AuditConfig
- Audit sample extract
- SIEM contract + mock drop
- Examiner Q&A cards
- Privileged weekly extract
- Residual risk notes (cert/custom) if any

---

## Knowledge check

1. What does AuditConfig control?
2. Name three Meridian-critical audit categories.
3. Who owns detection rules vs AuditConfig enablement?
4. Why mock a SIEM drop in lab?
5. Why are capability-change audits mandatory?
6. What six questions should every privileged event answer?

### Answers

1. Which IIQ actions emit audit events.
2. Auth, provisioning, capability/workgroup changes (plus import/cert as applicable).
3. SOC owns detections; IAM/IIQ admin owns enablement and quality of events.
4. Proves pipeline shape before real connectors exist.
5. Privileged IAM drift is a top exam and insider-risk control.
6. Who, what, when (UTC), target identity/app, success/fail, host/API account.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “AuditConfig” and “audit search” for action catalogs and retention notes.
- [SailPoint Community / Compass](https://community.sailpoint.com/) — search “AuditConfig best practices” for noisy-action tuning.
- [NIST SP 800-53 Rev. 5 — AU family](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — audit and accountability controls (AU-2, AU-3, AU-6, AU-12).
- [NIST SP 800-92 — Guide to Computer Security Log Management](https://csrc.nist.gov/publications/detail/sp/800-92/final) — log management, retention, and SIEM-oriented practices.
- [FFIEC IT Handbook — Information Security](https://ithandbook.ffiec.gov/) — logging and monitoring expectations for banking institutions.

---

## Stretch lab

Map custom service action `MNB_SOD_WATCH_RUN` (Lesson 102) into AuditConfig / logging design end-to-end, including a sample log line with `correlationId` and no PII. Draft the SOC detection: “SoD watch WARN above threshold.”

---

## Summary

- Turn on the audits that prove privileged IAM activity — AuthConfig is a switchboard, not a default.
- Prove with searches; forward with a written SIEM contract and RACI.
- Retain to bank policy — not “until tablespace fills.”

---

**Previous:** [Lesson 103 — UI Customization & Branding](103-ui-customization-branding.md)  
**Next:** [Lesson 105 — Partitioning & Task Servers](105-partitioning-task-servers.md)
