# Lesson 104 — AuditConfig & SIEM

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Enterprise Hardening & Mastery |
| **Time** | 60–90 minutes |
| **Prereq** | [Lesson 103 — UI Customization & Branding](103-ui-customization-branding.md); Lesson 48 reporting awareness |
| **Lab data** | AuditConfig via Debug; assurance pack naming from Lesson 48; API account from Lesson 100 |

## Learning objectives

You will be able to:

- Open and interpret **AuditConfig** action enablement in IdentityIQ
- Enable Meridian-critical audit actions (login, provisioning, capability changes, imports)
- Generate sample audit events and locate them in Advanced Analytics / Audit search
- Design a SIEM feed contract (fields, retention, owners) for Meridian SOC
- Tie audit evidence to examiner questions on privileged activity

## Why this matters

If AuditConfig leaves provisioning or admin changes off, your certifications and SoD reports cannot explain *who changed what*. SIEM without IIQ events creates a blind spot around the IAM control plane itself.

**Control / audit:** Banking examiners expect privileged IAM actions to be immutable, time-synced, and reviewable. AuditConfig is the switchboard; SIEM is long-term detection.

## Concepts

| Term | Meaning |
| --- | --- |
| **AuditConfig** | IIQ object controlling which actions emit audit events |
| **AuditEvent** | Recorded action with actor, source, target, attributes |
| **SIEM feed** | Forwarded events (syslog/CEF/API) to Splunk/QRadar/etc. |

```text
  Operator / API / Task
        |
        v
  IIQ action (provision, login, import, capability grant)
        |
        v
  AuditConfig enabled? --no--> silent (BAD for critical actions)
        |
       yes
        v
  AuditEvent store --> Analytics / export --> SIEM / SOC
```

**Meridian minimum enable set (lab)**

| Action category | Why |
| --- | --- |
| Authentication success/failure | API & admin monitoring |
| Provisioning | Joiner/mover/leaver evidence |
| Capability / workgroup changes | Privileged IAM drift |
| Import / console-sensitive ops | Change tracking |
| Certification decisions | Exam support (as available) |

**Retention:** Hot in IIQ DB per ops policy; cold in SIEM ≥ exam cycle (often 1–3+ years—follow bank records schedule).

## Before you start

- [ ] `spadmin` access to Debug
- [ ] Know SOC contact / lab SIEM proxy (even if “file export mock”)
- [ ] API identity `mnb.api.lab` exists (Lesson 100) for failure test
- [ ] Clock sync awareness (NTP) noted for multi-host later (Lesson 105)

## Lab procedure

### Task 1 — Export AuditConfig baseline

1. Debug → select **AuditConfig** (or Configuration named AuditConfig).
2. Export/view XML or UI editor of enabled actions.
3. Save baseline as `~/iiq-lab-data/audit/MNB-AuditConfig-baseline-YYYY-MM-DD.xml`.

**Expected result:** Dated baseline file before changes.

**If it fails:** Screenshot the audit configuration UI checklist instead.

### Task 2 — Enable Meridian-critical actions

1. Enable missing actions from the minimum set above (lab-safe).
2. Avoid enabling ultra-noisy actions that flood DB without SIEM capacity—note tradeoffs.
3. Save AuditConfig.
4. Export post-change copy `MNB-AuditConfig-hardened-YYYY-MM-DD.xml`.

**Expected result:** Diffable before/after AuditConfig artifacts.

**If it fails:** Enable at least login + provisioning; document residual gaps as risks.

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
2. Transport options: syslog CEF, flat file pickup, API pull—pick one for lab mock.
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

## Acceptance criteria

- [ ] Baseline + hardened AuditConfig saved
- [ ] Critical actions enabled (or gaps risk-accepted)
- [ ] Sample audit extract produced
- [ ] Failed auth or privileged change visible in search
- [ ] SIEM contract drafted with RACI
- [ ] Examiner Q&A cards written

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No events | Action disabled | Re-check AuditConfig |
| Events delayed | Async flush | Widen time window |
| DB growth | Over-enabled noise | Tune actions; archive/SIEM offload |
| Missing actor | Service account context | Ensure auth context on API calls |
| SIEM gaps | Clock skew | NTP; Lesson 105 multi-host |

## Training binder evidence

- Baseline + hardened AuditConfig  
- Audit sample extract  
- SIEM contract  
- Examiner Q&A cards  

## Knowledge check

1. What does AuditConfig control?
2. Name three Meridian-critical audit categories.
3. Who owns detection rules vs AuditConfig enablement?
4. Why mock a SIEM drop in lab?
5. Why are capability-change audits mandatory?

### Answers

1. Which IIQ actions emit audit events.  
2. Auth, provisioning, capability/workgroup changes (plus import/cert as applicable).  
3. SOC owns detections; IAM/IIQ admin owns enablement and quality of events.  
4. Proves pipeline shape before real connectors exist.  
5. Privileged IAM drift is a top exam and insider-risk control.

## Stretch lab

Map custom service action `MNB_SOD_WATCH_RUN` (Lesson 102) into AuditConfig / logging design.

## Summary

- Turn on the audits that prove privileged IAM activity.
- Prove with searches; forward with a written SIEM contract.
- Retain to bank policy—not “until tablespace fills.”

## Event quality standards

Every privileged event should answer: Who? What? When (UTC)? Against which identity/app? Success or fail? From which host/API account?

If fields are empty, fix configuration before promising SIEM value.

### Task 7 — Weekly audit assurance extract

1. Schedule or manually produce `MNB-Audit-Priv-YYYY-MM-DD` filtered to capability changes + spadmin logins + imports.
2. Send to IAM lead inbox pattern (`helen.ross@meridiannb.com`) with Risk CC.
3. Tie filename to Lesson 48 assurance pack naming.

**Expected result:** One privileged audit extract in assurance folder.

### Correlation with certifications

Cert decisions and remediations should be auditable. If AuditConfig lacks cert actions in your version, compensate with certification reports + Task Results and document the residual (RR-ID for Lesson 110).

---

**Previous:** [Lesson 103 — UI Customization & Branding](103-ui-customization-branding.md)  
**Next:** [Lesson 105 — Partitioning & Task Servers](105-partitioning-task-servers.md)
