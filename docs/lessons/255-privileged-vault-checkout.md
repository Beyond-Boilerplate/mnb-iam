# Lesson 255 — Privileged Vault Checkout (Break-Glass → PAM)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lessons 223, 251  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 37 / 86

> **Why (1–2 lines):** Shared root, Domain Admin, cloud break-glass, and payment-switch passwords belong in a vault with checkout controls — not tickets, chat, or a spreadsheet on a jump host. When `jordan.reed` needs emergency cloud admin, the path is time-bound BreakGlass → safe membership → checkout with INC — not a Slack DM.

## What this is

**HashiCorp Vault** (`:8200`) stores secrets; **mnb-pam-lab** (`:8097`) is a CyberArk-shaped facade (safes, membership, checkout/check-in, session recording stubs). IIQ owns request/approval (`MNB-Bundle-BreakGlass-Cloud`); PAM owns credential custody. Not licensed CyberArk PVWA/PSM video — same Lesson 86 control narrative on the local stack.

## Know these

| Object | Role |
| --- | --- |
| Safe | Boundary for privileged accounts (DomainAdmin, CloudBreakGlass, PaymentSwitch, SharedRoot) |
| Membership | Who may checkout — provisioned after BreakGlass approval |
| Checkout | Time-bound secret retrieval + session recording stub |
| Check-in | End session; rotate narrative in production |

```text
IIQ BreakGlass + INC → approval (Security)
  → POST /memberships (safe add)
  → POST /checkout (password once; audit without secret)
  → POST /checkin → remove membership on sunset
```

**Wrong way:** Standing shared password in team chat / jump-host spreadsheet. **Dual failure:** IIQ role without vault (theater) or vault access without IIQ request (invisible privilege).

## Intent

- Confirm Vault + pam-lab healthy; list Meridian safes.
- Add `jordan.reed` to CloudBreakGlass only after INC-tagged path.
- Prove non-members get 403; member checkout + check-in with session audit (no passwords in evidence).
- Optional: aggregate `MNB-PAM-CyberArk` SCIM for `SAFE:*` entitlements.

## Before you start

- [ ] `curl -sf http://127.0.0.1:8097/health` and Vault seal-status on `:8200`
- [ ] Lesson 223 BreakGlass pattern or seeded `MNB-Bundle-BreakGlass-Cloud`
- [ ] Read [`lab-data/enterprise/pam/README.md`](../../lab-data/enterprise/pam/README.md)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/255` (never store checkout passwords)

## Do this

1. Health:  
   `curl -sf http://127.0.0.1:8097/health | python3 -m json.tool`  
   `curl -sf http://127.0.0.1:8200/v1/sys/seal-status | python3 -m json.tool`  
   Open http://localhost:8097/ and Vault UI http://localhost:8200/ui (token `mnb-lab-vault-root` — lab only).  
   **Expect:** `vaultReachable: true`; Vault unsealed.

2. `curl -sf http://localhost:8097/safes | python3 -m json.tool`  
   **Expect:** DomainAdmin, CloudBreakGlass, PaymentSwitch, SharedRoot.

3. Skim pam README wrong-path paragraph (Slack / spreadsheet).  
   **Expect:** You can state why those fail ops scrutiny (no checkout trail, shared standing privilege, no time-bound reclaim).

4. After simulated BreakGlass approval with `INC-LAB-001`, add membership:  
   `curl -sf -X POST http://localhost:8097/memberships -H 'Content-Type: application/json' -d '{"user":"jordan.reed","safe":"MNB-Safe-CloudBreakGlass","op":"add"}'`  
   **Expect:** JSON lists CloudBreakGlass under jordan.reed.

5. Deny-before-grant:  
   `curl -s -X POST http://localhost:8097/checkout -H 'Content-Type: application/json' -d '{"safe":"MNB-Safe-CloudBreakGlass","account":"cloud-breakglass","requestedBy":"priya.wire","incidentId":"INC-LAB-001","ttlMinutes":15}'`  
   **Expect:** HTTP 403 `not_a_safe_member`.

6. Checkout as jordan.reed with INC (same payload, `requestedBy":"jordan.reed"`). Note `checkoutId`. **Do not** screenshot or commit the password field.  
   **Expect:** 201 with `incidentId`, TTL, `sessionRecording: true`.

7. `curl -sf http://localhost:8097/sessions | python3 -m json.tool | head -40`  
   **Expect:** Checkout event with `recording: started` and INC; **no** password fields in the log.

8. Check in: `curl -sf -X POST http://localhost:8097/checkin -H 'Content-Type: application/json' -d '{"checkoutId":"<id>"}'`  
   **Expect:** `status: checked_in`; sessions show `recording: closed`.

9. Optional IIQ: aggregate `MNB-PAM-CyberArk` (`http://pam-lab:8097`, SCIM `/scim/v2`) — `SAFE:MNB-Safe-CloudBreakGlass` entitlements for members.  
   **Expect:** SCIM Users list includes jordan.reed while membership active.

10. Remove membership when incident ends:  
    `curl -sf -X POST http://localhost:8097/memberships -H 'Content-Type: application/json' -d '{"user":"jordan.reed","safe":"MNB-Safe-CloudBreakGlass","op":"remove"}'`  
    **Expect:** Safe removed from user; further checkout as jordan.reed → 403.

## If it fails

- **Vault / pam-lab unhealthy** —  
  `docker compose -f docker-compose.iiq.yml -f docker-compose.enterprise.yml --profile enterprise up -d --build vault pam-lab`
- **403 after add** — username spelling; membership POST body `user` + `safe`.
- **409 already_checked_out** — check in prior checkout.
- **Expecting PSM video** — recording is a stub audit event, not CyberArk PSM.

## You are done when

Non-members cannot checkout; INC-tagged member can checkout and check in; `/sessions` audits without secrets; you can explain IIQ-without-vault vs vault-without-IIQ dual failure.

## Control note

- **Control:** Privileged credential custody (PAM checkout) + BreakGlass request.  
- **Owners:** Security (approval) + PAM Ops (safes) + IAM (role/membership).  
- **SLA (lab):** Membership add minutes after approval; checkout TTL short (15–60 min).  
- **Evidence:** `~/iiq-lab-evidence/sandbox/255/` — 403 response, sessions JSON (redacted), membership add/remove — **never** passwords.

## Quick check

1. Who stores the password — IIQ or Vault? → Vault (via pam-lab).  
2. What must ride on every checkout? → Incident id.  
3. Name the dual failure. → Role without vault / vault without request trail.

## Navigate

- Previous: Lesson 254  
- Next: —  
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · PAM: [pam/README.md](../../lab-data/enterprise/pam/README.md) · Classic: [86](86-pam-cyberark-module.md)
