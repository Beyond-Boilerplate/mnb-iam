# Tutorial Writer — feedback log

Running log of lessons learned about *how this skill writes tutorials*. Read this before writing/revising a tutorial; append a new dated entry whenever the user corrects or gives feedback on output from this skill.

Format per entry:

```markdown
## YYYY-MM-DD — <short topic>
- **Issue:** what went wrong or what the user flagged
- **Fix:** what was changed / what to do differently next time
```

## 2026-08-06 — Do not include 'line count'
- **Issue:** Doc includes `Why (1–2 lines):`
- **Fix:** Keep 'Why' [header] and do not include internal instructions [line number directive]

## 2026-08-06 — Do not include any 'In Paper / Notebook Assignments'
- **Issue:** Lessons contain paper assignments which users are not likely to follow through
- **Fix:** Instead, always give priority to real technical / UI flow tasks users can perform to solidify the lesson knowledge

## 2026-08-06 — Avoid long block of text
- **Issue:** Lessons contain a huge paragraph that is hard to read
- **Fix:** Instead, always give priority to bullets and line breaks and always encapsulate cmd commands as code

## 2026-08-06 — Nest related / internal fields 
- **Issue:** Lessons contain sections such as 'why', 'expect' etc. that belong to a point but are not nested accordingly
- **Fix:** Instead, always give priority to organize and indent the content for it to be clear and flowing

## 2026-08-06 — Never expose internal design / limitation details
- **Issue:** Lessons contain sections such as [per the Feasibility Boundaries in ENTERPRISE-LAB-V2.md]
- **Fix:** Instead, do not bother the reader with internal details 

## 2026-08-06 — Enterprise Sandbox: Workday-first cubes, not HR CSV seed
- **Issue:** User wanted enterprise seed to stop treating MNB-HR as authoritative and to leave Identity Warehouse empty until learners aggregate MNB-Workday themselves
- **Fix:** For Enterprise Path tutorials: (1) seed = app definitions only; (2) Warehouse empty after 201–202 is expected, not a failure; (3) Lesson 207 owns first Aggregate + Identity Refresh (create identities) from Workday + HCM UI; (4) reorder path so 207 precedes 204–206; (5) never tell readers to aggregate MNB-HR to “fix” missing cubes

## 2026-08-06 — Lesson 211 skipped auth/SSO security concepts
- **Issue:** Expanded Keycloak lesson still assumed readers already knew IdP, SSO, OIDC vs OAuth, public/confidential, PKCE, redirect URI, discovery/JWKS, authn vs authz, service accounts
- **Fix:** For first-introduction IdP/SSO lessons: add an explicit Concept primer that defines every new auth/security term with a Meridian example *before* Do this; reinforce each term in the matching Task (realm, groups=authz, public+PKCE, confidential secret, M2M, discovery fields); expand Quick check to cover the vocabulary, not only UI clicks

## 2026-08-06 — Enterprise lessons that skip Core must borrow Core concepts
- **Issue:** Lesson 214 assumed Classic 05/06/17–19 knowledge (agg vs refresh, correlation vs schema identityAttribute, manager correlation, uncorrelated vs orphan, Searchable userId / UIConfig) while Enterprise Path skips those lessons
- **Fix:** When an Enterprise lesson “maps to classic track,” add a Concept primer that lifts definitions, tables, flows, and anti-patterns from those Core lessons (adapted to Workday-first), then keep live Tasks as proof — don’t only say “maps to 17–19”

## 2026-08-06 — Lesson 215 Attribute Sync: Targets vs Sources vs Update policy
- **Issue:** Task 4 said “provisioning policy or global Attribute Sync” vaguely; learners wired Identity Mapping *Sources* to OpenLDAP (cube snapped back to LDAP) and expected the Update policy form to trigger itself; form editor Settings had no value binding (Value Settings / Script was the real control)
- **Fix:** For attribute-sync lessons: (1) teach Source = in, Target = out before clicks; (2) require Attribute Targets to OpenLDAP as the plan trigger; (3) Update policy Field scripts as value supply only; (4) call out LDAP-as-Source as the poison anti-pattern; (5) Task 5 = synchronize attributes + provisioning; (6) troubleshoot table separates no-plan vs blank-values vs Source-overwrite

## 2026-08-06 — Lesson 216: roles not pre-seeded — create IT + business
- **Issue:** Lesson assumed `MNB-Bundle-Birthright-Employee` / `MNB-Bundle-Wire-Initiator` already imported; they do not exist in the live estate
- **Fix:** For Enterprise birthright lessons: instruct Create New → Role for IT packs (entitlements) then business roles (Required Roles + selector / requestable); keep Bundle names downstream lessons expect; never treat roles as seed prerequisites

## 2026-08-06 — Lesson 216: empty LDAP Entitlement Catalog + wrong group name
- **Issue:** Learners saw empty Entitlement Catalog for OpenLDAP; lesson told them to find `MNB-Employees` which is Samba-only
- **Fix:** Task 1 = run Account Group Aggregation (`MNB-OpenLDAP-Group-Aggregation`) before role create; use OpenLDAP group `all-employees` (not Samba `MNB-Employees`); call out account-agg-only as expected empty catalog

## 2026-08-06 — Lesson 216: Wire Portal has no Group Aggregation
- **Issue:** Learners added `MNB-WirePortal` to Account Group Aggregation and got *No configuration found for 'Group Aggregation'*
- **Fix:** Teach two promotion paths — directory apps need Group Aggregation; Web Services Wire promotes `WIRE_INIT` via Account Aggregation + managed `entitlements` attribute (Lesson 209); never put Wire on a group-agg task unless a Group Aggregation operation exists

## 2026-08-06 — Lesson 217: joiner workflow not pre-seeded
- **Issue:** Lesson assumed `MNB-Workflow-Joiner` (and its IdentityTrigger) already existed; they do not after wipe / partial seed
- **Fix:** Tasks 1–2 create the workflow (Debug Import of `config/Workflow/MNB-Workflow-Joiner.xml` or Business Processes designer) and `MNB-IdentityTrigger-Joiner` before HCM hire; warn that trigger-before-workflow fails; Refresh step must set provision=true

## 2026-08-06 — Lesson 217: joiner never triggered — Process events off
- **Issue:** Live lab had cube `sagar.poudel` from Workday agg + Refresh, but zero WorkflowCases; Refresh Identity Cube had `processTriggers=false`; trigger also bound to `MNB-Joiner-Workflow` instead of `MNB-Workflow-Joiner`
- **Fix:** Task 5 must enable Refresh **Process events**; document Create triggers do not re-fire on existing cubes; verify IdentityTrigger workflow name exact match; manual launch fallback for already-created joiners

## 2026-08-06 — Lesson 217: Portal/Mailpit tasks skipped LDAP form + Keycloak gap
- **Issue:** Tasks jumped to Portal SSO / Mailpit as if birthright finished day-one access; learners hit OpenLDAP Create Form (Pending refresh) then found no Keycloak user; Mailpit “welcome” implied email exists in joiner workflow
- **Fix:** Insert Task 9 Complete OpenLDAP Create Form (exact DN/password values); Task 10 ldapsearch proof; Task 11 required Keycloak user+groups (birthright ≠ IdP); Task 12 Portal only after Keycloak; Task 13 Mailpit = expect **no** welcome mail / Lesson 232 gap; diagram and day-one table show LDAP form + manual IdP as explicit gates

## 2026-08-06 — Birthright owns Portal groups via MNB-Keycloak-IdP
- **Issue:** User chose option B — automate IdP in birthright instead of Lesson 217 manual Keycloak create; no later lesson closed the gap
- **Fix:** Added connector-mock `/idp/scim` Keycloak Admin facade + `keycloak-enable-iiq-provisioner.sh` + Application `MNB-Keycloak-IdP`; Lesson 216 adds `MNB-IT-IdP-Portal` (portal-users + mnb-employees) to birthright Required Roles; Lesson 217 Task 11 verifies IdP from birthright (no Admin create); seed imports new app XML

## 2026-08-06 — MNB-Keycloak-IdP ManagedAttribute.attribute blank
- **Issue:** Group aggregation created entitlements with empty `attribute` and UUID values; not usable as account `groups` memberships
- **Fix:** Account schema `groups` must set `schemaObjectType="group"` (OpenLDAP pattern); group schema `identityAttribute=displayName` so catalog values are `portal-users` / `mnb-employees`; re-agg after import

## 2026-08-07 — Joiner IdP profile prompt, empty Groups, OpenLDAP Form
- **Issue:** New Keycloak users prompted for email/first/last on first Portal login; users existed in Keycloak with empty Groups; OpenLDAP Create still opened Form work items
- **Fix:** (1) IdP Create Field scripts for `emails`/`givenName`/`familyName` + clear requiredActions on create; (2) `/idp/scim` resolve group UUIDs and implement PUT/PATCH `/Groups/{id}` members (IIQ membership path); (3) OpenLDAP Create Field scripts for `dn`/`password`/`cn`/`givenName`/`sn`; document in Lessons 216 (Tasks 1d/1c) and 217 (Task 9 scripts-first, profile/groups checks)
