# Lesson 254 — Password Reset Live (OpenLDAP + Keycloak)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~85 minutes  
**Prereq:** Lessons 203, 206, 212, 251  
**Stack:** `./tools/lab/docker/up.sh --enterprise`  
Optional Workstation proof: add `--with=sso`

**Maps to classic track:** 61 (password management / interceptor checklist)

> **Why:** A password reset that does not change what you type at login is theater. Proof is a failed old-password login and a succeeding new one — not a green checkmark in an admin UI.

## What this is

Classic Lesson 61’s three layers, live on this estate:

| Layer | Lab object / target | Proves |
| --- | --- | --- |
| **IIQ policy** | `MNB-PasswordPolicy-Lab` | Min length **10** + upper/lower/digit/special |
| **Directory login** | OpenLDAP (`MNB-OpenLDAP`) | Pass-through IIQ login (Lesson 206) |
| **SSO login** | Keycloak realm `meridian` | Employee Portal (and optional Workstation) |
| **Interceptor / IQService AD** | **Out of scope — answer No** | See [`lab-data/enterprise/password/README.md`](../../lab-data/enterprise/password/README.md) |

You will create disposable **`lab.pwreset1`**, prove baseline logins, reset **OpenLDAP** and **Keycloak** with concrete commands/UI, prove old secrets fail and new secrets work on each path, then record the interceptor checklist answer — **without** committing the new password to git or evidence screenshots.

> **Watch out:** Never paste the new password into Mailpit screenshots, tickets, git, or `~/iiq-lab-evidence/`. Deliver out of band (password manager / sticky note you destroy). Evidence records **outcomes only**.

## Know these

```text
Read password README (interceptor = No)
  → Confirm/import MNB-PasswordPolicy-Lab
  → Create lab.pwreset1 (HCM → IIQ → OpenLDAP account → Keycloak user)
  → Baseline: IIQ pass-through + Portal SSO with LabUser1!
  → Reset OpenLDAP (ldappasswd) → old bind fails; new bind + IIQ login work
  → Reset Keycloak (Admin or API) → old Portal fails; new Portal works
  → Optional UNLOCK contrast (disable/enable without password change)
  → Evidence: outcomes + interceptor No — never the secret
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **PASSWORD feature** | Connector can set password | `MNB-OpenLDAP` has `PASSWORD` in `featuresString` |
| **Pass-through** | IIQ binds to directory to check password | Login as `lab.pwreset1` against OpenLDAP |
| **SSO secret** | Password Keycloak checks | Portal `:8092` |
| **UNLOCK** | Clear lockout / re-enable — **not** a reset | Keycloak Enabled toggle |
| **Interceptor** | Capture native AD password changes into IIQ | **Not in this lab** (no IQService) |

- **Wrong way:** Screenshotting or committing the new password.  
- **Wrong way:** Resetting only in IIQ UI and skipping login proof.  
- **Wrong way:** Using Marcus/Helen and forgetting to restore `LabUser1!`.  
- **Wrong way:** Claiming AD Interceptor is in scope on this Docker Mac lab.  
- **Wrong way:** Mixing UNLOCK with PASSWORD in the runbook (“reset” when you only needed enable).

## Intent

- Confirm lab PasswordPolicy strength.  
- Reset OpenLDAP for `lab.pwreset1` and prove bind + pass-through.  
- Reset Keycloak for the same user and prove Portal SSO.  
- Record interceptor checklist **No** with rationale.  
- Leave an evidence pack with **no secrets**.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] Stack:

```bash
./tools/lab/docker/up.sh --enterprise
# optional workstation path later:
# ./tools/lab/docker/up.sh --enterprise --with=sso
```

- [ ] Read end-to-end: [`lab-data/enterprise/password/README.md`](../../lab-data/enterprise/password/README.md) (~2 minutes)
- [ ] IIQ: [http://localhost:8080/identityiq](http://localhost:8080/identityiq) — `spadmin` / `admin`
- [ ] OpenLDAP up (`mnb-openldap`); phpLDAPadmin optional: [http://localhost:8090/](http://localhost:8090/)
- [ ] Keycloak Admin: [http://localhost:8085/admin/](http://localhost:8085/admin/) — `admin` / `admin` — realm **`meridian`**
- [ ] Employee Portal: [http://localhost:8092/](http://localhost:8092/)
- [ ] HCM healthy: `curl -sf http://localhost:8091/health`
- [ ] Choose the new secret **now** (meets policy) but keep it off disk in the repo — example shape only: `N3wLab!Pass` (10+ chars, upper, lower, digit, special). **You pick a different value.**
- [ ] Evidence dir (no passwords inside):

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/254
```

## Do this

### Task 1 — Confirm PasswordPolicy object

1. IIQ → Debug → **Object Browser** (or Setup search) → `PasswordPolicy` → **`MNB-PasswordPolicy-Lab`**  
2. If missing, import:

```bash
# seed includes PasswordPolicy — or import the single file via Debug / MCP
./tools/lab/enterprise/seed-enterprise.sh
```

File: `config/PasswordPolicy/MNB-PasswordPolicy-Lab.xml`

| Constraint | Value |
| --- | --- |
| Min length | 10 |
| Min upper / lower / numeric / special | 1 each |
| History | 5 |

- **Why:** helpdesk must know the strength bar before inventing a weak temp password.
- **Expect:** policy object present; your chosen new secret meets it.

### Task 2 — Create disposable `lab.pwreset1` end-to-end

Never use Helen / Priya / Marcus as the reset subject.

#### 2a — HCM + IIQ cube

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.pwreset1 Lab Password \
  lab.pwreset1@meridiannb.com 'Technology'
```

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.pwreset1 | python3 -m json.tool \
  | grep -E 'userName|email|active|status'
```

Aggregate **`MNB-Workday`** → Refresh Identity Cube → confirm identity **`lab.pwreset1`**.

#### 2b — OpenLDAP account with known password

Prefer joiner birthright / OpenLDAP Create Form (Lesson 217) so DN and password match policy defaults.

If you must seed manually:

```bash
docker exec mnb-openldap ldapsearch -x -H ldap://127.0.0.1 \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin \
  -b 'ou=people,dc=meridiannb,dc=com' '(uid=lab.pwreset1)' dn uid
```

If no entry, add one (lab only):

```bash
docker exec mnb-openldap ldapadd -x -H ldap://127.0.0.1 \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin <<'EOF'
dn: uid=lab.pwreset1,ou=people,dc=meridiannb,dc=com
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
objectClass: top
cn: Lab Password
sn: Password
uid: lab.pwreset1
mail: lab.pwreset1@meridiannb.com
userPassword: LabUser1!
EOF
```

Aggregate **`MNB-OpenLDAP`** → correlate link on cube `lab.pwreset1`.

Prove bind with **current** password:

```bash
docker exec mnb-openldap ldapwhoami -x -H ldap://127.0.0.1 \
  -D 'uid=lab.pwreset1,ou=people,dc=meridiannb,dc=com' -w 'LabUser1!'
```

- **Expect:** `dn:uid=lab.pwreset1,ou=people,dc=meridiannb,dc=com` (success).

#### 2c — Keycloak user with known password

- Birthright **`MNB-Keycloak-IdP`** with `portal-users` if live  
- Else Keycloak Admin → `meridian` → Add user `lab.pwreset1`, email `lab.pwreset1@meridiannb.com`, Credentials `LabUser1!` Temporary **OFF**, join **`portal-users`**

- **Why:** you need both login targets before any reset.
- **Expect:** LDAP bind works; Keycloak user exists with `portal-users`.

### Task 3 — Baseline logins (old password works)

Record baselines **before** you change anything.

#### 3a — IIQ pass-through (OpenLDAP)

1. IIQ logout  
2. Login page → username `lab.pwreset1` / password `LabUser1!`  
3. Confirm pass-through against **`MNB-OpenLDAP`** is configured (Lesson 206). If pass-through is not enabled in your session, document that gap and still use `ldapwhoami` as directory proof.

- **Expect:** IIQ session opens **or** you explicitly rely on `ldapwhoami` success from Task 2b as the LDAP baseline.

#### 3b — Employee Portal SSO (Keycloak)

1. Private window → [http://localhost:8092/](http://localhost:8092/)  
2. Sign in `lab.pwreset1` / `LabUser1!`  
3. Sign out fully  

- **Expect:** Portal Signed in. Screenshot `01-baseline-portal-ok.png` (no password visible).

Write `~/iiq-lab-evidence/sandbox/254/BASELINE.txt`:

```text
Subject: lab.pwreset1
LDAP bind LabUser1!: OK
Portal SSO LabUser1!: OK
IIQ pass-through: OK / GAP ________
```

### Task 4 — Reset OpenLDAP password (concrete)

Pick your new secret (policy-compliant). Call it **NEW_LDAP** in your head — do not write it into evidence files.

#### 4a — Admin reset with `ldappasswd`

```bash
# Replace NEW_LDAP with your chosen secret (do not commit this command to git with the real value)
docker exec mnb-openldap ldappasswd -x -H ldap://127.0.0.1 \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin \
  -s 'NEW_LDAP' \
  'uid=lab.pwreset1,ou=people,dc=meridiannb,dc=com'
```

If `ldappasswd` is unavailable in the image, use `ldapmodify`:

```bash
docker exec -i mnb-openldap ldapmodify -x -H ldap://127.0.0.1 \
  -D 'cn=admin,dc=meridiannb,dc=com' -w admin <<'EOF'
dn: uid=lab.pwreset1,ou=people,dc=meridiannb,dc=com
changetype: modify
replace: userPassword
userPassword: NEW_LDAP
EOF
```

#### 4b — Optional IIQ Manage Passwords path

If your build exposes helpdesk / Manage Passwords targeting **`MNB-OpenLDAP`**:

1. As a helpdesk-capable user (or `spadmin`), open Manage Passwords / LCM password change  
2. Select identity `lab.pwreset1`, application OpenLDAP  
3. Set the same **NEW_LDAP** meeting `MNB-PasswordPolicy-Lab`  
4. Confirm Provisioning Transaction **Committed** (not Failed)

If IIQ PASSWORD plan fails with insufficient access, fix OpenLDAP ACL per password README **or** stay on `ldappasswd` for lab proof and note the ACL finding.

#### 4c — Prove old LDAP fails; new LDAP works

```bash
# Old must fail
docker exec mnb-openldap ldapwhoami -x -H ldap://127.0.0.1 \
  -D 'uid=lab.pwreset1,ou=people,dc=meridiannb,dc=com' -w 'LabUser1!' ; echo exit:$?

# New must succeed
docker exec mnb-openldap ldapwhoami -x -H ldap://127.0.0.1 \
  -D 'uid=lab.pwreset1,ou=people,dc=meridiannb,dc=com' -w 'NEW_LDAP' ; echo exit:$?
```

- **Expect:** old → bind error / non-zero; new → `dn:uid=lab.pwreset1,…`

Retry IIQ login with **old** password → fail; with **NEW_LDAP** → succeed (if pass-through on).

Write `LDAP-PROOF.txt` (no secrets):

```text
OpenLDAP reset method: ldappasswd | ldapmodify | IIQ Manage Passwords
Old LabUser1! bind: FAIL
New secret bind: OK
IIQ pass-through old/new: ________
```

- **Why:** directory bind is ground truth for OpenLDAP — UI success alone is not enough.
- **Expect:** old dead, new live on LDAP.

### Task 5 — Reset Keycloak password (concrete)

Keycloak still has `LabUser1!` until you change it. Portal SSO does **not** read OpenLDAP.

#### 5a — Admin Console

1. [http://localhost:8085/admin/](http://localhost:8085/admin/) → realm **`meridian`**  
2. **Users** → `lab.pwreset1` → **Credentials**  
3. **Set password** → enter **NEW_KC** (may match NEW_LDAP or differ — your choice; both must meet policy)  
4. **Temporary** = **OFF**  
5. Save  

#### 5b — Admin API (same outcome)

```bash
TOKEN=$(curl -s -X POST 'http://localhost:8085/realms/master/protocol/openid-connect/token' \
  -d 'client_id=admin-cli' -d 'username=admin' -d 'password=admin' -d 'grant_type=password' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8085/admin/realms/meridian/users?username=lab.pwreset1&exact=true' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["id"])')

# Replace NEW_KC — do not leave real secrets in shell history if avoidable
curl -s -o /dev/null -w '%{http_code}\n' -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  "http://localhost:8085/admin/realms/meridian/users/${USER_ID}/reset-password" \
  -d '{"type":"password","value":"NEW_KC","temporary":false}'
```

- **Expect:** HTTP `204`.

#### 5c — Prove old SSO fails; new SSO works

1. Fresh private window (clear Keycloak cookies)  
2. Portal [http://localhost:8092/](http://localhost:8092/) → `lab.pwreset1` / **`LabUser1!`**  
   - **Expect:** login **fails**  
   - Screenshot `02-portal-old-password-fail.png` (error state only)  
3. Same window → `lab.pwreset1` / **NEW_KC**  
   - **Expect:** **Signed in**  
   - Screenshot `03-portal-new-password-ok.png`

Optional if `--with=sso`: repeat on Workstation `:8094` **after** joining `mnb-workstation-users` (Lesson 251). Same Keycloak secret.

Write `KEYCLOAK-PROOF.txt`:

```text
Keycloak reset method: Admin Console | Admin API
Portal old LabUser1!: FAIL
Portal new secret: OK
Temporary flag: OFF
```

- **Why:** SSO and LDAP are separate stores on this estate — resetting one never implies the other.
- **Expect:** both proof files show fail→succeed.

> **Watch out:** Sticky OIDC sessions can look like “old password still works.” Always use a fresh private window after reset.

### Task 6 — Optional UNLOCK contrast (not a password reset)

1. Keycloak → `lab.pwreset1` → set **Enabled = OFF** → Save  
2. Portal login with **NEW_KC** → must **fail**  
3. Set **Enabled = ON** (UNLOCK / re-enable) — do **not** change password  
4. Portal login with **NEW_KC** → **succeeds**

- **Why:** helpdesk runbooks that say “reset” for lockout create password churn and ticket noise.
- **Expect:** re-enable restores access with the **same** secret.

Note in evidence: `UNLOCK contrast: disable blocked SSO; enable restored NEW_KC without another reset`.

### Task 7 — Interceptor checklist answer

From the password README, write `~/iiq-lab-evidence/sandbox/254/INTERCEPTOR.txt`:

```text
Password interception in scope? No.

Rationale: Enterprise Lab runs on macOS Docker without IQService or Microsoft
Password Interceptor. Native Samba/ADUC password changes are not captured into
IIQ. Helpdesk and joiner initial passwords use the IIQ LCM / directory admin
reset path only. Revisit if a Windows IQService stretch host is added later.
```

- **Why:** examiners ask the checklist question; “we use SailPoint” is not an answer.
- **Expect:** file on disk; **no** password material beside it.

### Task 8 — Final SUMMARY (no secrets)

`~/iiq-lab-evidence/sandbox/254/SUMMARY.txt`:

```text
Lesson 254
Subject: lab.pwreset1
PasswordPolicy: MNB-PasswordPolicy-Lab confirmed
LDAP: old fail / new ok (method ________)
Keycloak/Portal: old fail / new ok (method ________)
UNLOCK contrast: done / skipped
Interceptor: No (see INTERCEPTOR.txt)
Secrets in evidence folder: NONE
```

## If it fails

| Symptom | Fix |
| --- | --- |
| `ldapwhoami` always fails | Wrong DN / password; confirm entry with admin `ldapsearch`; check `ou=people,dc=meridiannb,dc=com` |
| IIQ PASSWORD plan insufficient access | OpenLDAP ACL — password README; lab may use admin `ldappasswd` and document ACL gap |
| Policy rejects password | Length ≥10 + upper + lower + digit + special |
| Keycloak set password but Portal accepts old | Temporary flag left ON; or sticky session — private window; confirm Credentials updated |
| Portal fails with new password | User disabled; missing `portal-users`; wrong realm; typo in NEW_KC |
| IIQ pass-through ignores LDAP change | Pass-through app not `MNB-OpenLDAP` or local IIQ password still in play — fix 206 config |
| Used Marcus and broke shared persona | Restore Keycloak + LDAP to `LabUser1!`; next time use `lab.pwreset1` |
| Accidentally committed password | Rotate immediately; purge from git history if pushed; never re-use that secret |

## You are done when

- [ ] `MNB-PasswordPolicy-Lab` confirmed  
- [ ] OpenLDAP: old password bind fails; new password bind succeeds  
- [ ] Keycloak/Portal: old password fails; new password succeeds  
- [ ] `INTERCEPTOR.txt` answers **No** with rationale  
- [ ] Evidence folder has proofs + SUMMARY and **contains no password values**  

## Control note

- **Control:** Password reset proof-of-effect (login/bind, not admin-UI success) + interceptor policy documentation  
- **Owner:** IAM Engineering + Directory/IdP Ops  
- **SLA (lab):** Old credential dead and new credential live on each target in the same session  
- **Evidence:** `~/iiq-lab-evidence/sandbox/254/` — outcomes only  
- **Out of scope:** AD Direct PASSWORD via IQService, Password Interceptor, real Entra Graph password reset  

## Quick check

1. What proves a reset worked? → Old credential fails login/bind; new succeeds  
2. Does OpenLDAP reset change Portal SSO? → **No** — Keycloak is a separate secret store here  
3. Interceptor / IQService AD password in this lab? → **No**, with written rationale  
4. Where may the new secret appear in evidence? → **Nowhere**  
5. How is UNLOCK different from PASSWORD? → Re-enable/clear lockout without setting a new secret  

## Feedback

Could you reset LDAP and Keycloak for a fresh `lab.pwreset*` user and prove fail→succeed on both paths without looking at this page?

If something failed, note the **task number**, which target (LDAP vs Keycloak), and the exact symptom (bind error vs Portal error vs IIQ provisioning Failed) — never the password itself.

## Navigate

- Previous: [Lesson 253](253-intranet-sso-apps.md)
- Next: [Lesson 255](255-privileged-vault-checkout.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Password: [password/README.md](../../lab-data/enterprise/password/README.md)
