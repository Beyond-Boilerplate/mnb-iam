# Lesson 227 — App-Owner Certification Live

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~75 minutes  
**Prereq:** Lesson 226  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 44

> **Why:** App owners certify what managers cannot judge — whether an account still belongs on their system, not whether a person still needs it for their job.

## What this is

Lesson 226 asked managers: “Does this **person** still need this access?”

**Application-owner certification** asks a different question: “Does this **account** still belong on *my* application?”

| Lens | Certifier resolves from | Each row is… |
| --- | --- | --- |
| Manager (226) | Identity `manager` chain | One identity’s access items |
| **App owner (227)** | `Application.Owner` field | One **account on that app** |

The pack includes `MNB-Cert-App-Owner-Wire` (`certificationType="Application"`, `certifierName="applicationOwner"`) scoped to Wire Portal (or you target CRM if Wire isn’t separate).

Today `Application.Owner` is often still `spadmin`. An admin rubber-stamping their own admin-owned app is **not** an owner decision. You will reassign ownership to `marcus.approve`, generate the cert, decide as Marcus, revoke something stale, and prove the live target changed.

## Know these

```text
Application.Owner = spadmin (meaningless for accountability)
  → reassign Owner to marcus.approve
  → generate Application Owner Certification
  → Mailpit launch mail to marcus.approve@…
  → Marcus decides per-account rows (not whole-identity access)
  → Revoke + sign-off
  → live target: entitlement removed or account disabled
```

| Term | Plain English |
| --- | --- |
| **Application Owner** | Persona accountable for who has accounts on that system |
| **`certifierName="applicationOwner"`** | IIQ looks up `Application.Owner` for the certifier |
| **Account-level row** | One link on one app — not Helen’s entire access list |
| **Manager vs owner** | Job need vs system membership |

- **Wrong way:** Leaving `Owner` on `spadmin` and certifying anyway — no real accountability.
- **Wrong way:** Expecting the same row shape as Lesson 226 — owner certs are account/app scoped.
- **Wrong way:** Revoke accepted in UI but never checking the target system.

## Intent

- Reassign an Application’s Owner to a real persona (`marcus.approve`).
- Launch an app-owner certification; decide as that owner.
- Revoke a stale entitlement/account; prove the target changed.
- Compare row shape/count to Lesson 226’s manager cert.

## Before you start

- [ ] Lesson 226 manager cert completed (comparison baseline — note rough row count)
- [ ] `marcus.approve` exists as an Identity cube
- [ ] Target app aggregated recently (`MNB-WirePortal` or `MNB-Salesforce-CRM-Live`)
- [ ] Mailpit: [http://localhost:8025](http://localhost:8025)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/227
```

## Do this

### Task 1 — Reassign Application Owner

1. **Applications → Application Definition**  
2. Open `MNB-WirePortal` (or `MNB-Salesforce-CRM-Live` if Wire isn’t separately onboarded)  
3. Set **Owner** to `marcus.approve`  
4. **Save**  

- **Why:** `certifierName="applicationOwner"` resolves the certifier straight off this field.
- **Expect:** Owner saved; not `spadmin`.

Screenshot under evidence.

> **Watch out:** Owner dropdown empty? Marcus must exist as an Identity — Refresh Identity Cubes / re-check seed.

### Task 2 — Generate the app-owner certification

1. **Certifications → Schedule / Generate → Application Owner Certification**  
2. Definition: `MNB-Cert-App-Owner-Wire` (or equivalent)  
3. Target the re-owned app  
4. **Generate Now**  

- **Expect:** Generation Task Result success; note approximate account/row count.

### Task 3 — Mailpit launch mail to the owner

Open Mailpit; look for mail to `marcus.approve@meridiannb.com` (or your seed email).

- **Expect:** Launch mail present; subject/audience differ from Lesson 226’s manager mail.

Note subject under evidence.

### Task 4 — Decide as Marcus (account-level rows)

1. Log in as `marcus.approve` / `LabUser1!`  
2. Open **My Certifications**  
3. Observe: rows are **one per account on the app**, not one identity’s whole access  
4. Pick a stale account — e.g. `priya.wire` if she no longer needs initiator rights on this app — and **Revoke**  

- **Expect:** Revoke recorded on an account-level row.

> **Tip:** Write one comparison line now: “226 rows ≈ N identity-access items; 227 rows ≈ M accounts on one app.”

### Task 5 — Complete / sign off

**Complete Certification**.

- **Why:** app-owner certs also honor `processRevokesImmediately`; sign-off is still the audit event.
- **Expect:** cert status completed.

### Task 6 — Prove the live target changed

Pick the proof that matches your app:

**CRM SCIM mock:**

```bash
curl -s http://localhost:8091/crm/scim/v2/Users \
  | python3 -m json.tool | head -100
```

Look for `active:false` or entitlement removed for the revoked user.

**JDBC Core Banking:**

```bash
psql -h localhost -p 5435 -U mnb -d mnb_apps \
  -c "select username, status, entitlement from mnb_app_accounts;"
```

**Wire / LDAP:** use the app’s account list in IIQ after re-agg, or `ldapsearch` if the revoke hit OpenLDAP.

- **Expect:** live account reflects the revoke.

Save command output under evidence; copy Provisioning Transaction id if present (Lesson 229).

### Task 7 — Mailpit completion + remediation note

Refresh Mailpit for the owner’s completion notice; check for a remediation work item if the revoke needed manual fulfillment.

- **Expect:** completion mail present; remediation noted if shown.

### Task 8 — Write the manager-vs-owner comparison

Under evidence:

```text
Manager cert (226): asks "does this person still need access?" — rows = identity access
App-owner cert (227): asks "does this account belong on my system?" — rows = accounts on app
Owner was marcus.approve (not spadmin). Revoked <user> on <app>. Target proof: <file>
```

## If it fails

| Symptom | Fix |
| --- | --- |
| Owner field won’t save / not in dropdown | `marcus.approve` must exist as Identity; Refresh cubes |
| Cert has zero accounts | Aggregate the app first |
| Marcus can’t see the cert | Owner reference must match Identity **name**, not only display name |
| Revoke accepted, target unchanged | Check Provisioning Transactions for Failed/Retry; Test Connection; retry |
| Still certifying as spadmin | Log out; log in as Marcus — same accountability rule as 226 |

## You are done when

- [ ] App Owner is a real persona (not spadmin)  
- [ ] Decision made **as that persona**  
- [ ] Target system shows account disabled or entitlement removed  
- [ ] Written manager-vs-owner comparison  

## Control note

- **Control:** Application-owner (account-level) access certification  
- **Owner:** App owner (`marcus.approve`) + IAM Ops (campaign)  
- **SLA (lab):** Same session decide; production account-level campaigns often quarterly per app  
- **Evidence:** `~/iiq-lab-evidence/sandbox/227/` — owner reassignment, launch mail, revoked account, target proof  

## Quick check

1. What field drives `certifierName="applicationOwner"`? → `Application.Owner`  
2. What’s the row unit vs a manager cert? → Account-on-app, not identity’s whole access  
3. Why is `spadmin` as Owner meaningless? → No real accountability  
4. What question does app-owner cert answer? → “Does this account still belong on my system?”  

## Feedback

Could you explain manager vs app-owner cert in two sentences without looking back? If Marcus never saw the cert, note whether Owner was saved as the Identity **name** — display-name mismatches are a common miss.

## Navigate

- Previous: [Lesson 226](226-manager-cert-mail.md)
- Next: [Lesson 228](228-targeted-cert-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
