# Lesson 221 — Build a Live Request Catalog

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~55 minutes  
**Prereq:** Lesson 216  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 35

> **Why (1–2 lines):** A request catalog is only honest if every entitlement in it actually provisions on a live target when granted — not a list of things that were never wired end to end.

## What this is

`MNB-QuickLink-Request-Access` is the pack's self-service entry point — a `QuickLink` with `action="external"` pointing at `accessRequest.jsf`, scoped to the `Self Service` `DynamicScope` (`allowSelf="true"`). What shows up *inside* that page depends entirely on which Bundles/entitlements are flagged `requestable`. Everything you add here must already provision for real: `MNB-Bundle-Wire-Initiator` (Lesson 216, provisions `WIRE_INIT`) and CRM access (Lesson 210) — because Lesson 222 depends on the request you submit here being genuinely fulfillable.

## Know these

```text
Self Service DynamicScope → Request Access QuickLink
  → catalog = requestable Bundles/entitlements
  → submit → IdentityRequest (pending, no approver yet — Lesson 222 wires that)
```

| Catalog item | Backing object | Live proof it's real |
| --- | --- | --- |
| Wire Initiator | `MNB-Bundle-Wire-Initiator` | `WIRE_INIT` on Lesson 216's target |
| CRM access | `MNB-Salesforce-CRM-Live` managed group | `CRM-Users` (Lesson 210) |

**Wrong way:** Flagging something requestable that was never provisioning-tested — the catalog looks complete and grants nothing.

## Intent

- Confirm the Request Access QuickLink is visible and scoped correctly for a normal persona.
- Make at least two real, live-provisioning entitlements requestable.
- Submit a real Access Request with a justification and capture the `IdentityRequest` id.
- Leave it unapproved on purpose so Lesson 222 has something real to approve.

## Before you start

- [ ] Lesson 216 wire birthright/request role provisions on a live target
- [ ] Lesson 210 CRM `CRM-Users` group aggregated
- [ ] `priya.wire` pass-through login works (Lesson 206 pattern)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/221`

## Do this

1. Log in as `helen.ross` and confirm **Request Access** appears on her home page/menu.  
   **Expect:** QuickLink visible — proves `Self Service` scope includes a normal workforce persona, not just admins.

2. Confirm `MNB-Bundle-Wire-Initiator` is `requestable=true` and appears searching "wire" in the catalog.  
   **Expect:** Role listed with a description, not hidden/owner-only.

3. Make CRM access requestable: flag `MNB-Salesforce-CRM-Live`'s `CRM-Users` managed entitlement requestable in the Entitlement Catalog, or wrap it in a small requestable Bundle if your build prefers role-based requests.  
   **Expect:** CRM item now searchable in the catalog.

4. Optional: if Gitea SSO (Lesson 213) is live, create a lightweight requestable Bundle mapped to the relevant Keycloak group as a third catalog item.  
   **Expect:** Third item searchable — a test that your catalog design generalizes past the two pre-wired apps.

5. Log out; log in as `priya.wire` / `LabUser1!`. Open **Request Access**, search "wire", select `MNB-Bundle-Wire-Initiator`, add justification ("Onboarding to wire desk per manager Sanjay Kapoor — Q3 rotation"). Submit.  
   **Expect:** Request accepted; no auto-grant.

6. Note the resulting `IdentityRequest` id shown by the UI.  
   **Expect:** Id written down — needed again in Lesson 222.

7. Do **not** approve or self-provision this request yet, even as spadmin.  
   **Expect:** Request sits pending — Lesson 222 is built around approving *this* one.

8. Confirm a real pending approval work item exists: spadmin's **Manage Work Items**, or Sanjay Kapoor's (`MNB00006`) queue if you know it.  
   **Expect:** An addressable work item — proof the request is live, not just logged.

## If it fails

- **Request Access QuickLink missing for Priya** — check the `Self Service` DynamicScope population/capability actually includes her; compare against Helen, already confirmed.
- **Wire role doesn't appear in search** — `requestable=true` alone may not be enough; confirm it isn't scoped hidden/owner-only.
- **CRM entitlement can't be flagged requestable** — some builds only allow entitlement requests via a `ManagedAttribute` with request options enabled; wrap it in a small IT Bundle instead.
- **Submission errors out** — check for a missing required provisioning-forms field (e.g. `MNB-OpenLDAP`'s account-create form fields, Lesson 204) not populated on the request form.
- **No approval work item appears anywhere** — the request may have auto-approved with no workflow wired; useful information for Lesson 222, which needs `MNB-Workflow-Access-Approval` attached before that lesson's chain has anything to do.

## You are done when

At least two live-provisioning entitlements are genuinely requestable, Priya has submitted a real Access Request for wire initiate with justification, and you have the exact `IdentityRequest` id for Lesson 222.

## Control note

- **Control:** Self-service access request catalog integrity.  
- **Owner:** IAM Ops (catalog curation) + app owners (entitlement scope).  
- **SLA (lab):** Same session; production catalogs are reviewed on a recurring cadence to prune non-provisioning items.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/221/` — catalog screenshots, `IdentityRequest` id, pending work item proof.

## Quick check

1. Why must every catalog item already provision for real? → Lesson 222 depends on this exact request being fulfillable.  
2. What scope controls who sees Request Access? → The `Self Service` `DynamicScope`.  
3. Why leave the request unapproved here? → So Lesson 222 has a live approval to work.

## Navigate

- Previous: Lesson 220  
- Next: Lesson 222  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
