# Lesson 76 — AWS IAM Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 75–90 min  
**Prereq:** Lesson 75 — M365 & SharePoint Online; Lesson 13 AWS CSV onboard helpful  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (AWS IAM row)
- Repo: `lab-data/apps/MNB-AWS-Cloud.csv` (contrast file extract)
- Repo: `lab-data/connectors/features-string-glossary.md`

---

## Learning objectives

You will be able to:

- Prefer **AWS IAM** / AWS connector over static CSV for privileged cloud governance when licensed
- Create **MNB-AWS-IAM** application with access key / role assumption placeholders
- Map IAM users, groups, and policies (or roles) to IIQ entitlements with Meridian risk tiers
- Complete lab-without-live-target using CSV contrast + native connector design pack
- Define Account Aggregation and break-glass / leaver expectations for cloud admins

---

## Why this matters

**Business.** Meridian AWS accounts host banking workloads. `AWS_ADMIN`-class access is high blast radius. File extracts drift; native IAM aggregation tracks policies closer to truth.

**Control / audit.** Examiners ask for continuous inventory of cloud admins and proof of revoke. Native connector Task Results beat quarterly CSV copies.

---

## Concepts

**AWS IAM connector.** Aggregates AWS IAM users/groups/policies (and related objects per connector version). Distinct from account landing-zone org management.

| Pattern | When |
| --- | --- |
| Native AWS IAM connector | Ongoing governance, provisioning |
| DelimitedFile `MNB-AWS-Cloud` | Early lab / emergency extract |
| Okta group `OKTA_AWS_POWER` | SSO path—still certify both IdP and AWS as designed |

```
MNB-AWS-IAM (native)
        │
        ▼
 AWS APIs (IAM)
        │
        ├── Users / Groups / Policies
        └── Provision attach/detach (if enabled)
```

**Matrix:** AWS IAM → AWS IAM / AWS.

**Lab-without-live-target.** Design pack + mock IAM inventory; optionally keep CSV app labeled legacy.

---

## Before you start

- [ ] IIQ up; `lab-data/apps/MNB-AWS-Cloud.csv` readable for contrast
- [ ] Never commit AWS access keys; use vault/env
- [ ] Persona `jordan.reed` as cloud admin candidate

---

## Lab procedure

### Task 1 — Contrast CSV vs native

1. Open `MNB-AWS-Cloud.csv`; note entitlements present.
2. Write upgrade rationale for `MNB-AWS-IAM` native app.
3. Plan coexistence: CSV retired after native agg proven.

**Expected result:** Upgrade rationale paragraph.

### Task 2 — Create MNB-AWS-IAM

1. Applications → Add New → **AWS** / **AWS IAM** (or equivalent).
2. Name: `MNB-AWS-IAM`. Owner: `helen.ross`; tech `jordan.reed`.
3. Configure account id / access key / IAM role ARN placeholders.
4. Save shell.

**Expected result:** Application object created.

**If it fails:** Document least-privilege IAM policy for connector user offline.

### Task 3 — Entitlement taxonomy

1. Define: `AWS_IAM_ADMIN`, `AWS_POWERUSER`, `AWS_READONLY`, `AWS_BILLING`.
2. Risk: ADMIN critical; POWERUSER high.
3. Map to dictionary; align names with prior `MNB-AWS-Cloud` where possible.

**Expected result:** Taxonomy table.

### Task 4 — Mock inventory (lab-without-live-target)

1. Create `~/iiq-lab-data/connectors/aws/MNB-AWS-IAM-mock.csv` with `userName,arn,employeeId,groups,policies,active`.
2. Include `jordan.reed`, `kai.nguyen`, `raj.external`.
3. Shadow aggregate.

**Expected result:** ≥3 accounts in aggregation evidence.

### Task 5 — Account Aggregation task

1. `MNB-AWS-IAM-Account-Aggregation`
2. Run live or shadow; compare counts to CSV legacy app if both exist.
3. Note deltas for binder.

**Expected result:** Task Result + delta note.

### Task 6 — Break-glass & leaver

1. Reference Lesson 37: temporary AWS admin must auto-expire.
2. Leaver: detach policies/groups → disable access keys → deactivate user → re-agg.
3. Evidence list for examiner.

**Expected result:** Cloud leaver/break-glass card.

### Task 7 — Multi-account note

1. Document whether Meridian needs one IIQ app per AWS account or aggregated via org pattern.
2. Lab default: single account `MNB-AWS-IAM`.

**Expected result:** Multi-account decision stub.

### Task 8 — Residual risk

`RR-AWS-SSO-01`: permissions via AWS SSO permission sets may need separate connector scope.

**Expected result:** RR logged.

---

## Acceptance criteria

- [ ] CSV vs native upgrade rationale written
- [ ] `MNB-AWS-IAM` shell + entitlement taxonomy
- [ ] Mock/Shadow aggregation evidence
- [ ] Leaver/break-glass card complete
- [ ] Multi-account stub + RR-AWS-SSO-01 recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| AccessDenied on agg | Connector IAM policy too tight | Grant iam:List*/Get* as required; Shadow for class |
| Keys in git | Misplaced secret | Rotate immediately; purge history per security process |
| CSV and native diverge | Stale file | Prefer native; retire CSV schedule |
| SSO users missing | IAM users only aggregated | Document SSO permission set approach |
| Admin still has keys | Disable user without key delete | Include access key deletion in runbook |

---

## Training binder evidence

- Upgrade rationale
- App config redacted
- Taxonomy + mock agg
- Leaver/break-glass card
- RR-AWS-SSO-01

---

## Knowledge check

1. What Meridian app name is used for native AWS IAM?
2. Why retire `MNB-AWS-Cloud` CSV after native success?
3. Which persona is the tech contact?
4. Name a critical entitlement from the taxonomy.
5. What residual risk addresses AWS SSO permission sets?

### Answers

1. `MNB-AWS-IAM`.
2. File extracts drift; native APIs reflect current IAM state.
3. `jordan.reed`.
4. `AWS_IAM_ADMIN`.
5. `RR-AWS-SSO-01`.

---

## Stretch lab

Cross-map `OKTA_AWS_POWER` (Lesson 73) to AWS entitlements and draft a dual-cert note (IdP group + IAM policy).

---

## Summary

- Native AWS IAM connector supersedes static cloud CSV for Meridian privileged governance.
- Lab-without-live-target still delivers taxonomy, mocks, and leaver evidence design.
- SSO permission sets and multi-account layouts need explicit residual risks.

---

**Previous:** [Lesson 75 — M365 & SharePoint Online](75-m365-sharepoint-online.md)  
**Next:** [Lesson 77 — Workday HCM Connector](77-workday-hcm-connector.md)
