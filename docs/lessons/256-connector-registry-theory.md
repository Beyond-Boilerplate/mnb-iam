# Lesson 256 — Connector Registry & Selection (Theory)

**Track:** Enterprise Sandbox Path — **Theory**  
**Time:** ~50 minutes  
**Prereq:** Lessons 204–210 (at least one live app built)  
**Stack:** `./tools/lab/docker/up.sh --enterprise` (IIQ Debug only)

**Maps to classic track:** 51–52 / 55

> **Why:** Risk asks “can IIQ disable this account within SLA?” The honest answer is in `ConnectorRegistry` → `featuresString`, not a vendor slide.

## What this is

**Theory** lesson — guided inspection and a selection matrix you can defend. No new Application build required.

IdentityIQ ships connector **types** in **`ConnectorRegistry`**. Each type declares capabilities (`PROVISIONING`, `ENABLE`, `PASSWORD`, …). Your `MNB-*` Applications inherit those features from the type. Promising password reset on a DelimitedFile app fails every audit.

Live lessons (**204–210**, **230**, **234–238**) exercise connectors. This lesson teaches you to **choose** the family before you click Create Application.

## Know these

```text
ConnectorRegistry (type + featuresString)
  → Template Application
  → MNB-* owned Application (host, schema, owner, tasks)
```

| Term | Plain English | Meridian example |
| --- | --- | --- |
| **Connector type** | Engine IIQ knows how to start | JDBC, Web Services, SCIM 2.0, AD Direct |
| **`featuresString`** | Capabilities the framework may invoke | `PROVISIONING, ENABLE, SYNC_PROVISIONING` on Core Banking |
| **Template** | Starter app for a type | Blank JDBC template |
| **`MNB-*` Application** | Bank-owned instance | `MNB-CoreBanking`, `MNB-WirePortal` |

| Family | Right when | Wrong when | Estate examples |
| --- | --- | --- | --- |
| **DelimitedFile** | File drop / teaching inventory | You need live disable/password | Early CSV bridges |
| **Direct / JDBC / LDAP** | First-class connector exists | Faking features a Direct type already owns | OpenLDAP, Samba AD, Core Banking |
| **Web Services / SCIM** | Custom REST or SCIM SaaS | Nightly CSV when an API exists | Wire Portal, CRM mock, Keycloak IdP |

| Feature | Promise to Risk |
| --- | --- |
| `PROVISIONING` | Create / modify accounts |
| `ENABLE` | Enable / disable |
| `PASSWORD` | Password set / change |
| `UNLOCK` | Unlock |
| `NO_RANDOM_ACCESS` | Iterate-only (file/LDIF) — no get-by-key |
| `SYNC_PROVISIONING` | Synchronous plan execution |

- **Wrong way:** Treating the Applications list as “what IIQ can do” — features come from the **type**.
- **Wrong way:** Choosing DelimitedFile for Wire Portal “because CSV is easier” — leaver disable will never hit the API.
- **Wrong way:** Turn **create identities** on for a target app — HR/Workday owns cube create.

## Intent

- Open `ConnectorRegistry` in Debug and decode one type’s `featuresString`.
- Complete a three-row selection matrix for Meridian systems you already run live.
- Name one capability your live Samba AD path **cannot** prove without IQService (Lesson 257).

## Before you start

- [ ] IIQ open as `spadmin`
- [ ] At least one of: `MNB-OpenLDAP`, `MNB-CoreBanking`, `MNB-WirePortal` exists
- [ ] Optional glossary: `lab-data/connectors/features-string-glossary.md`
- [ ] Evidence:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/256
```

## Do this

### Task 1 — Open ConnectorRegistry

1. **Debug → Object Browser** → type **`ConnectorRegistry`** (or search Configuration / Registry objects your build exposes)
2. Find types matching: **JDBC**, **Web Services**, **SCIM**, **Active Directory** / LDAP
3. Copy the `featuresString` for **JDBC** (or the type behind `MNB-CoreBanking`)

- **Why:** examiners ask where IIQ *declares* capability.
- **Expect:** a comma-separated feature list saved under evidence.

### Task 2 — Compare type features to a live Application

1. **Applications → Application Definition → MNB-CoreBanking** (or OpenLDAP)
2. Note the connector type and whether UI shows provisioning / enable options
3. Write:

```text
App: MNB-CoreBanking
Type: JDBC
featuresString (registry): ________
Live proof already done: Lesson 208 / 236
```

- **Expect:** registry features align with what Lesson 230/236 can triage.

### Task 3 — Selection matrix (three rows)

Fill under evidence (prefer / alternate / reject):

| System | Prefer family | Alternate | Reject + why |
| --- | --- | --- | --- |
| Core Banking DB | JDBC Direct | — | DelimitedFile — no live disable |
| Wire Portal API | Web Services | SCIM if offered | Nightly CSV — leaver SLA lie |
| Corporate AD (prod) | AD Direct + IQService | — | Generic LDAP-only for password ops |

- **Why:** Architecture signs this before go-live.
- **Expect:** three rows with honest rejects.

### Task 4 — Feature vs policy vs promise

Write one line:

```text
featuresString = what the type can invoke.
Provisioning Policy = what SQL/attrs we map.
Promise to Risk = only the intersection we tested (Lesson 230 / 219).
```

- **Expect:** you can explain why a green Test Connection ≠ “disable works.”

## If it fails

| Symptom | Fix |
| --- | --- |
| Can’t find ConnectorRegistry | Use Application type dropdown + Debug Application XML `connector=` / `featuresString` as proxy evidence |
| Features don’t match UI | You compared the wrong type — open the live app’s XML type name exactly |
| Matrix wants IQService detail | Continue in Lesson 257 — don’t invent a live Windows agent here |

## You are done when

- [ ] One registry / type `featuresString` captured  
- [ ] Three-row selection matrix saved  
- [ ] You can separate feature vs policy vs tested promise  

## Control note

- **Control:** Connector selection and capability honesty  
- **Owner:** IAM Architecture + App Owners  
- **Evidence:** `~/iiq-lab-evidence/sandbox/256/`  

## Quick check

1. Where do features come from? → Connector **type** / registry, not marketing names  
2. Why not CSV for Wire? → No live disable/provision to the API  
3. What does `NO_RANDOM_ACCESS` imply? → Iterate-only — no get-one-account workflows  

## Feedback

Could you pick a connector family for a new Meridian REST payments API without opening this page? If registry UI was missing, note what Application XML fields you used instead.

## Navigate

- Previous: [Lesson 255](255-privileged-vault-checkout.md)
- Next: [Lesson 257](257-iqservice-architecture-theory.md)
- Related live: [204](204-openldap-live-ops.md) · [208](208-jdbc-core-banking.md) · [209](209-wire-webservices.md) · [230](230-provisioning-troubleshoot-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md)
