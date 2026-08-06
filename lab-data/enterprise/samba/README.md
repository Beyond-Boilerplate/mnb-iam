# Meridian Samba AD (Corporate AD stand-in) for Enterprise Lab v2
#
# IIQ connects via LDAP on host port 3890 (container 389).
# IQService / AD Direct password ops are OUT OF SCOPE — see docs/ENTERPRISE-LAB-V2.md
#
# Domain: MERIDIANNB.COM / meridiannb.com
# Admin: Administrator / Password1!  (lab only)
# Bind for IIQ: CN=Administrator,CN=Users,DC=meridiannb,DC=com / Password1!
#   (or svc account created by seed-samba.sh after DC is healthy)
#
# Lab note: seed-samba.sh sets "ldap server require strong auth = no" so IIQ can
# simple-bind on port 389. Without that, Test Connection fails with LDAP 8
# (Transport encryption required). Do not copy this setting to production AD.

## Ports (host)

| Port | Protocol |
| --- | --- |
| 3890 | LDAP |
| 6360 | LDAPS (if enabled) |
| 445 | SMB |

## Seed users

Generated list: `lab-data/enterprise/generated/samba-users.csv`  
Apply after DC healthy: `./tools/lab/enterprise/seed-samba.sh`

## Fallback

If Samba fails to bootstrap (common on some Apple Silicon setups), use OpenLDAP
pass-through login and keep `MNB-ActiveDirectory` on the Core CSV path until Samba is healthy.
The enterprise LDAP Application XML targets `samba-ad:389` inside Compose.
