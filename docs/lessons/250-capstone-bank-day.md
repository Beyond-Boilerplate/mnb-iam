# Lesson 250 — Capstone: Full Bank Day E2E

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~110 minutes  
**Prereq:** Lessons 201–249  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 50 / 110 / DoD

> **Why (1 line):** If you can run a bank day unassisted, you own the platform.

## What this is

This is the eight-point Enterprise Lab Definition of Done from `docs/ENTERPRISE-LAB-V2.md`, run back-to-back on one fresh identity, with no notes for the optional stretch. You are not learning anything new here — you're proving that everything from Lessons 201–249 composes into one continuous operational day: an HR event becomes accounts, a request becomes approved access, a cert removes something real, and an offboarding kills SSO for good. Treat this like a shift a new Meridian IAM engineer would be handed on day one without a supervisor watching.

This capstone stays a DoD checklist by design — every other lesson in 233–254 was rewritten to the enriched [`_SANDBOX_STYLE.md`](_SANDBOX_STYLE.md) template (Know these / Before you start / Expect / Control note); here the eight numbered DoD blocks below already are that structure at capstone scale, so it isn't re-templated line by line.

## Before you start

- [ ] `./tools/lab/enterprise/e2e-smoke.sh` green before you begin (fix red items first — a capstone on a broken stack proves nothing)
- [ ] Lessons 201–249 objects saved and, where applicable, exported per Lesson 248
- [ ] A brand-new identity name picked (don't reuse a pre-seeded persona)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/250`
- [ ] Uninterrupted block of ~110 minutes (this runs in one sitting)

## Intent

- Confirm the whole stack is healthy before touching anything.
- Run a joiner from HCM through to Portal + Gitea SSO.
- Run a request → multi-step approval → Mailpit proof → provision cycle.
- Run a manager cert with a real revoke that hits a target.
- Run a leaver and prove SSO is dead afterward.
- Export every object you touched and check off all eight DoD criteria with evidence.
- Optionally induce and fix one failure with no notes, to prove operational reflexes.

## Do this

### 0. Preflight (10 min)

1. `./tools/lab/enterprise/e2e-smoke.sh` — every check should PASS (or SKIP only if you're intentionally not running `--enterprise`, which you should be). Fix anything red before proceeding; a capstone run on a broken stack proves nothing.
2. Pick a brand-new identity for this run so nothing is pre-seeded: `./tools/lab/enterprise/hcm-scenario.sh joiner marcy.day Marcy Day marcy.day@meridiannb.com "Commercial Banking"`. Confirm the POST succeeded (`python3 -m json.tool` output shows the new worker).
3. Create a fresh evidence folder: `mkdir -p ~/iiq-lab-evidence/sandbox/250` — every artifact below goes here, one file per numbered DoD item.

### 1. Pass-through login (10 min) — DoD #1

4. In IIQ, confirm `MNB-OpenLDAP` (or `MNB-ActiveDirectory-Live`) is configured as a pass-through login source (Lesson 206). Log out of `spadmin`; log in as `helen.ross` / `LabUser1!` using directory credentials, not the internal IIQ password. Screenshot the successful login and save as `250/01-passthrough-login.png`.

### 2. Joiner → accounts (20 min) — DoD #2

5. Aggregate `MNB-Workday`, then **Refresh Identity Cubes**, so `marcy.day` appears as an IIQ identity correlated to her HCM record.
6. Let `MNB-IdentityTrigger-Joiner` fire `MNB-Workflow-Joiner`; if you added the manager-approval step in Lesson 242, complete that approval as her resolved manager so provisioning proceeds.
7. Run the full aggregation order from Lesson 233's runbook for the remaining targets: OpenLDAP, `MNB-ActiveDirectory-Live`, `MNB-CoreBanking`, `MNB-WirePortal`, `MNB-Salesforce-CRM-Live`, `MNB-Okta`.
8. Open `marcy.day`'s identity cube — confirm links exist on AD/LDAP + IdP + JDBC + Wire per her birthright role for Commercial Banking. Save the **Application Accounts** tab screenshot as `250/02-joiner-accounts.png`.

### 3. Portal + Gitea SSO (15 min) — DoD #3

9. If Keycloak doesn't already have `marcy.day` from realm sync, confirm/create her user in the `meridian` realm (Keycloak admin at `http://localhost:8085`), matching her `MNB-Okta` correlation key.
10. Log into the Employee Portal at `http://localhost:8092` as `marcy.day` via Keycloak SSO. Screenshot the authenticated portal session.
11. Log into Gitea at `http://localhost:8093` the same way (OIDC via the `gitea` Keycloak client). Screenshot the authenticated Gitea session. Save both as `250/03-portal-sso.png` and `250/03-gitea-sso.png`.
12. Confirm Wire access is visible/usable for her only if her birthright includes it (Commercial Banking should include Wire-initiator-adjacent access, not approver — check against the SOD constraint from `MNB-SOD-Wire-DualControl`).

### 4. Request → approval → Mailpit → provision (20 min) — DoD #4

13. As `marcy.day`, submit an Access Request for one CRM or Wire entitlement she doesn't already have, with a justification over 20 characters (Lesson 243's validation will block anything shorter). Note the `IdentityRequest` id.
14. Confirm the multi-step approval routes to her manager then the app owner (Lesson 222's pattern via `MNB-Workflow-Access-Approval`).
15. Check Mailpit (`http://localhost:8025`) for the launch/assignment mail. Approve as manager, then as app owner.
16. Confirm the entitlement provisioned on the real target (curl the CRM/Wire endpoint or check her identity cube's Entitlements tab). Save the IdentityRequest screenshot, the Mailpit thread, and the target proof as `250/04-request-approval-*.png`.

### 5. Manager + app-owner certs (20 min) — DoD #6

17. Launch a manager cert scoped to `marcy.day`'s manager's org (Lesson 226's pattern) — decide at least one revoke against her or a peer.
18. Launch an app-owner cert against the app whose entitlement you just granted in step 13–16 (Lesson 227's pattern) — decide a revoke there too.
19. Confirm both revokes hit their targets (Provisioning Transactions + a live curl/psql/ldapsearch check, Lesson 229's pattern). Save both cert completions and the target proofs as `250/05-certs-*.png`.

### 6. Leaver → SSO dead (15 min) — DoD #5

20. Run the leaver: `./tools/lab/enterprise/hcm-scenario.sh leaver marcy.day`. Aggregate `MNB-Workday`, let `MNB-IdentityTrigger-Leaver`/`MNB-Workflow-Leaver` disable her accounts across AD/LDAP/JDBC/IdP.
21. Attempt to log into the Employee Portal and Gitea again as `marcy.day` — both must now fail (Keycloak account disabled or IdP link removed). Screenshot both failed login attempts as `250/06-leaver-sso-dead-*.png`.
22. Confirm residual access via a quick targeted cert or the leaver's residual-entitlement report catches anything not auto-disabled (e.g. a manual-fulfillment ITSM entitlement from Lesson 239) and remediate it.

### 7. SSD export + smoke (15 min) — DoD #7

23. Export any object you touched freshly during this capstone (e.g. a new IdentityRequest-driven `ManagedAttribute`, or a workflow tweak if you made one) into `config/`, run `./build.sh importdynamic`, and `git diff -- config/` to confirm real content.
24. Re-run `./tools/lab/enterprise/e2e-smoke.sh` and `./tools/lab/enterprise/contract-tests.sh` — confirm both are green after your whole capstone run.

### 8. Toolkit/MCP smoke (5 min) — DoD #8

25. `curl -s -u spadmin:admin http://localhost:8080/identityiq/plugin/rest/mnbToolkit/enterprise/jml?identity=marcy.day | python3 -m json.tool` — confirm `inactive:true` and her link list reflects the leaver state.
26. Through your MCP client, call `list_agent_work_items` and confirm no orphaned work items remain open for `marcy.day`.

### Optional stretch (no notes)

27. Without referring back to any earlier lesson, induce one failure (bad connector credential, malformed plan, wrong root path — Lesson 230/237's categories) somewhere in the stack and fix it end-to-end from the raw error text alone.

## If it fails

- **Any preflight smoke check fails** → fix the stack before starting; a capstone run against a partially-up estate will fail in ways that look like your mistakes but are actually infrastructure.
- **Joiner never correlates** → check the aggregation order (Lesson 233) — HCM/Refresh must run before any target aggregation.
- **Portal/Gitea SSO fails for a new joiner** → Keycloak realm sync may not auto-create users; confirm/create her manually per Lesson 211/213 before blaming the IdP.
- **Leaver doesn't kill SSO** → confirm the leaver workflow actually disables the Keycloak-linked account (`MNB-Okta`), not just the directory accounts — Portal/Gitea auth depends specifically on that link.
- **Any DoD item can't be proven** → don't skip it; go back to the specific lesson (226–229 for certs, 217–219 for JML, 222 for approvals) and redo the missing piece before checking it off.

## You are done when

All eight Enterprise Lab DoD criteria from `docs/ENTERPRISE-LAB-V2.md` pass with saved evidence under `~/iiq-lab-evidence/sandbox/250/`, run on one identity end-to-end in a single sitting.

## Control note

- **Control:** End-to-end operational readiness sign-off (JML + request + cert + SSO + config-as-code, one identity, one sitting).  
- **Owner:** IAM Engineering lead / capstone reviewer.  
- **SLA (lab):** All eight DoD items evidenced same session; no item skipped or deferred.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/250/01`–`08` per the numbered blocks above.

## Navigate

- Previous: Lesson 249
- Next: Lesson 251 (v3 add-ons: workstation, Entra, intranet, password)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
