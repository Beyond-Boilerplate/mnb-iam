# Lesson 76 — AWS IAM Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 75 — M365 & SharePoint Online; Lesson 13 (`MNB-AWS-Cloud` CSV onboard) for contrast  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (AWS IAM row)
- Repo: `lab-data/apps/MNB-AWS-Cloud.csv` (legacy file extract for contrast)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Explain the AWS IAM object model (users, groups, policies, roles, access keys) and which of them are governable entitlements
- Distinguish IAM users from federated access via IAM Identity Center (AWS SSO) and know what this connector does and does not see
- Perform the real-world setup: a least-privilege connector principal with a scoped IAM policy, keys or role assumption
- Create **MNB-AWS-IAM** with a defensible entitlement taxonomy and run Account Aggregation
- Design the cloud leaver runbook — including the step everyone forgets: **access keys**
- Upgrade Meridian from the Lesson 13 CSV extract to native aggregation, with a documented retirement plan

---

## Why this matters

**Business.** Meridian's AWS accounts host the internet banking platform and its data lake. In Lesson 13 you governed `AWS_ADMIN` from a quarterly CSV extract. Here is why that is not enough: `jordan.reed` was granted `AdministratorAccess` on a Tuesday for an incident, and the grant was supposed to be temporary. The next CSV extract was 11 weeks away. For 11 weeks, IIQ — and every certification built on it — believed Jordan was a read-only user. File extracts don't drift a little in cloud environments; they drift completely, because cloud access changes hourly.

**Control / audit.** The examiner's cloud questions are precise: *continuous* inventory of privileged cloud identities, evidence of revocation including **credentials** (not just the user record), and an account of federated access. Native aggregation Task Results answer the first two. Knowing your connector's blind spot around IAM Identity Center answers the third — and admitting a blind spot with a residual risk beats being caught unaware.

---

## Concepts

### The AWS IAM object model

| IAM object | What it is | Governance treatment |
| --- | --- | --- |
| **User** | A permanent identity in one AWS account, with console password and/or **access keys** | The account IIQ aggregates |
| **Group** | A bundle of users sharing attached policies | Entitlement (like an AD group) |
| **Managed policy** | A named permission document (`AdministratorAccess`, `ReadOnlyAccess`) attachable to users/groups/roles | Entitlement when attached directly to a user |
| **Inline policy** | A one-off policy embedded in a single user/group | Red flag — ungovernable sprawl; surface and eliminate |
| **Role** | An identity *assumed* temporarily by people, services, or other accounts | Usually out of user-governance scope; the *permission to assume it* is the entitlement |
| **Access key** | Long-lived API credential pair belonging to a user | Not an entitlement — a credential that must die when the user does |

Real-life anchor: when `kai.nguyen` calls `aws s3 cp` from a build script, that's an **access key**. When she clicks around the console, that's her **console password**. Disabling one does nothing to the other. This asymmetry is the root of the most common cloud offboarding failure, and it shapes Task 6.

### Direct policy attachment is the finding, not the norm

Well-run AWS accounts grant permissions through **groups** (or roles). A managed policy attached *directly* to a user bypasses every group-based review. So your entitlement taxonomy treats direct attachments as first-class, high-visibility entitlements — precisely because each one is a candidate finding. When the first native aggregation shows `jordan.reed` with `AdministratorAccess` attached directly (not via `GRP_CLOUD_ADMINS`), that's the value of the connector made visible in one row.

### IAM users vs IAM Identity Center — the blind spot

Modern AWS estates increasingly use **IAM Identity Center** (formerly AWS SSO): people federate from the IdP (Okta, Lesson 73), assume roles via **permission sets**, and have *no IAM user at all*. The classic AWS IAM connector aggregates IAM users — it does **not** see permission-set assignments. Meridian's honest position:

```
Human access to AWS at Meridian
   ├── Legacy IAM users (this lesson)  → MNB-AWS-IAM aggregates them
   ├── Federated via Okta → permission sets → RR-AWS-SSO-01 residual risk
   │                                          (governed partly via OKTA_AWS_POWER group, Lesson 73)
   └── Service/machine users → inventory + key rotation policy, not certification of humans
```

If aggregation shows *fewer* privileged users than you expected, don't celebrate yet — check whether privilege moved to permission sets you can't see.

### One account or many?

IAM is regionless but **per-account**. Meridian has prod, dev, and security accounts; each needs its own application (`MNB-AWS-IAM-Prod`, …) or a cross-account role-assumption design. Lab default: single account, single app, with the multi-account decision documented in Task 7.

---

## How it works

The connector calls the AWS IAM API (a global endpoint) signed with SigV4, as a dedicated connector principal:

```
IdentityIQ (MNB-AWS-IAM)
        │  access key of connector user  — or —  AssumeRole into a connector role
        ▼
AWS IAM API (iam.amazonaws.com)
        ├── ListUsers / GetUser                → accounts
        ├── ListGroups / GetGroup              → group entitlements
        ├── ListAttachedUserPolicies           → direct-attachment entitlements
        ├── ListAccessKeys                     → credential inventory
        └── (provisioning) Add/RemoveUserFromGroup,
            Attach/DetachUserPolicy, DeleteAccessKey, DeleteLoginProfile
```

| Operation | API calls | IIQ behavior |
| --- | --- | --- |
| Account aggregation | `ListUsers` + per-user detail | Account per IAM user, `UserName` native identity |
| Entitlement aggregation | Groups + attached policies | Two entitlement families: `group:` and `policy:` |
| Disable | `DeleteLoginProfile` (console) — keys are separate! | Disable operation (verify what your version actually does) |
| Group revoke | `RemoveUserFromGroup` | Entitlement remove |
| Policy detach | `DetachUserPolicy` | Entitlement remove |

Authentication note: prefer **role assumption** over static access keys for the connector itself where your deployment supports it (IIQ on EC2 can use an instance profile — zero stored secrets). If keys are unavoidable, they live in the vault and rotate ≤90 days. The connector that governs credentials must not itself be a credential-hygiene violation.

---

## Real-world setup (outside IIQ)

### Step 1 — Connector principal

1. In the target AWS account, create IAM user `svc-identityiq` (or better, role `role-identityiq-connector` assumable by your IIQ compute).
2. No console access. If a user: create one access key pair, vault it, set a 90-day rotation reminder.

### Step 2 — Least-privilege connector policy

Attach a customer-managed policy — read-only for phase 1:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "IIQAggregationReadOnly",
    "Effect": "Allow",
    "Action": [
      "iam:ListUsers", "iam:GetUser",
      "iam:ListGroups", "iam:GetGroup", "iam:ListGroupsForUser",
      "iam:ListAttachedUserPolicies", "iam:ListUserPolicies",
      "iam:ListAccessKeys", "iam:GetLoginProfile"
    ],
    "Resource": "*"
  }]
}
```

Phase 2 (provisioning) adds `iam:AddUserToGroup`, `iam:RemoveUserFromGroup`, `iam:AttachUserPolicy`, `iam:DetachUserPolicy`, `iam:DeleteAccessKey`, `iam:DeleteLoginProfile` — each addition security-reviewed, because a writable IAM connector is itself a privileged system.

### Step 3 — Guardrails

1. CloudTrail alarm on the connector principal doing anything *outside* its policy (defense against key theft).
2. Deny-list protection: the connector must never be able to modify its own policy or the break-glass users (`iam:*` on those ARNs explicitly denied).

### Step 4 — Governance records

Document: account ID, principal ARN, policy version, key rotation date, phase 1/2 status, and the security sign-off.

---

## Before you start

- [ ] IIQ up as `spadmin`; `lab-data/apps/MNB-AWS-Cloud.csv` readable for contrast
- [ ] Decide your path: live AWS account (free tier suffices for IAM) or mock fallback
- [ ] Never commit AWS keys — vault or env only; check your shell history habits too
- [ ] Personas: `jordan.reed` (cloud admin), `kai.nguyen` (poweruser), `raj.external` (contractor)

---

## Lab procedure

### Task 1 — Contrast: what the CSV can never tell you

Ground the upgrade in specifics before building it.

1. Open `~/iiq-lab-data/apps/MNB-AWS-Cloud.csv`. List what it contains (userName, one entitlement, status) — then list what it structurally *cannot* contain: direct policy attachments, access-key inventory and age, group-vs-direct grant path, anything newer than the last export.
2. Write the upgrade rationale: native aggregation closes the 11-week Jordan gap and adds credential visibility.
3. Coexistence plan: CSV app stays until two clean native aggregation cycles, then is retired (Task 8).

**Expected result:** Upgrade rationale paragraph + coexistence plan in the binder.

### Task 2 — Create MNB-AWS-IAM

1. Applications → Add New → **AWS** / **AWS IAM** (or equivalent menu path).
2. Connection: account ID, region default, and the Step 1 credential (lab: placeholders noting "key in vault" or the instance-profile/AssumeRole design).
3. Name `MNB-AWS-IAM`; owner `helen.ross`; technical contact `jordan.reed`.
4. Live account: Test Connection — success proves the SigV4 signing chain and the policy's List permissions.

**Expected result:** Application saved; live path shows Test Connection success.

**If it fails:** `AccessDenied` naming a specific action → add exactly that action to the connector policy, nothing broader. `InvalidClientTokenId` → key inactive or wrong account.

### Task 3 — Schema and entitlement taxonomy

1. Account schema: `UserName` (native identity), `Arn`, `CreateDate`, `PasswordLastUsed`, multi-valued `groups` and `attachedPolicies` — **both** as entitlement attributes (two families, per the Concepts section), plus `accessKeyIds`/`accessKeyAge` if your version exposes them.
2. Correlation: IAM has no employeeId, so document the convention that saves you — Meridian tags IAM users with `employeeId` (aggregate tags if supported) and enforces username = HR `userName`. Fallback: `UserName` ↔ identity `userName`.
3. Risk-rate in the entitlement dictionary: `policy:AdministratorAccess` critical / non-requestable; `group:GRP_CLOUD_ADMINS` critical; `group:GRP_POWERUSERS` high; `policy:ReadOnlyAccess` low.
4. **Create identities: OFF** — unknown IAM users must surface as uncorrelated accounts for investigation (Lesson 19), not become people.

**Expected result:** Schema with two entitlement families; risk tiers in the dictionary; create-identities off.

### Task 4 — Mock inventory (fallback: no live account)

1. Create `~/iiq-lab-data/connectors/aws/MNB-AWS-IAM-mock.csv`:

```csv
UserName,Arn,employeeId,groups,attachedPolicies,accessKeyCount,active
jordan.reed,arn:aws:iam::111122223333:user/jordan.reed,MNB00092,GRP_CLOUD_ADMINS,AdministratorAccess,2,true
kai.nguyen,arn:aws:iam::111122223333:user/kai.nguyen,MNB00096,GRP_POWERUSERS,,1,true
raj.external,arn:aws:iam::111122223333:user/raj.external,MNB00093,,ReadOnlyAccess,1,true
svc-databake,arn:aws:iam::111122223333:user/svc-databake,,,AmazonS3FullAccess,1,true
```

2. Shadow-aggregate via DelimitedFile (pipe-split multi-valued columns).
3. Read the seeded findings like an analyst: Jordan has `AdministratorAccess` **directly attached on top of** his admin group (double grant — why?); Jordan has **two access keys** (one is probably forgotten); `svc-databake` has no employeeId (service account — inventory, don't certify as a human).

**Expected result:** Four mock accounts aggregated; three findings written down.

### Task 5 — Account Aggregation

1. Create `MNB-AWS-IAM-Account-Aggregation`; run live or shadow.
2. Compare counts against the legacy CSV app — the delta list (who exists in native but not CSV, and vice versa) is itself evidence of the drift problem.
3. Live path: confirm `PasswordLastUsed` populated — dormancy hunting (Lesson 20) needs it.

**Expected result:** Task Result + a written delta note vs the CSV app.

### Task 6 — The cloud leaver runbook (keys included)

This is the task that separates cloud offboarding from directory offboarding.

1. Storyboard termination of a cloud admin, in order, with reasons:
   1. **Remove from groups / detach direct policies** — permissions gone even if later steps fail.
   2. **Delete login profile** — console access dead.
   3. **Deactivate, then delete, all access keys** — *the step everyone forgets.* A leaver's laptop, CI variables, and dotfiles can hold keys that work forever if you skip this. `ListAccessKeys` before, empty after.
   4. **Re-aggregate** — evidence: no groups, no policies, no keys.
2. Break-glass tie-in (Lesson 37): temporary `GRP_CLOUD_ADMINS` membership must carry an expiry; the aggregation-driven detection of a *non-expiring* break-glass grant is a standing control test.
3. Add the SSO caveat: if the leaver also had Okta-federated access, `OKTA_AWS_POWER` removal (Lesson 73) is a parallel step — one leaver, two rails.

**Expected result:** Four-step leaver card with the access-key step highlighted and the SSO parallel noted.

### Task 7 — Multi-account decision stub

1. Document: Meridian's prod/dev/security accounts each get their own application in production (`MNB-AWS-IAM-Prod` etc.), aggregated via per-account connector roles assumable from a central identity account.
2. Lab default: single account, this app. Note what changes at scale (naming, task scheduling, entitlement namespacing by account ID).

**Expected result:** Multi-account decision stub in the binder.

### Task 8 — CSV retirement plan and residual risk

1. Retirement plan for `MNB-AWS-Cloud`: after two clean native cycles, mark the CSV app inactive, migrate any certifications referencing it, archive final Task Result, delete the export cron.
2. Record `RR-AWS-SSO-01`: *Federated access via IAM Identity Center permission sets is not visible to this connector. Compensating controls: Okta group governance (Lesson 73) + periodic Identity Center assignment export review.* Owner: `jordan.reed`.

**Expected result:** Retirement plan + RR logged with compensating controls.

---

## Acceptance criteria

- [ ] Upgrade rationale and CSV coexistence/retirement plan written
- [ ] Real-world setup understood: connector principal, least-privilege policy JSON, guardrails
- [ ] `MNB-AWS-IAM` created; schema carries both entitlement families; create-identities off
- [ ] Aggregation evidence (live or mock) with the three seeded findings identified
- [ ] Four-step leaver card with explicit access-key deletion and SSO caveat
- [ ] Multi-account stub + `RR-AWS-SSO-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AccessDenied` naming an action | Connector policy missing that action | Add exactly that action; resist `iam:*` |
| Keys found in git history | Secret mishandled | Rotate immediately; purge history per security process; add pre-commit scanning |
| Native and CSV counts diverge | Expected — the CSV is stale | Investigate deltas; this is the retirement argument, not a bug |
| Privileged headcount looks too low | Privilege moved to Identity Center permission sets | Confirm blind spot; lean on `RR-AWS-SSO-01` controls |
| Leaver still calling APIs after "disable" | Login profile deleted but access keys alive | Deactivate/delete keys; fix the runbook and the workflow |
| Service accounts polluting certifications | No employeeId → uncorrelated humans-ish rows | Filter `svc-*` into a service-account population with its own review |

---

## Training binder evidence

- Upgrade rationale + delta note vs CSV
- Connector policy JSON + guardrail notes (no keys!)
- Aggregation Task Result + findings write-up (Jordan double-grant, second key, `svc-databake`)
- Leaver card with key-deletion step
- Multi-account stub, retirement plan, `RR-AWS-SSO-01`

---

## Knowledge check

1. Why do IAM groups and directly-attached policies form two separate entitlement families?
2. Why is deleting the login profile insufficient to offboard an IAM user?
3. What human access does this connector *not* see, and what compensates?
4. Why should the connector's own policy start read-only?
5. What made the CSV approach unacceptable for cloud, in one sentence?
6. Why must `svc-databake` not appear in a manager certification?

### Answers

1. Group membership is the governed norm; a direct attachment bypasses group review and is itself a potential finding — merging them hides exactly the signal you want.
2. Access keys are independent credentials that survive console-access removal; they must be deactivated and deleted explicitly.
3. IAM Identity Center (AWS SSO) permission-set assignments; compensated by Okta group governance and periodic assignment exports (`RR-AWS-SSO-01`).
4. A writable IAM connector is a privileged system; provisioning permissions are added per-action after security review (phase 2).
5. Cloud access changes hourly, so a quarterly extract certifies a fiction — Jordan was admin for 11 weeks while IIQ said read-only.
6. It's a machine identity with no owning human in the row; it belongs in a service-account inventory with key-rotation review, not a people certification.

---

## Further reading

- [AWS IAM User Guide — Security best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) — AWS's own list; note how many items (no direct attachments, rotate keys, prefer roles) map to this lesson's findings.
- [AWS IAM API Reference](https://docs.aws.amazon.com/IAM/latest/APIReference/welcome.html) — the exact calls behind aggregation and provisioning.
- [AWS IAM Identity Center documentation](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html) — understand the blind spot you documented in `RR-AWS-SSO-01`.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "AWS connector" for the version-specific application guide.
- [CIS Amazon Web Services Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services) — the audit checklist examiners and cloud-security teams both use; sections on IAM users and access keys mirror Tasks 4–6.

---

## Stretch lab

Cross-map `OKTA_AWS_POWER` (Lesson 73) to the AWS entitlements it ultimately grants, and draft a dual-certification note: the IdP group and the IAM/permission-set privilege must be reviewed as one logical access, or a revoke on one rail leaves the other alive. Then write the CloudTrail query (or describe it) that would alert on the connector principal calling any action outside its policy.

---

## Summary

- Native IAM aggregation replaces stale extracts with continuous inventory: groups, direct policy attachments, and — critically — access keys.
- The connector's own footprint is a security design: least-privilege policy, phased write permissions, guardrails against self-modification.
- Cloud offboarding is only complete when credentials die with the user, and the Identity Center blind spot is documented, compensated, and owned.

---

**Previous:** [Lesson 75 — M365 & SharePoint Online](75-m365-sharepoint-online.md)  
**Next:** [Lesson 77 — Workday HCM Connector](77-workday-hcm-connector.md)
