# Lesson 219 — Leaver LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 31 / 34

> **Why:** A leaver is only done when SSO fails and accounts are disabled everywhere — a Terminated badge alone is a paper trail, not security. Prove disable on directory and IdP, not just IIQ status.

## What this is

`MNB-IdentityTrigger-Leaver` (`type="attributeChange"`) launches `MNB-Workflow-Leaver`, which refreshes the identity with `provision=true` and `disable=true` — a disable plan across linked applications.

Classic 31/34 taught rapid offboarding; here you prove lockout on live surfaces (LDAP, Keycloak/Portal, optionally Gitea).

Multi-store reality: disabling OpenLDAP does **not** automatically disable Keycloak unless IIQ provisions the IdP (`MNB-Okta`) or you close that hop manually — that gap is a real finding.

## Know these

```text
HCM PATCH active=false / Terminated
  → Aggregate Workday → cube inactive/status flip
  → Leaver trigger → MNB-Workflow-Leaver
  → disable plan → directories / apps
  → IdP disable (auto or manual) → Portal SSO must fail
```

| Surface | How you prove disable |
| --- | --- |
| OpenLDAP / Samba | `ldapsearch` / failed pass-through (Lesson 206) |
| Keycloak | User Enabled = false |
| Portal / Gitea | Login attempt **fails** |

- **Wrong way:** Marking inactive in IIQ Debug without HCM termination — no source-of-truth trail, and the leaver trigger may never fire.

## Intent

- Use a disposable identity only (never Helen/Priya).
- Terminate via live HCM; exercise leaver workflow (auto or manual).
- Prove disable on ≥1 directory and failed Portal login.
- Record Mailpit termination mail presence or honest gap.

## Before you start

- [ ] Disposable cube with LDAP account + Portal login (reuse `lab.joiner1` or create `lab.leaver1`)
- [ ] Confirm Portal login works **before** terminate (baseline)
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/219
```

## Do this

### Task 1 — Ensure a disposable identity exists

Reuse Lesson 217’s joiner, or create a fresh one:

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.leaver1 Lab Leaver \
  lab.leaver1@meridiannb.com 'Bank Operations'
```

Then aggregate / refresh / Keycloak / Portal steps as in Lesson 217 until Portal login works.

- **Why:** shared personas break later certs and SSO lessons — never terminate Helen.
- **Expect:** Portal login succeeds for the disposable user before you proceed.

### Task 2 — Capture the “before” baseline

Sign into Employee Portal as the disposable user. Screenshot under evidence (no passwords).

- **Why:** without a working baseline, a failed post-terminate login proves nothing.
- **Expect:** successful login proof saved.

### Task 3 — Terminate in live HCM

```bash
./tools/lab/enterprise/hcm-scenario.sh leaver lab.leaver1
```

(`PATCH` sets `active: false`, `status: Terminated`.)

- **Why:** leavers must start at the authoritative source — same as production HR terminate.
- **Expect:** script success.

### Task 4 — Confirm the source

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.leaver1 \
  | python3 -m json.tool | grep -E 'active|status'
```

- **Why:** ground truth before IIQ — wrong worker id here terminates the wrong person.
- **Expect:** `active: false`, status Terminated.

### Task 5 — Aggregate Workday and promote

Run **Account Aggregation** on `MNB-Workday`, then Identity Refresh with attribute promotion.

- **Why:** cube inactive/status flip is the `attributeChange` the Leaver trigger watches.
- **Expect:** cube shows inactive / Terminated.

### Task 6 — Confirm leaver workflow

Check Task Results for `MNB-Workflow-Leaver`, or:

```bash
docker logs mnb-identityiq 2>&1 | grep -i "MNB Leaver workflow"
```

If missing, launch manually with `identityName=lab.leaver1`.

- **Why:** auto-fire is preferred; manual launch still completes the disable plan.
- **Expect:** workflow ran; disable provisioning attempted.

### Task 7 — Directory proof

Prove disable on OpenLDAP (or Samba):

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b ou=people,dc=meridiannb,dc=com \
  -D cn=admin,dc=meridiannb,dc=com -w admin \
  '(uid=lab.leaver1)'
```

Look for a disabled flag / account status — **or** attempt pass-through login (Lesson 206) as that user and confirm it fails.

- **Why:** IIQ “disabled” without a directory change leaves residual bind access.
- **Expect:** observable disable or failed directory login.

### Task 8 — Keycloak / IdP disable

Admin → Users → disposable user — confirm **Enabled** = false. If IIQ isn’t provisioning IdP yet, disable manually and note it.

- **Why:** Portal authenticates against Keycloak — LDAP disable alone does not kill SSO.
- **Expect:** IdP cannot authenticate; note whether disable was auto or manual (multi-store finding).

### Task 9 — Portal login must fail

Attempt Employee Portal login as the leaver.

- **Why:** this is the acceptance test — Terminated badge without failed SSO is incomplete.
- **Expect:** **login fails**. If it succeeds, trace HCM → cube → plan → target until you find the open hop — that gap *is* the lesson outcome.

### Task 10 — Mailpit termination notice

Check [http://localhost:8025](http://localhost:8025).

- **Why:** termination mail may be missing from the workflow XML — honest gap, not an SMTP bug.
- **Expect:** mail present, or note “leaver workflow has no email step.”

## If it fails

| Symptom | Fix |
| --- | --- |
| Trigger never fires | Watched attribute/filter may not match `inactive` — name the attribute in the trigger or use manual launch |
| Plan computes, no target disable | Refresh without effective `provision`, or app lacks disable/ENABLE features |
| LDAP disabled, Portal still works | Keycloak is separate — disable IdP or wire `MNB-Okta` provisioning |
| Wrong identity terminated | `hcm-scenario.sh leaver` arg must match the disposable user, not Helen/Priya |
| No mail | Known limitation if workflow has no email step — don’t debug SMTP for that gap alone |

## You are done when

- [ ] Disposable identity disabled on at least one directory (raw proof)
- [ ] Portal login as the leaver **fails**
- [ ] You can name any remaining hop where access still works

## Control note

- **Control:** Leaver / rapid offboarding (terminate → disable all surfaces)
- **Owners:** HR Ops + IAM Ops + IdP owner
- **SLA (lab):** same session; production often same-day / hours for privileged
- **Evidence:** `~/iiq-lab-evidence/sandbox/219/` — HCM PATCH proof, ldap/IdP disable, failed Portal attempt

## Quick check

1. Does LDAP disable alone kill Portal SSO? → no — Keycloak is a separate store unless provisioned
2. What IIQ flags drive disable plans? → `disable=true` with `provision=true` on refresh
3. Why use a disposable identity? → shared personas break later certs/SSO lessons

## Feedback

Could you name every store that must be disabled for SSO to fail? If Portal still worked after LDAP disable, that multi-store gap is the finding — write it down before moving on.

## Navigate

- Previous: [Lesson 218](218-mover-lcm-live.md)
- Next: [Lesson 220](220-contractor-loa-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
