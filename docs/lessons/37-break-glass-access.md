# Lesson 37 — Emergency / Break-Glass Access

**Level:** Advanced  
**Track:** Requests  
**Time:** 60–75 minutes  
**Prereq:** Lesson 36 (approval chains); Lesson 28 privileged roles; LCM recommended  

**Lab data:**
- Entitlement / role: `PRIV_BREAK` — `lab-data/reference/entitlement-dictionary.csv`
- Role design: `MNB-Role-BreakGlass` (Lesson 28) if present
- Ticket pattern: `MNB-INC-####` required in request comments
- Approver: Security (`helen.ross` / SOC); contrast Lesson 34 rapid **offboard**

---

## Learning objectives

You will be able to:

- Document Meridian break-glass policy (max duration, Security approval, logging)
- Request short-lived `PRIV_BREAK` / BreakGlass access with a mandatory incident ticket in comments
- Route approval to Security (not manager-only rubber stamp)
- Revoke / sunset access the same day and verify removal
- Schedule post-incident review (manager + Security) within two business days
- Contrast emergency **grant** (this lesson) with emergency **disable** (Lesson 34)

---

## Why this matters

**Business.** Outages tempt shared root passwords and Zoom heroics. A governed break-glass path is slower than a sticky note password—and infinitely safer for a bank. When a payment batch sticks at 2 a.m., Meridian needs `PRIV_BREAK` with ticket `MNB-INC-1042`, not a standing admin shared among on-call engineers.

**Control / audit.** Standing break-glass accounts fail the purpose. Examiners want: ticket linkage, short TTL, Security approval, automatic or same-day removal, and post-review. Control owner: Security Operations; IAM owns tooling; Technology owns platform recovery runbooks. This is the emergency **grant** pattern—Lesson 34 is emergency **disable** for leavers/incidents; do not confuse them.

---

## Concepts

### Break-glass policy (Meridian lab standard)

| Control | Requirement |
| --- | --- |
| Entitlement | `PRIV_BREAK` / role `MNB-Role-BreakGlass` |
| Max duration | 8 hours (same calendar day preferred) |
| Approval | Security (`helen.ross` / SOC)—not manager alone |
| Comment | Mandatory `MNB-INC-####` (+ bridge link optional) |
| Standing accounts | Forbidden |
| Post-review | Manager + Security within 2 business days |
| Catalog | Not casual self-service (Lesson 35) |

### Grant vs disable

| Pattern | Lesson | Intent |
| --- | --- | --- |
| Break-glass **grant** | 37 | Temporary privilege to recover production |
| Rapid **offboard** | 34 | Emergency removal of access (leaver/insider risk) |

Using break-glass to “get around” LoA freeze for `sofia.torres` or contractor expiry for `raj.external` is a policy violation—not an emergency.

### Dual approval vs Security-only

Lesson 28 intent listed Technology Director + Security for BreakGlass design. Operational lab standard routes the IdentityRequest to **Security** as the mandatory vote (manager may be informed). Manager-only approval is forbidden—managers rubber-stamp outages.

---

## How it works

Break-glass is a controlled LCM request with aggressive sunset, Security approval, and mandatory post-review—not a permanent Bundle assignment.

```
Incident declared (MNB-INC-1042)
        │
        ▼
Request PRIV_BREAK / MNB-Role-BreakGlass with ticket in comment
        │
        ▼
Security approves (time-boxed ≤ 8h)
        │
        ▼
Provision / enable short-lived access
        │
        ▼
Incident mitigated → revoke same day
        │
        ▼
Post-access review (manager + Security ≤ 2 business days)
```

| Mechanism | Purpose |
| --- | --- |
| Sunrise/sunset on request | Enforces TTL when configured |
| Mandatory comment | Ticket linkage for SIEM / IR |
| Security work item | Prevents manager-only rubber stamp |
| Same-day revoke | No standing break-glass residue |
| Post-review mini-cert | Detect abuse / lateral movement lessons |

**IIQ terms:** Model as requestable role with aggressive sunset, sunrise/sunset dates on the request, or manual revoke plus certification. PAM checkout (vaulted credential) is the production complement—“IIQ role is necessary but not sufficient.”

---

## Before you start

- [ ] LCM available or alternate request path documented
- [ ] `PRIV_BREAK` exists as managed attribute and/or BreakGlass role exists (Lesson 28)
- [ ] Security approver identity available (`helen.ross` or lab SOC user)
- [ ] Pick a technical identity for the drill (e.g. `owen.morris` / SRE)—not finance wire users unless scenario demands
- [ ] Evidence folder `~/iiq-lab-data/evidence/break-glass-L37/`

---

## Lab procedure

### Task 1 — Publish the policy page

Ops and Security need one page they can recite under pressure.

1. Write `MNB-BreakGlass-Policy` text covering duration, approval, comment rules, revoke, and post-review.
2. Explicitly ban: shared admin passwords, permanent `PRIV_BREAK`, manager-only approval for break-glass.
3. Cross-link Lesson 34: break-glass **grant** ≠ rapid **offboard**.
4. Cross-link Lesson 28: role object exists; this lesson exercises the emergency path.

**Expected result:** One-page policy suitable for Security handbook append.

**If it fails:** Use the policy table in Concepts verbatim with Meridian names.

### Task 2 — Prepare PRIV_BREAK for governed request

1. Open managed attribute / role for `PRIV_BREAK`.
2. Ensure it is **not** in the casual catalog; use privileged QuickLink or admin-on-behalf only.
3. Set or document: requestable under controlled path; require comments; approval scheme = Security.
4. If Lesson 28 role `MNB-Role-BreakGlass` exists, prefer requesting the role (bundles explanation).

**Expected result:** Controlled request path identified; casual CRM catalog does not advertise break-glass.

**If it fails:** Admin-on-behalf IdentityRequest with Security work item is acceptable lab pattern.

### Task 3 — Submit break-glass with ticket comment

The ticket string is the forensic link. Missing ticket = reject.

1. Open Access Request (privileged path).
2. Target: chosen engineer identity.
3. Add `PRIV_BREAK` or `MNB-Role-BreakGlass`.
4. Set sunset / end date-time within 8 hours if UI supports it.
5. Comment **exactly** includes ticket, e.g.:

```text
MNB-INC-1042 — prod payment batch stuck; need BreakGlass to restart consumer; bridge recorded
```

6. Submit.

**Expected result:** IdentityRequest pending Security with ticket visible in comments.

**If it fails:** If comment not mandatory in UI, still include ticket and note “config gap: make comment required.”

### Task 4 — Security approval

1. Open work item as Security approver (`helen.ross` or act-as).
2. Verify incident ticket format present; reject if missing.
3. Approve with comment: `Approved 8h TTL — revoke after INC bridge closes`.
4. Record approver, time, request id.

**Expected result:** Approval history shows Security identity—not only the user’s manager.

**If it fails:** Reassign work item to `helen.ross`; fix approval scheme for next run.

### Task 5 — Sunset / revoke same day

Standing residue is the failure mode examiners find months later.

1. After “incident mitigated” (lab simulation), revoke `PRIV_BREAK` / remove role.
2. Methods: access request remove, certification revoke, Manage Access remove, or sunset auto-expire if configured.
3. Refresh identity; confirm entitlement gone.
4. Timestamp revoke in evidence folder.

**Expected result:** Same-day removal proven; no standing break-glass left on the cube.

**If it fails:** Manual entitlement remove + Refresh; file config ticket for automatic sunset.

### Task 6 — Post-incident review

1. Schedule review within 2 business days: Manager of recipient + Security.
2. Agenda: Was ticket valid? Was TTL honored? Any lateral movement? Lessons for PAM integration.
3. Write mini-cert outcome: `Acceptable emergency use` or `Policy violation—escalated`.

**Expected result:** Post-review note with date, attendees, and outcome in the binder.

### Task 7 — Examiner question drill

*”Prove break-glass was time-boxed, Security-approved, and removed.”*

Write the three-artifact answer: (1) IdentityRequest with `MNB-INC-####` comment, (2) Security approval history, (3) post-revoke cube screenshot + post-review note.

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Break-glass policy page written (≤8h, Security approve, ticket required)
- [ ] Request submitted with `MNB-INC-####` in comments
- [ ] Security approval recorded
- [ ] Same-day revoke verified on identity
- [ ] Post-review scheduled/documented within 2 business days

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Manager approved only | Wrong scheme | Route PRIV_BREAK to Security |
| Access still present next day | No sunset | Manual revoke; add TTL |
| Appears in CRM catalog | Requestable flag | Hide / privileged QuickLink |
| No ticket in comment | UI allows empty | Reject request; make comment required |
| Confused with Lesson 34 | Grant vs disable | Re-read Concepts contrast |

---

## Training binder evidence

1. Policy page
2. IdentityRequest with `MNB-INC-1042` (or your ticket) comment
3. Security approval work item history
4. Post-revoke identity screenshot
5. Post-review meeting note

**Control owner:** Security Operations; IAM owns tooling; Technology owns recovery runbooks  
**SLA:** ≤8h TTL; same-day revoke; post-review ≤ 2 business days

---

## Knowledge check

1. What is the max duration for Meridian break-glass in this lab standard?
2. What must appear in the request comment?
3. Who approves break-glass?
4. What is the post-review window?
5. Why are standing break-glass accounts forbidden?
6. How does this lesson differ from Lesson 34?

### Answers

1. 8 hours (same day preferred).
2. Incident ticket id (`MNB-INC-####`) plus brief justification.
3. Security / SOC (e.g. `helen.ross`)—not manager alone.
4. Within 2 business days (manager + Security).
5. They become unmonitored permanent privilege—the opposite of emergency time-boxing.
6. Lesson 37 is emergency **grant**; Lesson 34 is emergency **disable**/offboard.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “sunrise sunset” and “privileged access request” for TTL on role assignments.
- [SailPoint Community](https://community.sailpoint.com/) — search “break glass” for Security-approved emergency request patterns.
- [NIST SP 800-53 AC-2(2)](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — temporary and emergency accounts; automated termination.
- [NIST SP 800-53 AU-2 / AU-6](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — audit events and review; ticket linkage and post-incident review.
- [CIS Controls v8 — Control 5 & 8](https://www.cisecurity.org/controls) — admin account management and audit log management for emergency privilege.

---

## Stretch lab

1. Integrate conceptually with PAM: IIQ requests checkout of vaulted credential; store PAM session id in comment.
2. Auto-launch a focused certification on any identity that received `PRIV_BREAK` in the last 7 days.
3. Add SIEM alert when `PRIV_BREAK` is assigned.

---

## Summary

- You defined a time-boxed, ticketed, Security-approved break-glass path for `PRIV_BREAK`.
- You practiced request → approve → same-day revoke → post-review.
- You kept emergency grant distinct from rapid offboarding disable.

---

**Previous:** [Lesson 36b — Be the Approver](36b-be-the-approver.md) · [Lesson 36 — Approval Chains & Escalations](36-approval-chains.md)  
**Next:** [Lesson 38 — IdentityRequest Tracking & Auditing](38-identity-request-tracking.md)
