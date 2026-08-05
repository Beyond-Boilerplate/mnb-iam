# Pass-through authentication (Enterprise Lab)

Prove IIQ login as a real directory user (OpenLDAP and/or Samba).

## OpenLDAP (always in Core stack)

1. Confirm bind works:

```bash
ldapsearch -x -H ldap://localhost:389 -b ou=people,dc=meridiannb,dc=com \
  -D 'uid=helen.ross,ou=people,dc=meridiannb,dc=com' -w 'LabUser1!' '(uid=helen.ross)' dn
```

2. In IIQ: **Gear → Global Settings → Login Configuration → LDAP/Directory**
   - Enable authentication against application **`MNB-OpenLDAP`**
   - Map username to `uid` / `mail`
3. Log out of `spadmin`, log in as `helen.ross` / `LabUser1!`

## Samba AD (enterprise profile)

When `mnb-samba-ad` is healthy and seeded:

1. Use application **`MNB-ActiveDirectory-Live`** (LDAP to `samba-ad:389`)
2. Add it as a second pass-through source (or primary for AD drills)
3. Username = `sAMAccountName` (same as Meridian `name`, e.g. `helen.ross`)

IQService password reset paths remain out of scope — see [`docs/ENTERPRISE-LAB-V2.md`](../../docs/ENTERPRISE-LAB-V2.md).

## Employee Portal SSO

Keycloak realm `meridian` — `http://localhost:8092/` → Sign in → IdP login as `helen.ross` / `LabUser1!`.
