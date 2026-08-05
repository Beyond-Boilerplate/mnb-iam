# Password management — Enterprise Lab (Lesson 61 live path)

## Layers

| Layer | Lab setting |
| --- | --- |
| IIQ policy | `config/PasswordPolicy/MNB-PasswordPolicy-Lab.xml` — min length 10 + complexity |
| OpenLDAP | Seed password `LabUser1!`; IIQ bind must be able to modify `userPassword` (see ACL notes below) |
| Keycloak | Realm `meridian` — password reset via Admin Console or user credentials API |
| Samba AD + IQService | **Out of scope** for this lab gate |

## Prove loop

1. Confirm SSO/pass-through with current password (`LabUser1!`).
2. Helpdesk/LCM **PASSWORD** reset in IIQ to OpenLDAP and/or Keycloak (never paste the new secret into git, Mailpit screenshots, or tickets — note only “delivered via approved channel”).
3. Old password fails Workstation/Portal login; new password succeeds.
4. Optional: disable user in Keycloak, **UNLOCK**/enable without changing secret, confirm prior password still works.

## Password Interceptor checklist answer

**Password interception in scope? No.**

Rationale: Enterprise Lab runs on macOS Docker without IQService or Microsoft Password Interceptor. Native Samba/ADUC password changes are **not** captured into IIQ. Helpdesk and joiner initial passwords use the **IIQ LCM reset path only**. Revisit if a Windows IQService stretch host is added later.

## OpenLDAP ACL

If PASSWORD plans fail with insufficient access:

```bash
docker exec mnb-openldap ldapsearch -x -H ldap://127.0.0.1 -D 'cn=admin,dc=meridiannb,dc=com' -w admin -b 'olcDatabase={1}mdb,cn=config' olcAccess
```

Ensure the IIQ service bind DN (often the app’s configured bind user) can write `userPassword` under `ou=people,dc=meridiannb,dc=com`. Prefer a dedicated provisioner DN over using `cn=admin` in production; lab may use admin for simplicity.

## What this lab does **not** claim

- AD Direct PASSWORD via IQService
- Password Interceptor capturing native AD changes
- Real Entra Graph password reset against a Microsoft tenant
