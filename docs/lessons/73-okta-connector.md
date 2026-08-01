# Lesson 73 — Okta Workforce IdP Connector

**Level:** Intermediate  
**Track:** Connectors — Web APIs & SaaS  
**Time:** 90–120 min  
**Prereq:** Lesson 72 — ServiceNow Connector; Lesson 59 Entra patterns helpful  

**Lab data:**
- Repo: `lab-data/connectors/connector-selection-matrix.csv` (Okta row)
- Repo: `lab-data/connectors/features-string-glossary.md`
- Repo: `lab-data/connectors/scim/Users.json` (SCIM-shaped reference if Okta SCIM used)

---

## Learning objectives

You will be able to:

- Explain Okta's workforce IdP object model — users, groups, app assignments — and why group-based assignment is the governed norm
- Draw the **IdP boundary**: what IIQ governs in Okta versus what Okta owns outright (auth policy, MFA factors, sessions)
- Explain exactly what the `OKTA_AWS_POWER` group grants and why Lessons 74 and 76 treat it as a cloud entitlement
- Explain why IdP revocation is not downstream revocation — the dual-rail leaver concept
- Map Okta lifecycle states (ACTIVE, SUSPENDED, DEPROVISIONED) to IIQ enable/disable semantics
- Perform the real-world setup: OAuth service app with scoped grants (preferred) vs API token, rate-limit planning
- Create **MNB-Okta**, aggregate groups as entitlements, and design the suspend → strip → deprovision leaver with session revocation

---

## Why this matters

**Business.** Meridian federates workforce SSO through Okta: one login, then tiles for Salesforce (Lesson 71), ServiceNow (Lesson 72), Google Workspace (Lesson 74), and AWS. That convenience concentrates risk in one place — Okta group membership *is* SaaS access. When `jordan.reed` was added to `OKTA_AWS_POWER` during a production incident, that one membership handed him federated power access to Meridian's AWS accounts with no IAM user, no key, and no entry in any AWS-side report. If IIQ cannot see Okta groups, it cannot see a growing share of what people can actually do.

**Control / audit.** The examiner asks two sharp questions here. First: *"is your IdP your identity source of truth?"* — and the answer must be no, `MNB-HR` is; Okta is a governed target, and a mis-set authoritative flag would let IdP accounts mint identities. Second: *"when someone leaves, does killing SSO remove their access?"* — and the honest answer is *only partially*, which is exactly the dual-rail concept this lesson teaches. Being able to articulate both is what separates a defensible IdP control narrative from a hopeful one.

---

## Concepts

### The Okta workforce object model

Okta is a directory plus an authentication broker. Four objects matter for governance:

| Okta object | What it is | Real-life example at Meridian | Governance treatment |
| --- | --- | --- | --- |
| **User** | An account keyed by `login`, with a lifecycle state | `priya.wire@meridiannb.com`, status ACTIVE | The account IIQ aggregates |
| **Group** | A membership set that drives app assignment and policy | `OKTA_AWS_POWER`, `OKTA_WIRE_USERS` | Multi-valued entitlement — the core of this lesson |
| **App assignment** | A user's link to an integrated application (a "tile"), granted **individually or via group** | Priya's Wire Portal tile via `OKTA_WIRE_USERS` | Entitlement where exposed; individual assignments are the review flag |
| **Auth policy / MFA factors / sessions** | How and when users authenticate | Okta Verify push for wire staff | **Okta owns these — IIQ observes at most** |

The assignment mechanic mirrors what you saw in ServiceNow roles and AWS policies: **group-based app assignment is the governed norm; individual assignment is the exception to investigate.** A user hand-assigned to the AWS app outside any group bypasses every group-based review — same finding shape, third platform in a row. Patterns repeat; that is why this track teaches them side by side.

### The IdP boundary — what IIQ governs vs what Okta owns

Not everything in Okta belongs in IIQ's scope, and pretending otherwise produces certifications nobody can act on. Draw the line deliberately:

```
MNB-HR (authoritative: who is a Meridian person)
        │
        ▼
 Identity cubes
        │
        ├── MNB-Okta (TARGET) ────────────────────────────────┐
        │     IIQ GOVERNS: group memberships, app assignments, │
        │     lifecycle state (evidence of enable/disable)     │
        │                                                      │
        │     OKTA OWNS: sign-on policy, MFA factor            │
        │     enrollment, session length, network zones —      │
        │     reviewed with the IdP team, not certified in IIQ │
        └──────────────────────────────────────────────────────┘
```

| Concern | Source of truth |
| --- | --- |
| Who is an employee? | `MNB-HR` — never Okta |
| Who is in which Okta group / has which app tile? | Okta, **governed as entitlements by IIQ** |
| How users authenticate (MFA, sessions, policy) | Okta — IdP engineering owns it; IIQ does not certify it |

Lesson 74 calls these the "Okta boundary concepts" and builds on them: because Meridian federates Google login through Okta, password features on the Google connector are irrelevant — passwords live at the IdP, on Okta's side of this boundary.

### `OKTA_AWS_POWER` — a group that is really a cloud entitlement

Learn this one group thoroughly; two later lessons depend on it. Okta integrates with AWS via SAML federation: membership in `OKTA_AWS_POWER` assigns the AWS app and maps, on Okta's side of the federation, to a power-level AWS role/permission set. The chain:

```
jordan.reed added to OKTA_AWS_POWER
        │  (group-based app assignment)
        ▼
AWS app tile appears; SAML assertion carries the power-role mapping
        ▼
Jordan federates into AWS with power access —
NO IAM user, NO access key, NOTHING visible to the AWS IAM connector
```

Consequences you must be able to recite: the AWS IAM connector (Lesson 76) aggregates IAM users and **cannot see this access at all** — federated access is its documented blind spot (`RR-AWS-SSO-01`), and governing `OKTA_AWS_POWER` here is the compensating control. So the group is risk-rated **critical**, certified like the cloud entitlement it is, and its removal is a first-class leaver step. A reviewer who sees "just an Okta group" and rubber-stamps it has approved AWS power access without knowing it.

### IdP revoke ≠ downstream revoke — the dual-rail leaver

Killing SSO feels final. It is not. When you suspend an Okta user:

- **New** SSO logins stop — the tiles are dead.
- The **SaaS accounts behind the tiles still exist**: the Salesforce user is still active, the ServiceNow `sys_user` still holds roles, the Google account still receives mail. Anyone with a direct-login path, an API token, or an active session on those platforms retains access.
- **Existing sessions and tokens** on downstream apps can keep working until they expire — hours or days, unless explicitly revoked.

So a leaver runs on **two rails**: rail one is the IdP (suspend, strip groups, revoke sessions, deprovision); rail two is every downstream target (Lessons 71, 72, 74, 76 leaver patterns). Lesson 76 states it from the other side: one leaver, two rails. Neither rail alone is complete, and the examiner-grade failure is claiming rail one covered rail two.

### Lifecycle states — Okta's vocabulary for enable/disable

Okta users move through explicit states; the three that matter here:

| Okta state | Meaning | IIQ mapping |
| --- | --- | --- |
| `ACTIVE` | Normal, can authenticate | Enabled account |
| `SUSPENDED` | Login blocked, **fully reversible**, memberships intact | Disable operation — the leaver's first move |
| `DEPROVISIONED` | Deactivated; app assignments torn down; reactivation is a re-onboarding | Terminal state — end of the leaver runway |

Suspend-first mirrors the Google suspend pattern (Lesson 74): instant, reversible, evidence-friendly. Deprovision follows once HR confirms the exit is final.

---

## How it works

The connector calls the **Okta management API** over HTTPS against your org (`https://meridiannb.okta.com`), authenticated by either a static **API token** (SSWS) or — preferred — an **OAuth 2.0 service app** with scoped grants:

```
IdentityIQ (MNB-Okta)
        │  OAuth service app (private key JWT → scoped access token)
        │  or legacy: SSWS API token
        ▼
Okta management API (https://meridiannb.okta.com/api/v1/...)
        ├── GET /users                    → account aggregation (paged, rate-limited)
        ├── GET /groups, /groups/{id}/users → group entitlement aggregation
        ├── POST /users/{id}/lifecycle/suspend | /deactivate → leaver operations
        ├── DELETE /groups/{id}/users/{uid} → group revoke
        └── DELETE /users/{id}/sessions   → session revocation (rapid offboarding)
```

| Operation | API behavior | IIQ behavior |
| --- | --- | --- |
| Account aggregation | Paged `GET /users` via link headers | One account per user; `login` as native identity; `status` carried |
| Group aggregation | `GET /groups` + per-group membership | Managed attributes + memberships on accounts |
| Disable / enable | Lifecycle `suspend` / `unsuspend` | Disable/enable operations |
| Deprovision | Lifecycle `deactivate` | Terminal leaver step |
| Group add / remove | Group membership PUT/DELETE | Entitlement add/remove in a provisioning plan |

Two operational realities. **Rate limits:** Okta enforces per-endpoint API rate limits and answers excess with HTTP 429 plus `X-Rate-Limit-*` headers telling you when to resume; a large nightly aggregation must pace itself, and a connector sharing the org with other integrations shares the budget. **Auth models:** a static SSWS token inherits the full permissions of the admin who minted it and expires on inactivity — a broad, fragile credential. An OAuth service app is granted **only named scopes** (`okta.users.read`, `okta.groups.read` for phase 1) and authenticates with a vaulted private key. The connector that governs the IdP should itself be the least-privileged client on it.

---

## Real-world setup (outside IIQ)

Read this even on the mock path. Okta gives away free developer orgs at [developer.okta.com](https://developer.okta.com/) — you can execute all of it for real.

### Step 1 — Choose the auth model: OAuth service app (preferred)

1. In Okta Admin → Applications → create an **API services app** (OAuth 2.0 service app, or equivalent menu path).
2. Configure **private key JWT** authentication; keep the private key in the vault, never in IIQ config files.
3. Grant scopes for phase 1: `okta.users.read`, `okta.groups.read` — nothing more. Phase 2 (provisioning) adds `okta.users.manage`, `okta.groups.manage`, each addition security-reviewed: a writable IdP connector can suspend the workforce.
4. Fallback only: an SSWS API token minted by a dedicated least-privilege admin (read-only admin role). Document why OAuth wasn't possible if you take this path.

### Step 2 — Rate-limit planning

1. Check your org's per-endpoint limits and what other integrations (HR sync, SIEM pullers) already consume.
2. Schedule the IIQ aggregation off-peak and record the expected call volume (roughly: users ÷ page size + groups + per-group membership pages).

### Step 3 — Naming and hygiene in the org

1. Confirm the governance-relevant groups follow the `OKTA_` convention (`OKTA_AWS_POWER`, `OKTA_WIRE_USERS`, `OKTA_ALL_STAFF`, `OKTA_CONTRACTORS`) so the entitlement catalog reads cleanly.
2. Verify `employeeId` is populated on Okta user profiles from the HR-driven flow — it is your robust correlation key.

### Step 4 — Governance records

Document: org URL, service app client ID, granted scopes, key rotation date, rate-limit notes, phase 1/2 status, and security sign-off.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; HR-authoritative concept from Lesson 04 solid
- [ ] Decide your path: live Okta developer org (free) or the mock fallback in Task 5
- [ ] No production Okta tokens on lab machines — placeholders or a disposable dev org only
- [ ] Personas: `priya.wire`, `jordan.reed`, `nina.joiner`, `raj.external`, `samir.hassan`; IdP engineering contact `kai.nguyen`

---

## Lab procedure

### Task 1 — Authoritative boundary statement

Every Okta deployment eventually faces the temptation to let the IdP mint identities "because the data is right there." Kill that idea in writing before touching configuration.

1. Write: *Okta does not create Meridian identities in this design; `MNB-HR` does. `MNB-Okta` is a non-authoritative target.*
2. Note the exception process: if a future project proposes Okta-authoritative contractors, it requires an ADR and a formal control-design review — not a checkbox flip.
3. Sketch the boundary diagram from the Concepts section into the binder: govern groups/assignments/state; leave auth policy, MFA, and sessions with the IdP team.

**Expected result:** Boundary statement and diagram in the binder.

### Task 2 — Create MNB-Okta

In production this consumes the Step 1 outputs: org URL and OAuth client credentials. The connector form asks for exactly those.

1. Applications → Add New → **Okta** (or equivalent menu path).
2. Connection: org URL `https://meridiannb.okta.com` (lab: your dev org URL), auth = OAuth service app client ID + private-key placeholder noting "key in vault" (SSWS token as documented fallback).
3. Name `MNB-Okta`; owner `helen.ross`; IdP engineering contact `kai.nguyen`. Save.
4. Live org: click **Test Connection** — success proves TLS, token issuance, and at least `okta.users.read`.

**Expected result:** `MNB-Okta` saved; live path shows Test Connection success.

**If it fails:** `401` → token/key invalid or SSWS prefix mishandled. `403` → the service app lacks a required scope; grant it in Okta, not IIQ.

### Task 3 — Group entitlement design

This is where `OKTA_AWS_POWER` gets its governance identity. A group dictionary without documented downstream meaning is just a list of names.

1. Dictionary rows, each with what the group *actually grants*:
   - `OKTA_AWS_POWER` — **critical, non-requestable**: federated power access to Meridian AWS via SAML role mapping; the compensating control for the AWS connector's federation blind spot (Lesson 76, `RR-AWS-SSO-01`).
   - `OKTA_WIRE_USERS` — **critical**: assigns the Wire Portal app; pairs with `WIRE_INIT`/`WIRE_APPR` governance (Lesson 14).
   - `OKTA_ALL_STAFF` — low: baseline tiles (mail, intranet); birthright candidate.
   - `OKTA_CONTRACTORS` — medium: contractor policy scoping; watch for members who also hold critical groups.
2. Rule of thumb, in the binder: *an Okta group is risk-rated by the most powerful thing it assigns, not by its name.*
3. App assignments: where your connector version exposes individual (non-group) app assignments, mark them for review — same finding shape as ServiceNow direct roles and AWS direct policy attachments.

**Expected result:** Four dictionary rows with downstream meaning and risk tiers; the individual-assignment review note.

### Task 4 — Schema and correlation

The schema must carry lifecycle state and groups, or the leaver evidence and the entitlement catalog never materialize.

1. Account schema: `login` (native identity), `email`, `userId` (from the Okta profile), `status`, multi-valued `groups` as the **entitlement attribute**; `appAssignments` too if your version exposes it.
2. Group schema: `name` (native identity), `description`, `type` (Okta distinguishes native groups from app-mastered ones — aggregate both or document why not).
3. Correlation, in documented order: Okta `employeeId` ↔ identity `userId` primary; `login`/`email` ↔ identity `email` fallback. Note the fallback's weakness: emails get rewritten on name changes; associate id doesn't.
4. **Create identities: OFF.** The Task 1 statement, enforced in configuration.

**Expected result:** Schema with `status` and `groups` entitlement; correlation order documented; create-identities disabled.

### Task 5 — Mock inventory (fallback: no live org)

If you have no dev org, simulate the aggregation result so the downstream tasks still work. This is a fallback, not the lesson.

1. Create `~/iiq-lab-data/connectors/okta/MNB-Okta-mock.csv`:

```csv
userName,email,employeeId,groups,status
priya.wire,priya.wire@meridiannb.com,MNB00090,OKTA_WIRE_USERS|OKTA_ALL_STAFF,ACTIVE
jordan.reed,jordan.reed@meridiannb.com,MNB00092,OKTA_AWS_POWER|OKTA_ALL_STAFF,ACTIVE
nina.joiner,nina.joiner@meridiannb.com,,OKTA_ALL_STAFF,ACTIVE
raj.external,raj.external@meridiannb.com,MNB00093,OKTA_CONTRACTORS|OKTA_AWS_POWER,ACTIVE
samir.hassan,samir.hassan@meridiannb.com,MNB00094,,DEPROVISIONED
```

2. Shadow-aggregate via a DelimitedFile app (pipe-split `groups` as the multi-valued entitlement).
3. Read the seeded stories like an analyst: **Jordan** holds `OKTA_AWS_POWER` from the incident — cloud power access the AWS connector can't see; **Raj** is a *contractor* in `OKTA_AWS_POWER` (worse — who approved federation for an external?); **Nina** has a blank `employeeId`, so she correlates only by email — your fallback path exercised, and a data-quality follow-up for the HR-to-Okta flow; **Samir** shows a completed leaver: `DEPROVISIONED`, groups empty.

**Expected result:** Five mock accounts ready to aggregate; four seeded stories written down.

### Task 6 — Account Aggregation

The Task Result is your continuous inventory of who can reach what through the IdP — and the evidence every downstream cert leans on.

1. Tasks → New → Account Aggregation: `MNB-Okta-Account-Aggregation`. Run (live or shadow).
2. Spot-check cubes: `priya.wire` shows `OKTA_WIRE_USERS`; `jordan.reed` and `raj.external` show `OKTA_AWS_POWER`; `samir.hassan` shows `DEPROVISIONED` with no groups; `nina.joiner` correlated via email despite the blank employeeId.
3. Live path: watch for 429s in the task log — pacing, not failure. Schedule nightly, after HR aggregation.

**Expected result:** Task Result success; all spot-checks pass, including Nina's fallback correlation.

**If it fails:** Multi-valued group column not splitting → delimiter config. Live `403` on `/groups` → the `okta.groups.read` scope is missing.

### Task 7 — The leaver: suspend → strip → deprovision, plus the session kill

This is the lesson's centerpiece runbook — and where the dual-rail concept becomes procedure. Walk it end-to-end for a high-risk leaver.

1. Storyboard termination of `jordan.reed` (holder of `OKTA_AWS_POWER`), in order, with reasons:
   1. **Suspend** — instant, reversible login block; new SSO stops within seconds.
   2. **Revoke sessions** (`DELETE /users/{id}/sessions`) — kills existing Okta sessions so open browser tabs can't keep federating; for critical-group holders this runs *with* the suspend, per the Lesson 34 rapid-offboarding drill.
   3. **Remove high-risk groups** (`OKTA_AWS_POWER` first) — produces per-entitlement revoke evidence and guarantees nothing comes back if the account is ever unsuspended.
   4. **Deprovision** once HR confirms the exit is final — the terminal state; app assignments torn down.
   5. **Re-aggregate** — IIQ shows `DEPROVISIONED`, groups empty: the evidence.
2. Then write the **second rail** explicitly: downstream sessions on AWS, Salesforce, ServiceNow, and Google can outlive all of the above, and the SaaS accounts behind the tiles still exist — each target's own leaver pattern (Lessons 71/72/74/76) runs in parallel. One leaver, two rails.
3. SLAs: session revoke + critical group removal within 15 minutes of the HR term event; suspend within the same window; deprovision within 24 hours of HR confirmation.

**Expected result:** Five-step IdP-rail runbook with SLAs, plus the explicit second-rail paragraph.

### Task 8 — SCIM alternate note

The selection matrix lists SCIM 2.0 as the alternate path. Know when you'd take it.

1. Write the decision note: the native Okta connector is preferred (lifecycle operations, sessions, richer schema); a generic SCIM 2.0 integration is the fallback when licensing or version constraints block the native connector, at the cost of Okta-specific operations like session revocation.
2. Cross-reference `lab-data/connectors/scim/Users.json` from Lesson 70 for the SCIM shape.

**Expected result:** Alternate-path decision paragraph.

### Task 9 — Examiner drill and residual risk

*"Show me how a terminated employee loses AWS access granted through your IdP — and prove SSO death actually ended their access."*

1. Write the evidence list: (1) provisioning plan / workflow log showing `OKTA_AWS_POWER` removal and lifecycle operations, (2) post-termination Task Result showing `DEPROVISIONED` and empty groups, (3) the second-rail evidence — the AWS-side leaver artifacts from Lesson 76 — demonstrating you know IdP revoke alone was insufficient.
2. Record `RR-OKTA-AUTHZ-01`: *Okta group names may not match downstream app RBAC 1:1 — certify groups with a business-owner glossary so reviewers know what each group actually grants.* Owner: `helen.ross`.
3. Record `RR-OKTA-RAIL-01`: *Downstream SaaS accounts and sessions survive IdP deprovisioning. Compensating controls: per-target connector leaver patterns (Lessons 71, 72, 74, 76) and session-revocation step in the runbook.* Owner: `kai.nguyen`.

**Expected result:** Evidence list + both residual risks logged with owners.

---

## Acceptance criteria

- [ ] Boundary statement + diagram: HR authoritative, Okta a governed target, auth policy left with the IdP team
- [ ] Real-world setup understood: OAuth service app with `okta.users.read`/`okta.groups.read`, rate limits, key hygiene
- [ ] `MNB-Okta` created; schema carries `status` + `groups` entitlement; create-identities off
- [ ] Group dictionary with downstream meanings; `OKTA_AWS_POWER` documented as critical federated-AWS access
- [ ] Aggregation evidence (live or mock) with the Jordan, Raj, Nina, and Samir stories identified
- [ ] Five-step IdP leaver runbook with session revocation, SLAs, and the second-rail paragraph
- [ ] SCIM alternate note, examiner evidence list, `RR-OKTA-AUTHZ-01` and `RR-OKTA-RAIL-01` recorded

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `401 Unauthorized` on Test Connection | Invalid/expired API token or bad private key; SSWS prefix mishandled | Re-mint or re-vault the credential; prefer moving to the OAuth service app |
| `403` on specific endpoints (e.g. `/groups`) | OAuth service app missing that scope | Grant `okta.groups.read` (or the named scope) on the service app in Okta |
| `429 Too Many Requests` during aggregation | Per-endpoint rate limit hit; budget shared with other integrations | Pace the connector, schedule off-peak, read the `X-Rate-Limit-Reset` header; don't just retry hot |
| Groups aggregate but memberships look incomplete | Group `type` filter excluding app-mastered groups | Include the relevant group types or document the exclusion |
| Okta accounts creating new identity cubes | Application mis-flagged authoritative | Set non-authoritative immediately; this violates the Task 1 boundary — clean up carefully |
| User suspended but still reaching SaaS apps | Existing downstream sessions/tokens; second rail not run | Revoke Okta sessions *and* run each target's leaver pattern — this is `RR-OKTA-RAIL-01` in action |

---

## Training binder evidence

- Boundary statement + diagram
- Real-world setup worksheet (org URL, service app client ID, scopes, rate-limit notes — no keys!)
- Group dictionary with downstream meanings and risk tiers
- Aggregation Task Result + Jordan/Raj/Nina/Samir cube screenshots and findings write-up
- Five-step leaver runbook with SLAs and second-rail paragraph
- Examiner evidence list + `RR-OKTA-AUTHZ-01`, `RR-OKTA-RAIL-01`

---

## Knowledge check

1. Is Okta Meridian's identity source of truth, and what enforces that in the application config?
2. What does membership in `OKTA_AWS_POWER` actually grant, and why can't the AWS IAM connector see it?
3. Which Okta concerns does IIQ deliberately *not* govern, and who owns them?
4. Map SUSPENDED and DEPROVISIONED to leaver semantics — why suspend first?
5. Why does suspending an Okta user not end a leaver's access, and what is the complete answer?
6. Why is an OAuth service app preferred over an SSWS API token for the connector?

### Answers

1. No — `MNB-HR` is authoritative; `MNB-Okta` is non-authoritative with create-identities off, per the Task 1 boundary statement.
2. Federated power access to AWS via SAML role mapping — no IAM user or key exists, so the AWS IAM connector (Lesson 76) is blind to it; governing this group is the compensating control for `RR-AWS-SSO-01`.
3. Sign-on policy, MFA factor enrollment, sessions, and network zones — owned by IdP engineering and reviewed with them, not certified in IIQ.
4. SUSPENDED is an instant, reversible disable (evidence-friendly, safe if the termination reverses); DEPROVISIONED is the terminal state after HR confirms — suspend buys certainty without burning the account.
5. Downstream SaaS accounts and their sessions survive IdP death; the complete answer is the dual-rail leaver — IdP rail (suspend, session revoke, group strip, deprovision) plus every target's own leaver pattern.
6. Scoped grants (`okta.users.read`, `okta.groups.read`) instead of inheriting a whole admin's permissions; vaulted private-key auth instead of a static token that expires on inactivity and leaks broadly if stolen.

---

## Further reading

- [Okta Developer documentation](https://developer.okta.com/docs/) — search "Users API" and "user lifecycle" for the states behind Task 7, and "OAuth 2.0 for Okta APIs" for the service-app model in the Real-world setup.
- [Okta rate limits reference](https://developer.okta.com/docs/reference/rate-limits/) — the per-endpoint budgets your aggregation schedule must respect; explains the 429 + `X-Rate-Limit-*` behavior in the troubleshooting table.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "Okta connector" for the version-specific application guide, supported operations, and featuresString reference.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — field threads on Okta scope errors, rate-limit pacing, and group-type filtering for this connector.
- [NIST SP 800-63B — Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html) — the federation and session-management background behind "IdP revoke ≠ downstream revoke."

---

## Stretch lab

Design (do not deploy) the birthright rule sketch: all employees receive `OKTA_ALL_STAFF` automatically; `OKTA_WIRE_USERS` and `OKTA_AWS_POWER` are requestable only with approval chains ending at `marcus.approve` and `helen.ross` respectively. Then preview Lesson 76's stretch from this side: map `OKTA_AWS_POWER` to the AWS permission sets it ultimately grants, and draft the dual-certification note — the IdP group and the AWS-side privilege reviewed as one logical access, or a revoke on one rail leaves the other alive.

---

## Summary

- Okta is a governed target, never the identity source: IIQ certifies groups and app assignments as entitlements, while auth policy, MFA, and sessions stay with the IdP team — the boundary Lessons 74 and 76 build on.
- `OKTA_AWS_POWER` is a cloud entitlement wearing a group costume: it grants federated AWS power access invisible to the AWS IAM connector, so it is critical-rated, certified, and first to go in a leaver.
- The leaver runs on two rails — suspend → session revoke → group strip → deprovision at the IdP, plus every downstream target's own pattern — because killing SSO does not kill the accounts behind the tiles.

---

**Previous:** [Lesson 72 — ServiceNow Connector](72-servicenow-connector.md)  
**Next:** [Lesson 74 — Google Workspace Connector](74-google-workspace-connector.md)
