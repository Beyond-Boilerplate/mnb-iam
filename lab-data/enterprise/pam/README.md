# Meridian PAM Lab — privileged vault

**Not a real CyberArk.** HashiCorp Vault stores secrets; `mnb-pam-lab` provides CyberArk-shaped **safes**, **checkout/check-in**, **session recording stubs**, and SCIM membership for IIQ.

| | |
| --- | --- |
| Vault UI | http://localhost:8200/ui |
| Lab root token | `mnb-lab-vault-root` (**lab only** — never for production) |
| PAM API / UI | http://localhost:8097/ |
| IIQ app | `MNB-PAM-CyberArk` → `http://pam-lab:8097/scim/v2` |

## Safes (seeded)

| Safe | Purpose |
| --- | --- |
| `MNB-Safe-DomainAdmin` | Shared Domain Admin |
| `MNB-Safe-CloudBreakGlass` | Emergency cloud admin |
| `MNB-Safe-PaymentSwitch` | Payment switch root |
| `MNB-Safe-SharedRoot` | Bastion shared root |

Seed file: [`safes.json`](safes.json) (lab placeholder passwords — rotate mentally; do not treat as production).

## Correct path (Lesson 86 / 255)

1. IIQ BreakGlass / privileged **request** with `INC-…` justification → approval (Security).
2. Provision **safe membership** (`POST /memberships` or connector entitlement `SAFE:MNB-Safe-CloudBreakGlass`).
3. Operator **checkout** with incident id → password returned once; session recording stub starts.
4. **Check-in** when done; membership removed on leaver / sunset.

Wrong path: Slack DM, shared 1Password vault in chat, spreadsheet on jump host.

## API quick ref

```bash
curl -s http://localhost:8097/safes | python3 -m json.tool
curl -s -X POST http://localhost:8097/memberships \
  -H 'Content-Type: application/json' \
  -d '{"user":"jordan.reed","safe":"MNB-Safe-CloudBreakGlass","op":"add"}'
curl -s -X POST http://localhost:8097/checkout \
  -H 'Content-Type: application/json' \
  -d '{"safe":"MNB-Safe-CloudBreakGlass","account":"cloud-breakglass","requestedBy":"jordan.reed","incidentId":"INC-LAB-001","ttlMinutes":30}'
curl -s http://localhost:8097/sessions | python3 -m json.tool
```

Do not paste checkout passwords into tickets, git, or screenshots.
