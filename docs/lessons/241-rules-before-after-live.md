# Lesson 241 — Before/After Provisioning Rules

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~75 minutes  
**Prereq:** Lesson 230  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 89 / 91

> **Why (1–2 lines):** Rules encode policy the connector UI cannot — department guards and compliance notify hooks. Prove where dual-control is enforced besides the SoD scan (224), or connector UI gaps become silent policy bypasses.

## What this is

Provisioning Policy tabs map attributes; they can’t say “reject this plan if the identity isn’t Treasury-eligible” or “email compliance after every successful wire-role grant.” `BeforeProvisioning` / `AfterProvisioning` Rules are BeanShell/Java hooks around the `ProvisioningPlan` for a connector. Classic 89 catalogs rule types; 91 is Before/After depth. Repo ships `Rule/MNB-Rule-HelloWorld.xml` as smoke — you author live rules on `MNB-WirePortal`, aligned with SoD dual-control.

## Know these

| Rule type (sample) | When it runs | This lesson |
| --- | --- | --- |
| BeforeProvisioning | Immediately before connector call | Dept guard — reject bad wire grants |
| AfterProvisioning | After successful connector work | Mailpit notify on wire grant |
| IdentityAttribute / others | Aggregation / refresh pipelines | Stretch later — don’t boil the ocean |

```text
Access request / role assign → plan
  → BeforeProvisioning (may throw → block)
  → connector
  → AfterProvisioning (side effects: email, ticket)
```

**Wrong way:** Putting SoD-only trust in a nightly scan while connectors happily provision both wire powers with no Before guard.

## Intent

- Write Before rule rejecting ineligible wire-role grants.
- Prove a violating plan blocks with your message.
- Write After rule emailing Mailpit on successful wire grant.
- Export both rules under `config/Rule/` cleanly.

## Before you start

- [ ] `MNB-WirePortal` aggregates/provisions (Lesson 209 / 230)
- [ ] Mailpit proven (203)
- [ ] Know an ineligible dept identity vs `priya.wire` / `marcus.approve`
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/241`

## Do this

1. **Setup → Business Rules → New Rule** type `BeforeProvisioning`, name `MNB-Rule-Wire-Dept-Guard`. Inspect `plan` for AttributeRequests granting wire initiator/approver roles; if identity `department` ∉ `{Treasury & Payments, Commercial Banking}`, throw `GeneralException` with `"Wire role denied: <identity> is not in an eligible department"`.  
   **Expect:** Rule saves; logic reviews plan + identity attrs.

2. Attach as `MNB-WirePortal` **Before Provisioning Rule**.  
   **Expect:** Application shows the rule name in the rules slot (not only “Before Operation” if your build distinguishes them).

3. Trigger a violating plan: assign `MNB-Bundle-Wire-Initiator` to a Technology Platforms (or other ineligible) identity.  
   **Expect:** Request/PT fails; error carries your message (UI or Task Result / server log).

4. Confirm in **Provisioning Transactions** or workflow error step.  
   **Expect:** Blocked before connector success — no new wire entitlement on target.

5. **New Rule** type `AfterProvisioning`, name `MNB-Rule-Wire-Notify`. On successful wire-role grant, send email (subject `Wire role granted: $identity.name`) to any `@meridiannb.com` address (Mailpit catches all). Attach as After Provisioning Rule on `MNB-WirePortal`.  
   **Expect:** Rule attached.

6. Legitimate grant: `priya.wire` or `marcus.approve` (eligible departments).  
   **Expect:** Provisioning succeeds.

7. Mailpit `http://localhost:8025` — After-rule mail with correct identity.  
   **Expect:** Subject/body identify the grant.

8. Export clean XML to `config/Rule/MNB-Rule-Wire-Dept-Guard.xml` and `config/Rule/MNB-Rule-Wire-Notify.xml` (strip internal ids per `config/README.md`).  
   **Expect:** Files re-importable.

9. Save blocked error text + Mailpit screenshot under `~/iiq-lab-evidence/sandbox/241/`.  
   **Expect:** Evidence pack complete.

## If it fails

- **Before never fires** — wrong rule slot; plan routed via another connector/role path.
- **Generic UI error only** — full text in Task Results / `docker logs mnb-identityiq`.
- **After fires, no mail** — use Lab SMTP (`mailpit:1025`), don’t hardcode another host.
- **Export re-import errors** — strip `id` / `created` / `modified` noise.

## You are done when

Before rule blocks an ineligible wire grant with your message; After rule emails Mailpit on a legitimate grant; both exported under `config/Rule/`.

## Control note

- **Control:** Connector-layer policy enforcement + privileged-grant notification.  
- **Owner:** IAM Engineering.  
- **SLA (lab):** Block same request; notify within seconds via Mailpit.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/241/` + `config/Rule/*.xml`.

## Quick check

1. Before vs After — which can stop the connector call? → BeforeProvisioning.  
2. Name one rule type not built in this lesson. → IdentityAttribute (or any from classic 89 catalog).  
3. Why export to `config/Rule/`? → SSD promote / repeatable lab (248).

## Navigate

- Previous: Lesson 240  
- Next: Lesson 242  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
