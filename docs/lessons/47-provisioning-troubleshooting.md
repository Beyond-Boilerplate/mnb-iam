# Lesson 47 — Provisioning Plans & Troubleshooting

**Level:** Advanced  
**Track:** Ops  
**Time:** 90  
**Prereq:** Lesson 46 — Certification Remediation & Evidence  

**Lab data:** `apps/MNB-*.csv` file connector paths; any IdentityRequest from cert revoke or LCM request

---

## Learning objectives

You will be able to:

- Locate a **provisioning plan** from an IdentityRequest, certification remediation, or refresh
- Interpret plan operations (create / modify / delete / disable) and AttributeRequests
- Induce a **safe lab failure** by pointing a file connector at a bad path, then observe the error
- Restore the path, retry, and confirm success
- Write a five-step Meridian debug playbook for “nothing happened”

---

## Why this matters

Approvals and cert revokes without provisioning are theater. Banking examiners will ask for proof that access was removed on the target—not only that someone clicked Revoke.

File-based lab connectors “provision” by writing or updating files. Beginners often stare at the UI while the failure lives in Task Results and connector paths. This lesson makes that chain visible.

---

## Concepts

A **provisioning plan** is IIQ’s structured list of account/entitlement changes to execute against applications.

| Plan element | Meaning |
| --- | --- |
| Application | Target app (`MNB-AWS-Cloud`, etc.) |
| NativeIdentity | Account identifier on the app |
| Operation | Create, Modify, Disable, Delete, Unlock… |
| AttributeRequest | Entitlement/attribute add or remove |

```
Trigger (LCM / cert revoke / leaver)
        │
        ▼
 IdentityRequest / Workflow
        │
        ▼
 Provisioning plan compiled
        │
        ▼
 Provisioner / connector
        │
        ├── Success → aggregate → cube matches
        └── Failure → Task Result / logs → fix → retry
```

**Meridian debug playbook (memorize):**

1. Request / cert decision  
2. Plan contents  
3. Task Result status & error  
4. Application connector config / logs / file path  
5. Fix → retry → re-aggregate → verify cube  

---

## Before you start

- [ ] IIQ up; `spadmin` access to Debug and Task Results
- [ ] Know where file connector data sources live (`~/iiq-lab-data/apps/...`)
- [ ] One open IdentityRequest or cert remediation available (create a tiny entitlement remove if needed)
- [ ] Lab only: you may briefly break a path—restore before leaving the session

---

## Lab procedure

### Task 1 — Find a provisioning plan

1. Open an **IdentityRequest** (from access request, leaver, or cert revoke).
2. Navigate to provisioning details / plan view (or Debug → IdentityRequest XML).
3. Alternatively open the related **ProvisioningRequest** / project object if shown in your version.
4. Note Request ID for binder.

**Expected result:** You can open raw plan structure for one real Meridian change.

**If it fails:** Trigger a simple LCM remove of a medium-risk entitlement on a test identity, then reopen.

### Task 2 — Read the plan

1. Identify Application name(s).
2. Identify NativeIdentity.
3. List AttributeRequests: which entitlement removed/added?
4. Confirm Operation matches intent (Modify/Remove vs Disable account).
5. Write a one-sentence plain-English translation: “Remove AWS_ADMIN from jordan.reed on MNB-AWS-Cloud.”

**Expected result:** Annotated plan notes in binder (screenshot + translation).

### Task 3 — Induce a safe failure (bad path)

1. Open Application `MNB-AWS-Cloud` (or another file connector you can restore quickly).
2. Note the current data file path.
3. Change path to a **non-existent** file (e.g., `/tmp/mnb-does-not-exist.csv`)—lab only.
4. Save. Trigger provisioning (retry failed request, or run a small entitlement change).
5. Open **Task Results** / provisioning result; capture the error message.

**Expected result:** Clear failure in Task Result referencing file/path/IO error—not a silent UI success.

**If it fails:** If connector caches path, restart not required usually—re-save app and retry; ensure you actually executed provisioner.

### Task 4 — Fix and retry

1. Restore the correct path to `~/iiq-lab-data/apps/MNB-AWS-Cloud.csv` (or the app’s real file).
2. Save Application.
3. Retry the IdentityRequest / provisioning.
4. Confirm Task Result = Success.
5. Run **Account Aggregation** for the app; verify identity cube matches intended end state.

**Expected result:** Success result + cube proof. Bad path fully reverted.

### Task 5 — Write the debug playbook card

Create a one-page playbook titled `MNB-Provisioning-Debug-Playbook` with the five steps from Concepts, plus:

- First place to look: Task Results  
- File apps: verify path + write permissions  
- Never debug only from Work Item status  
- Escalate to app owner if target system rejects change  

**Expected result:** Playbook card printable for ops wall / Capstone.

---

## Acceptance criteria

- [ ] Plan located and interpreted in plain English
- [ ] Safe bad-path failure captured in Task Result
- [ ] Path restored; retry succeeded; cube verified
- [ ] Five-step playbook written
- [ ] No lab apps left pointed at bad paths

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| UI says complete, target unchanged | Plan never executed / wrong app | Inspect plan Application; check Task Result |
| File not updated | Path wrong / permissions | Fix path; check OS write rights |
| Intermittent failures | File locked by editor | Close CSV in editors; retry |
| Retry no-ops | Request already closed | Clone/reopen or new LCM request |
| Disable vs entitlement remove confusion | Wrong Operation | Align plan Operation to desired outcome |

---

## Training binder evidence

- Annotated plan screenshot  
- Failed Task Result (bad path)  
- Successful Task Result after fix  
- Playbook one-pager  
- Confirmation no bad paths remain (app config screenshot)

---

## Knowledge check

1. What is a provisioning plan?
2. Where do you look first on failure?
3. Why do file apps confuse beginners?
4. List the five playbook steps in order.
5. After a successful provision, what verification step remains?

### Answers

1. Structured list of account/entitlement changes IIQ will execute on target apps.  
2. Task Results (and the plan itself)—not only the Work Item label.  
3. “Provisioning” may only write files; path/permission errors look like IAM bugs.  
4. Request → plan → Task Result → app/logs/path → fix/retry/verify.  
5. Aggregate (as needed) and confirm the identity cube / target matches intent.

---

## Stretch lab

Temporarily raise connector/provisioning log verbosity in lab; capture a redacted snippet showing the AttributeRequest. Revert logging afterward.

---

## Summary

- Plans make change intent explicit; Task Results make outcomes explicit.
- Break-fix drills teach real failure modes safely.
- Meridian ops use a fixed five-step playbook—not random UI clicking.

---

**Previous:** [Lesson 46 — Certification Remediation & Evidence](46-cert-remediation-evidence.md)  
**Next:** [Lesson 48 — Audit-Ready Reporting](48-audit-ready-reporting.md)
