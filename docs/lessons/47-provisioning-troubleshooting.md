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
- Verify post-provision state with Account Aggregation and cube proof

---

## Why this matters

**Business.** Approvals and cert revokes without provisioning are theater. When a certifier revokes `AWS_ADMIN` from `jordan.reed` or removes residual `WIRE_INIT` from a mover, Meridian must prove the target changed — not only that someone clicked Revoke.

**Control / audit.** Banking examiners will ask for proof that access was removed on the target. File-based lab connectors “provision” by writing or updating files. Beginners often stare at the UI while the failure lives in Task Results and connector paths. This lesson makes that chain visible. Control owner: IAM Ops; escalate to app owners when the target system rejects the change.

---

## Concepts

### What a provisioning plan is

A **provisioning plan** is IIQ’s structured list of account/entitlement changes to execute against applications. It is compiled from LCM requests, certification remediations, leaver workflows, and similar triggers.

| Plan element | Meaning | Meridian example |
| --- | --- | --- |
| Application | Target app | `MNB-AWS-Cloud` |
| NativeIdentity | Account identifier on the app | Jordan’s AWS account key |
| Operation | Create, Modify, Disable, Delete, Unlock… | Modify / Remove entitlement |
| AttributeRequest | Entitlement/attribute add or remove | Remove `AWS_ADMIN` |

### Why file connectors confuse beginners

In this Part I lab, many apps are Delimited File. “Provisioning success” may mean “file updated” — and failure often means path typo, file locked in Excel, or permissions. The UI Work Item can say Complete while Task Results show IO errors. Always read Task Results.

The wrong way: debug only from Work Item status labels. That hides connector failures forever.

### Meridian example — cert revoke stalls on AWS

Lesson 46 traced a revoke of `AWS_ADMIN` from `jordan.reed`. The IdentityRequest looks “done,” but Task Results show `FileNotFoundException` because `MNB-AWS-Cloud` pointed at `/tmp/mnb-does-not-exist.csv` after a botched edit. Fixing the path and retrying is the control — not re-clicking Revoke in the certification UI.

Same playbook applies to residual `WIRE_INIT` removals after Priya’s mover (Lesson 30) and emergency disables that write delimited Wire Portal files (Lesson 34).

---

## How it works

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

| Playbook step | Where to look | Question you answer |
| --- | --- | --- |
| 1. Request / cert decision | Work Item / IdentityRequest | What was intended? |
| 2. Plan contents | Plan / Debug XML | Which app, native ID, AttributeRequest? |
| 3. Task Result | Tasks → Results | Success or error text? |
| 4. Connector / path / logs | Application config | File path valid? Write allowed? |
| 5. Fix → retry → verify | Re-run + Account Aggregation | Cube matches intent? |

Memorize as `MNB-Provisioning-Debug-Playbook`. First place to look on failure: **Task Results**.

| Common failure | Where it shows | First fix |
| --- | --- | --- |
| Bad file path | Task Result IO/path error | Restore `~/iiq-lab-data/apps/...` path |
| CSV open in Excel | Intermittent write fail | Close editor; retry |
| Wrong Operation | Plan succeeded, wrong outcome | Align Disable vs entitlement Remove |
| Request already closed | Retry no-ops | New LCM request or reopen |
| Aggregation skipped | Cube still shows old ents | Run Account Aggregation; re-check cube |

---

## Before you start

- [ ] IIQ up; `spadmin` access to Debug and Task Results
- [ ] Know where file connector data sources live (`~/iiq-lab-data/apps/...`)
- [ ] One open IdentityRequest or cert remediation available (create a tiny entitlement remove if needed)
- [ ] Lab only: you may briefly break a path — restore before leaving the session
- [ ] Prefer practicing on `MNB-AWS-Cloud` or Wire Portal files you can restore from `lab-data/apps/`
- [ ] Screenshot current Application file path *before* inducing failure (restore insurance)

---

## Lab procedure

### Task 1 — Find a provisioning plan

You cannot troubleshoot what you cannot open. Locate one real Meridian change first — ideally the cert revoke you traced in Lesson 46.

1. Open an **IdentityRequest** (from access request, leaver, or cert revoke).
2. Navigate to provisioning details / plan view (or Debug → IdentityRequest XML).
3. Alternatively open the related **ProvisioningRequest** / project object if shown in your version.
4. Note Request ID for binder.
5. Confirm the plan’s Application is one you expect (do not debug the wrong connector).

**Expected result:** You can open raw plan structure for one real Meridian change.

**If it fails:** Trigger a simple LCM remove of a medium-risk entitlement on a test identity, then reopen.

### Task 2 — Read the plan

Translate the plan into one plain-English sentence. If you cannot, you do not understand the change yet.

1. Identify Application name(s).
2. Identify NativeIdentity.
3. List AttributeRequests: which entitlement removed/added?
4. Confirm Operation matches intent (Modify/Remove vs Disable account).
5. Write a one-sentence plain-English translation: “Remove AWS_ADMIN from jordan.reed on MNB-AWS-Cloud.”
6. Note whether this plan came from cert remediation, LCM request, or leaver — the trigger changes who you escalate to.

**Expected result:** Annotated plan notes in binder (screenshot + translation + trigger type).

### Task 3 — Induce a safe failure (bad path)

Break-fix drills teach failure modes examiners will ask about. Restore before you leave.

1. Open Application `MNB-AWS-Cloud` (or another file connector you can restore quickly).
2. Note the current data file path.
3. Change path to a **non-existent** file (e.g., `/tmp/mnb-does-not-exist.csv`) — lab only.
4. Save. Trigger provisioning (retry failed request, or run a small entitlement change).
5. Open **Task Results** / provisioning result; capture the error message.

**Expected result:** Clear failure in Task Result referencing file/path/IO error — not a silent UI success.

**If it fails:** If connector caches path, restart not required usually — re-save app and retry; ensure you actually executed provisioner.

### Task 4 — Fix and retry

Success without cube verification is incomplete. Aggregate and confirm.

1. Restore the correct path to `~/iiq-lab-data/apps/MNB-AWS-Cloud.csv` (or the app’s real file).
2. Save Application.
3. Retry the IdentityRequest / provisioning.
4. Confirm Task Result = Success.
5. Run **Account Aggregation** for the app; verify identity cube matches intended end state.

**Expected result:** Success result + cube proof. Bad path fully reverted.

### Task 5 — Write the debug playbook card

Ops walls need a one-pager, not a novel.

Create a one-page playbook titled `MNB-Provisioning-Debug-Playbook` with the five steps from How it works, plus:

- First place to look: Task Results  
- File apps: verify path + write permissions  
- Never debug only from Work Item status  
- Escalate to app owner if target system rejects change  

**Expected result:** Playbook card printable for ops wall / Capstone.

### Task 6 — Examiner proof drill

> “Show me that the revoke from last quarter’s certification actually removed access on the target.”

Answer with three artifacts: (1) cert decision / IdentityRequest ID, (2) successful Task Result after fix, (3) post-aggregation cube (or file row) without the entitlement.

**Expected result:** Written three-artifact answer in the binder next to the playbook.

---

## Acceptance criteria

- [ ] Plan located and interpreted in plain English
- [ ] Safe bad-path failure captured in Task Result
- [ ] Path restored; retry succeeded; cube verified
- [ ] Five-step playbook written
- [ ] No lab apps left pointed at bad paths
- [ ] Examiner three-artifact proof written

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| UI says complete, target unchanged | Plan never executed / wrong app | Inspect plan Application; check Task Result |
| File not updated | Path wrong / permissions | Fix path; check OS write rights |
| Intermittent failures | File locked by editor | Close CSV in editors; retry |
| Retry no-ops | Request already closed | Clone/reopen or new LCM request |
| Disable vs entitlement remove confusion | Wrong Operation | Align plan Operation to desired outcome |
| Shared lab left on bad path | Forgot Task 4 restore | Re-point all `MNB-*` file apps; re-test connection/agg |

---

## Training binder evidence

- Annotated plan screenshot  
- Failed Task Result (bad path)  
- Successful Task Result after fix  
- Playbook one-pager  
- Confirmation no bad paths remain (app config screenshot)
- Examiner three-artifact proof note (request → Task Result → cube)

---

## Knowledge check

1. What is a provisioning plan?
2. Where do you look first on failure?
3. Why do file apps confuse beginners?
4. List the five playbook steps in order.
5. After a successful provision, what verification step remains?
6. Why is Work Item “Complete” alone insufficient evidence?

### Answers

1. Structured list of account/entitlement changes IIQ will execute on target apps.
2. Task Results (and the plan itself) — not only the Work Item label.
3. “Provisioning” may only write files; path/permission errors look like IAM bugs.
4. Request → plan → Task Result → app/logs/path → fix/retry/verify.
5. Aggregate (as needed) and confirm the identity cube / target matches intent.
6. The connector may have failed after the workflow labeled the request complete — Task Results tell the truth.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “provisioning plan” and “provisioning troubleshooting.”
- [SailPoint Community](https://community.sailpoint.com/) — search “provisioning failure task result” for connector path and retry patterns.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — real-world plan/AttributeRequest debugging threads.
- [NIST SP 800-53 AU / SI families](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) — auditability of changes and system integrity when remediations fail.
- [FFIEC Information Technology Examination Handbook](https://ithandbook.ffiec.gov/) — search change management / access administration for proof-of-removal expectations.

---

## Stretch lab

Temporarily raise connector/provisioning log verbosity in lab; capture a redacted snippet showing the AttributeRequest. Revert logging afterward. Optional: walk the same five-step playbook on a Wire Portal residual `WIRE_INIT` remove after Priya’s mover — proves the playbook is app-agnostic.

---

## Summary

- Plans make change intent explicit; Task Results make outcomes explicit.
- Break-fix drills teach real failure modes safely.
- Meridian ops use a fixed five-step playbook — not random UI clicking.
- Examiner proof is three artifacts: decision/request, Task Result, post-aggregate cube.

---

**Previous:** [Lesson 46 — Certification Remediation & Evidence](46-cert-remediation-evidence.md)  
**Next:** [Lesson 48 — Audit-Ready Reporting](48-audit-ready-reporting.md)
