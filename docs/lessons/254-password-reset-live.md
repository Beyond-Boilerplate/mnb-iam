# Lesson 254 — Password Reset Live (OpenLDAP + Keycloak)

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~60 minutes  
**Prereq:** Lessons 203, 206, 212, 251  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 61

> **Why:** A password reset that does not change what you type at login is theater. Proof is a failed old-password login and a succeeding new one — not a green checkmark in an admin UI.

## What this is

Lesson 61's three layers, live on this estate: **IIQ** `MNB-PasswordPolicy-Lab` (min length 10 + complexity, imported via enterprise seed); **targets that matter for login** — OpenLDAP (pass-through) and Keycloak (SSO); and the **interceptor/IQService AD password** question, answered **No** here (see [`lab-data/enterprise/password/README.md`](../../lab-data/enterprise/password/README.md)). You reset a lab user's password, prove the old secret fails and the new one works on Portal or Workstation, without ever committing the new secret to git.

## Know these

| Layer | Object |
| --- | --- |
| IIQ policy | `MNB-PasswordPolicy-Lab` — min length 10 + complexity |
| Login targets | OpenLDAP (pass-through), Keycloak (SSO) |
| Interceptor/IQService AD password | Answered **No** in this lab — see password README |

**Wrong way:** Screenshotting or committing the new password anywhere in evidence — deliver it "out of band" and destroy the note.

## Intent

- Import/confirm the lab PasswordPolicy object.
- Reset password for a disposable test identity (or temporarily for Marcus) on Keycloak and/or OpenLDAP.
- Prove SSO with new password; fail with old.
- Record interceptor checklist answer **No** with rationale.

## Before you start

- [ ] `lab-data/enterprise/password/README.md` available to read
- [ ] Portal (`:8092`) or Workstation (`:8094`) login path working with current password
- [ ] Decided subject: throwaway `lab.pwtest` user, or Marcus (restore `LabUser1!` after)
- [ ] Evidence: `mkdir -p ~/iiq-lab-evidence/sandbox/254` (never store checkout/reset passwords here)

## Do this

1. Read `lab-data/enterprise/password/README.md` end-to-end.  
   **Expect:** Two minutes — this is the control narrative for the whole lesson.
2. Import `config/PasswordPolicy/MNB-PasswordPolicy-Lab.xml` if missing (`seed-enterprise.sh` or MCP import).  
   **Expect:** Policy object present in IIQ.
3. Pick a subject: prefer a throwaway Keycloak user `lab.pwtest`, or Marcus if you'll restore `LabUser1!` afterward.  
   **Expect:** Subject identity confirmed.
4. Confirm current login works: Portal `http://localhost:8092/` or Workstation `:8094` with the current password.  
   **Expect:** Baseline login succeeds before you touch anything.
5. Perform a **PASSWORD** reset — preferred: IIQ Manage Passwords/LCM password change targeting OpenLDAP and/or `MNB-Okta` (Keycloak) if the PASSWORD feature is enabled; lab fallback: Keycloak Admin → Users → Credentials → Set password (not temporary), or OpenLDAP via `ldappasswd`/phpLDAPadmin.  
   **Expect:** The proof is login success, not which UI flipped the hash — connector PASSWORD wiring varies by image.
6. Deliver the new secret "out of band" (password manager or a sticky note you destroy) — do **not** screenshot Mailpit or commit it.  
   **Expect:** No secret persisted anywhere durable.
7. Sign out; attempt old password.  
   **Expect:** Fails. Sign in with new password.  
   **Expect:** Succeeds on Portal or Workstation.
8. Optional unlock drill: disable the user in Keycloak, confirm SSO fails; re-enable (UNLOCK) without changing password.  
   **Expect:** Prior new password still works after unlock.
9. Write under `~/iiq-lab-evidence/sandbox/254/`: interceptor answer **No** + one-sentence rationale (from the password README).  
   **Expect:** Note saved, no secrets included.

## If it fails

- **IIQ PASSWORD plan errors on OpenLDAP** — ACL: IIQ bind DN cannot write `userPassword`. Fix the ACL or use admin bind for lab only; document what you did.
- **Keycloak accepts reset but Portal still uses old session** — sign out / clear cookies; OIDC sessions are sticky.
- **Policy rejects your new password** — meet min length 10 + upper/lower/digit/special per `MNB-PasswordPolicy-Lab`.

## You are done when

Old password fails SSO, new password succeeds, and the interceptor checklist answer **No** is on disk under your evidence folder.

## Control note

- **Control:** Password reset proof-of-effect (login, not admin-UI success message) + interceptor policy documentation.  
- **Owner:** IAM Engineering + Directory/IdP Ops.  
- **SLA (lab):** Old credential dead, new credential live, same session.  
- **Evidence:** `~/iiq-lab-evidence/sandbox/254/` — old-fail/new-succeed proof, interceptor rationale — never the password itself.

## Quick check

1. What's the real proof a password reset worked? → Old password fails login, new one succeeds.  
2. What's the interceptor/IQService AD password answer in this lab? → No, with a documented rationale.  
3. Where should the new secret ever appear in evidence? → Nowhere — deliver out of band, never screenshot or commit it.

## Navigate

- Previous: Lesson 253
- Next: — (v3 add-on complete; return to 250 for capstone or extend estate)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Password: [password/README.md](../../lab-data/enterprise/password/README.md)
