# Lesson 219 — Leaver LCM End-to-End

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~70 minutes  
**Prereq:** Lesson 217  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 31 / 34

> **Why (1–2 lines):** A leaver is only done when SSO fails and accounts are disabled everywhere — a Terminated badge alone is a paper trail, not security. Examiners ask for disable evidence on directory and IdP, not just IIQ status.

## What this is

`MNB-IdentityTrigger-Leaver` (`type="attributeChange"`) launches `MNB-Workflow-Leaver`, which `refreshIdentity`s with `provision=true` and `disable=true` — a disable plan across linked applications. Classic 31/34 taught rapid offboarding; here you prove lockout on live surfaces (LDAP, Keycloak/Portal, optionally Gitea). Multi-store reality: disabling OpenLDAP does **not** automatically disable Keycloak unless IIQ provisions the IdP (`MNB-Okta`) or you close that hop manually — that gap is a real finding.

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
| OpenLDAP / Samba | `ldapsearch` / failed pass-through (206) |
| Keycloak | User Enabled = false |
| Portal / Gitea | Login attempt fails |

**Wrong way:** Marking inactive in IIQ Debug without HCM termination — no source-of-truth trail and leaver trigger may never fire.

## Intent

- Use a disposable identity only.
- Terminate via live HCM; exercise leaver workflow (auto or manual).
- Prove disable on ≥1 directory and failed Portal login.
- Record Mailpit termination mail presence or honest gap.

## Before you start

- [ ] Disposable cube with LDAP account + Portal login (reuse `lab.joiner1` or create `lab.leaver1`)
- [ ] Confirm Portal login works **before** terminate (baseline)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/219`

## Do this

1. Ensure disposable identity exists with accounts: reuse Lesson 217 joiner or  
   `./tools/lab/enterprise/hcm-scenario.sh joiner lab.leaver1 Lab Leaver lab.leaver1@meridiannb.com 'Bank Operations'`  
   then aggregate/refresh/Keycloak steps as in 217.  
   **Expect:** Portal login succeeds before you proceed.

2. Capture “before” — Portal login as the disposable user.  
   **Expect:** Baseline proof in evidence (screenshot without password).

3. Terminate: `./tools/lab/enterprise/hcm-scenario.sh leaver lab.leaver1`  
   (`PATCH` `{"active": false, "status": "Terminated"}`).  
   **Expect:** Script success.

4. Confirm source: `curl -s http://localhost:8091/hcm/v1/workers/lab.leaver1 | python3 -m json.tool | grep -E 'active|status'`.  
   **Expect:** `active: false`, status Terminated.

5. Aggregate `MNB-Workday` + Identity Refresh (attribute promote).  
   **Expect:** Cube inactive/status flipped — attributeChange the Leaver trigger watches.

6. Confirm `MNB-Workflow-Leaver`: Task Result or  
   `docker logs mnb-identityiq 2>&1 | grep -i "MNB Leaver workflow"`.  
   If missing, launch manually with `identityName=lab.leaver1`.  
   **Expect:** Workflow ran; disable provisioning attempted.

7. Directory proof: `ldapsearch` for `uid=lab.leaver1` (disabled flag / account status) **or** pass-through login (206) as that user must fail.  
   **Expect:** Observable disable or failed bind/login on directory path.

8. Keycloak: Admin → Users → disposable user — confirm Enabled false, or disable manually if IIQ isn’t provisioning IdP yet.  
   **Expect:** IdP cannot authenticate; note whether this was auto or manual (multi-IdP finding).

9. Attempt Employee Portal login as the leaver.  
   **Expect:** **Must fail.** If it succeeds, trace HCM → cube → plan → target until you find the open hop — that gap *is* the lesson outcome.

10. Mailpit for termination notice.  
    **Expect:** Mail, or honest “leaver workflow has no email step” note (compare XML step list).

## If it fails

- **Trigger never fires** — watched attribute/filter may not match `inactive`; name the attribute in the trigger or use manual launch.
- **Plan computes, no target disable** — refresh without effective `provision`; or app `featuresString` lacks disable/ENABLE features.
- **LDAP disabled, Portal still works** — Keycloak is separate; disable IdP or wire `MNB-Okta` provisioning.
- **Wrong identity terminated** — `hcm-scenario.sh leaver` arg must match disposable user, not Helen/Priya.
- **No mail** — known limitation if workflow has no email step; don’t debug SMTP for that gap alone.

## You are done when

Disposable identity is disabled on at least one directory (raw proof) and fails Portal login; you can name any remaining hop where access still works.

## Control note

- **Control:** Leaver / rapid offboarding (terminate → disable all surfaces).  
- **Owners:** HR Ops + IAM Ops + IdP owner.  
- **SLA (lab):** Same session; production often same-day / hours for privileged.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/219/` — HCM PATCH proof, ldap/IdP disable, failed Portal attempt.

## Quick check

1. Does LDAP disable alone kill Portal SSO? → No — Keycloak is a separate store unless provisioned.  
2. What IIQ workflow flag drives disable plans? → `disable=true` with `provision=true` on refresh.  
3. Why use a disposable identity? → Shared personas break later certs/SSO lessons.

## Navigate

- Previous: Lesson 218  
- Next: Lesson 220  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
