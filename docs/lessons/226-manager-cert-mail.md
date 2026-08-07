# Lesson 226 — Manager Cert + Email

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~90 minutes  
**Prereq:** Lessons 203, 214  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 43

> **Why:** Certs are real when certifiers get mail and decide in-product — rubber-stamp Approve-All hides real decisions and fails manager usability. Revoke must reach a live target, not only the IIQ database.

## What this is

A **certification** (access review) asks a human: “Does this access still belong?”

**Manager Access Review** is an **Identity**-type certification:

| Idea | Meaning |
| --- | --- |
| **One cert per manager** | Helen gets a campaign for her direct reports |
| **Rows** | Each report’s entitlements / roles |
| **Certifier** | Resolved from the identity `manager` chain (`certifierName="manager"`) |
| **Decisions** | Approve, Revoke, Delegate, … |
| **Sign-off** | Closes the campaign for audit |

The pack ships `MNB-Cert-Manager-Access-Review` (`config/CertificationDefinition/MNB-CertificationDefinition-Manager.xml`) with `processRevokesImmediately=true` — so a **Revoke** can fire a **Provisioning Transaction** against Samba / OpenLDAP / JDBC / CRM in the same session.

**Mailpit** ([http://localhost:8025](http://localhost:8025)) catches launch and completion mail (Lesson 203 SMTP).

Classic 43 taught decision quality on static data; here you decide *as Helen*, revoke something meaningful, and prove the target changed.

## Know these

```text
Confirm Helen has reports (manager correlation)
  → Generate Manager Access Review (scoped org)
  → Mailpit launch / assignment mail to Helen
  → Log in AS helen.ross (not spadmin)
  → Approve one appropriate row + Revoke one high-risk row
  → Complete / sign-off
  → Provisioning Transaction on live app
  → Mailpit completion mail
  → Save ids for Lesson 229
```

| Decision | When to use |
| --- | --- |
| **Approve** | Access still required and appropriate |
| **Revoke** | Access no longer needed — expect live provision |
| **Delegate** | Someone else must decide (use sparingly in lab) |
| **Exception / forward** | Edge cases — document why |

| Term | Plain English |
| --- | --- |
| **Certifier** | Person accountable for decisions |
| **Campaign / definition** | Template that generates certs |
| **Approve-All pathology** | Clicking approve on everything without reading |
| **`processRevokesImmediately`** | Revokes provision on save instead of waiting |

**Sizing:** Prefer Helen’s org — finishable in ~30–45 minutes of decisions. Birthright-only noise trains Approve-All — include at least one high-risk Wire/CRM row to revoke.

- **Wrong way:** Completing as `spadmin` instead of the manager — no certifier accountability trail.
- **Wrong way:** Approve-All with zero revokes on a mixed-risk population — rubber stamp.
- **Wrong way:** Stopping at “Revoke clicked” without a Committed Provisioning Transaction / target proof.

## Intent

- Launch manager cert for Helen’s org; see launch mail in Mailpit.
- Decide as `helen.ross` (approve one, revoke one meaningful entitlement).
- Prove revoke on a live target via Provisioning Transaction.
- Sign off; confirm completion mail; save ids for Lesson 229.

## Before you start

- [ ] Mailpit works (Lesson 203): [http://localhost:8025](http://localhost:8025)
- [ ] Manager correlation: Helen has reports (Lesson 214)
- [ ] Pass-through / lab password for Helen: `LabUser1!` (or your seed)
- [ ] At least one report holds a revocable Wire/CRM entitlement you can re-check live
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/226
```

## Do this

### Task 1 — Confirm Helen’s org is non-empty

In IIQ identity search (Advanced / filter), find identities whose manager is `helen.ross` (e.g. Christopher Hayes and others).

- **Why:** empty org = zero-row cert = nothing to decide.
- **Expect:** non-empty report list.

If empty: fix manager correlation / Refresh Identity Cubes (Lesson 214), then continue.

### Task 2 — Generate the manager certification

1. **Certifications → Schedule / Generate → Manager Access Review**  
2. Definition: `MNB-Cert-Manager-Access-Review` (or your pack’s manager definition)  
3. Scope: Helen’s subordinates (keep it tight)  
4. Name: `MNB-Mgr-<today>`  
5. **Generate Now**  

- **Why:** `processRevokesImmediately=true` provisions on save so you verify targets same session.
- **Expect:** Generation Task Result success.

### Task 3 — Mailpit launch mail

Open Mailpit; search `helen.ross` / certification / access review.

- **Expect:** Certification generated / assignment mail visible.

Screenshot under evidence; note message id.

> **Tip:** No mail? Gear → Global Settings → IdentityIQ Configuration → Notification Settings: SMTP host `mailpit`, port `1025`. Re-launch; refresh Mailpit.

### Task 4 — Decide as Helen (not spadmin)

1. Log out of `spadmin`  
2. Log in as `helen.ross` / `LabUser1!`  
3. Open **My Certifications**  
4. **Approve** one correct birthright-style entitlement (still appropriate)  
5. **Revoke** one Wire or CRM entitlement on a report (e.g. Christopher Hayes) you can re-check on a live app  

- **Why:** two decision types prove you read the rows — not Approve-All.
- **Expect:** Approve + Revoke both recorded.

> **Watch out:** Certifying while still logged in as spadmin fails the accountability control even if the UI lets you click.

### Task 5 — Complete / sign off

**Complete Certification** (sign-off).

- **Why:** sign-off is the event that closes the campaign; undecided certs don’t complete the mail/provision story.
- **Expect:** cert status completed / signed off.

### Task 6 — Prove revoke via Provisioning Transaction

As `spadmin`: **Setup → Provisioning Transactions** (or Monitor path your build uses).

Filter to the revoked identity / app.

- **Expect:** Committed/Success against a live app (e.g. `MNB-Salesforce-CRM-Live` or `MNB-WirePortal`).

Copy the **transaction id** under evidence — Lesson 229 needs it.

### Task 7 — Mailpit completion mail

Refresh Mailpit — completion / sign-off mail; note optional Certification Remediation work-item mail if revoke needs manual follow-up.

- **Expect:** completion mail present; note remediation if shown.

### Task 8 — Bag evidence for Lesson 229

Save under `~/iiq-lab-evidence/sandbox/226/`:

- Launch mail id  
- Provisioning Transaction id  
- Completed-cert screenshot  
- Which identity + entitlement you revoked  

- **Expect:** ids ready for remediation tracing.

## If it fails

| Symptom | Fix |
| --- | --- |
| No Mailpit mail | SMTP host `mailpit` port `1025`; re-launch; refresh Mailpit |
| Zero identities in cert | Manager attribute missing; Refresh Helen’s org; regenerate |
| Revoke doesn’t provision | `processRevokesImmediately` false in your copy, or connector down — check Failed PT rows |
| Helen can’t see cert | She must be certifier via `manager` chain, not a random capability |
| Only birthright rows | Broaden scope or pick a report who has Wire/CRM from earlier lessons |

## You are done when

- [ ] Manager cert decided **as Helen** with mail trail  
- [ ] One live revoke with Committed Provisioning Transaction  
- [ ] Completion mail in Mailpit  
- [ ] Ids saved for Lesson 229  

## Control note

- **Control:** Manager access certification + notification  
- **Owner:** Manager (certifier) + IAM Ops (campaign)  
- **SLA (lab):** Same session decide; production campaigns often 14–30 day windows with reminders  
- **Evidence:** `~/iiq-lab-evidence/sandbox/226/` — mails, PT id, sign-off proof  

## Quick check

1. Why not certify as spadmin? → No manager accountability  
2. What flag provisions revokes immediately? → `processRevokesImmediately=true`  
3. Name one rubber-stamp signal → Approve-All with no revokes on a mixed-risk population  
4. What must a Revoke produce for Lesson 229? → A Provisioning Transaction id (and later target proof)  

## Feedback

Could you explain Approve-All pathology in one sentence? If Helen never got mail, note SMTP settings *before* blaming the certification definition — those are separate layers.

## Navigate

- Previous: [Lesson 225](225-policy-violations-live.md)
- Next: [Lesson 227](227-app-owner-cert-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
