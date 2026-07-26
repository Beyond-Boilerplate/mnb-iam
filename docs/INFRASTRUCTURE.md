# Infrastructure — How SailPoint IdentityIQ Fits Together

A beginner-friendly map of what IdentityIQ is, what each piece of this repo does, and how a real company (including our fictitious bank) uses the platform.

If you have not installed yet, start with [LOCAL_SETUP.md](LOCAL_SETUP.md).

---

## 1. What problem does IdentityIQ solve?

Every employee needs access to systems: email, HR, core banking, cloud apps, databases, VPN, and more.

Without a central identity platform, companies end up with:

- Orphan accounts (people leave, access remains)
- Over-privileged users (“everyone is admin”)
- No audit trail for who approved what
- Manual, ticket-driven onboarding that takes days

**SailPoint IdentityIQ (IIQ)** is an **Identity Governance and Administration (IGA)** platform. It answers:

| Question | IIQ concept |
| --- | --- |
| Who is this person? | **Identity** (identity cube) |
| What accounts do they have? | **Accounts** on **Applications** |
| What can those accounts do? | **Entitlements** / groups / roles |
| Should they have that access? | **Policies**, **certifications**, **approvals** |
| How did access get created/removed? | **Provisioning**, **workflows**, **audit** |

IdentityIQ sits **between** people (HR / managers / IT) and target systems, and becomes the system of record for *who should have what*.

---

## 2. What is in this project folder?

```text
Sailpoint/
├── identityiq-8.5/                 # Official IdentityIQ 8.5 distribution
│   ├── identityiq.war              # The web application (deploy to Tomcat)
│   ├── database/                   # SQL to create/upgrade IIQ schemas
│   ├── doc/                        # Product PDFs (install, LCM, certifications, …)
│   ├── integration/                # Optional packaged integrations (SAP, Oracle, …)
│   └── ConnectorGateway-*.zip      # Optional gateway for some remote connectors
├── HRApplications.txt              # Sample authoritative HR file (people + org)
├── EmployeeData.txt                # Sample “who has what IT access” file
├── email.txt                       # Sample certification notification emails
├── LOCAL_SETUP.md                  # How to stand up a local instance
├── INFRASTRUCTURE.md               # This file
└── lessons/                        # Progressive hands-on curriculum
```

### `identityiq.war`

A Java web application. When exploded under Tomcat as `/identityiq`, it becomes:

- UI for admins, managers, and end users
- Background **task** engine (aggregations, certifications, refreshes)
- **Workflow** engine (approvals, lifecycle events)
- REST / SCIM surfaces (depending on configuration)
- `WEB-INF/bin/iiq` console for imports, encrypt, debugging

### `database/`

Creates the schemas IIQ needs. For MySQL labs the important script is:

- `create_identityiq_tables-8.5.mysql`

It creates:

| Schema | Purpose |
| --- | --- |
| `identityiq` | Core product data (identities, apps, roles, certs, …) |
| `identityiqah` | Access History (historical access / analytics support) |
| `identityiqPlugin` | Plugin framework database |

### `doc/`

Vendor documentation. Prefer these when you need exact product behavior. This markdown layer is the **lab-friendly** path.

### Sample text files at repo root

These are **not** part of the WAR. They are lab source data you will point **Delimited File** applications at:

- `HRApplications.txt` — employees, managers, departments, status (authoritative source)
- `EmployeeData.txt` — usernames mapped to IT systems / entitlements (`ODS`, `AWS`, `SAP`, …)
- `email.txt` — example of what managers receive when a certification is assigned

---

## 3. Runtime architecture (local lab)

```text
┌─────────────────────────────────────────────────────────┐
│  Browser  →  http://localhost:8080/identityiq           │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  Apache Tomcat 9                                        │
│    webapps/identityiq/   ← exploded identityiq.war      │
│      WEB-INF/classes/iiq.properties                     │
│      WEB-INF/bin/iiq          (console)                 │
│      WEB-INF/config/init*.xml (seed objects)            │
└───────────────────────────┬─────────────────────────────┘
                            │ JDBC
┌───────────────────────────▼─────────────────────────────┐
│  MySQL 8                                                │
│    identityiq / identityiqah / identityiqPlugin         │
└─────────────────────────────────────────────────────────┘

Optional later:
  Delimited files, LDAP, JDBC apps, AD, cloud connectors, Connector Gateway
```

### Key config file: `iiq.properties`

Lives at:

```text
$IIQ_HOME/WEB-INF/classes/iiq.properties
```

It tells IdentityIQ:

- How to connect to each database
- Whether plugins are enabled
- Pool / dialect settings

**Rule of thumb:** If Tomcat is up but IIQ will not start, check MySQL + `iiq.properties` first.

### Key bootstrap files

| File | When you import it |
| --- | --- |
| `WEB-INF/config/init.xml` | Brand-new empty database (required) |
| `WEB-INF/config/init-lcm.xml` | Adds Lifecycle Manager starter objects (strongly recommended for lessons) |

Import happens through:

```bash
cd $IIQ_HOME/WEB-INF/bin
./iiq console
> import init.xml
```

---

## 4. IdentityIQ mental model (learn these words)

### Identity (Identity Cube)

The digital representation of a person (or sometimes a service account / machine identity). Built by aggregating one or more sources and correlating accounts.

### Application

A connected system IIQ knows about: HR file, Active Directory, core banking app, AWS, ServiceNow, etc.

Applications have:

- **Connector type** (Delimited File, LDAP, JDBC, …)
- **Schema** (which attributes / entitlements exist)
- **Aggregation** settings (how IIQ reads accounts)
- Optional **provisioning** settings (how IIQ writes changes back)

### Account

A user’s login on one application. One identity can own many accounts.

### Entitlement

A unit of access on an application: group, role, permission flag, profile. In `EmployeeData.txt`, values like `ODS`, `AWS`, and `SAP` are entitlement-like access markers for lab purposes.

### Correlation

The rules that say: “this account on App X belongs to identity Y.”  
Usually based on email, employeeId, or username.

### Aggregation

A task that **pulls** accounts/entitlements from an application into IIQ.

### Identity Refresh

A task that recalculates identity attributes, roles, policies, and (optionally) provisioning needs after data changes.

### Role

A package of access. Common patterns:

- **Birthright / business roles** — given because of job/department
- **IT roles** — technical groupings of entitlements
- **Detected roles** — discovered from existing access patterns

### Lifecycle event

Joiner, mover, leaver (and custom events). Trigger workflows when HR data changes.

### Certification (Access Review)

A campaign where managers / owners attest: keep, revoke, or delegate access. Your `email.txt` shows real-looking notification text for this process.

### Policy

Rules such as Separation of Duties (SoD): “no one should have both *create payment* and *approve payment*.”

### Work item

A human to-do inside IIQ: approve a request, complete a certification, fill a form.

### Workflow

The orchestrated process behind requests, lifecycle events, and many approvals. Editable as XML (advanced) or via product UI features.

### Rule

Small script/logic hooks (often BeanShell/Java) for correlation, customization, provisioning plan modification, etc.

---

## 5. Typical data flow in a bank

Using **Meridian National Bank** (our fictitious company):

```text
1. HR system (or HR CSV) is marked Authoritative
2. Aggregate HR → identities appear / update (joiners, movers, leavers)
3. Aggregate target apps (AD, core banking, cloud) → accounts + entitlements appear
4. Correlation links accounts to identities
5. Roles / birthright policies assign baseline access
6. Employees request extra access → approvals → provisioning
7. Periodic certifications force managers to review access
8. SoD policies flag toxic combinations
9. Audit / reports prove control to regulators
```

That loop is the heart of IGA. Everything else is detail.

---

## 6. How this repo’s sample files map to that flow

### `HRApplications.txt` → Authoritative HR application

Columns include:

`employeeId`, `userName`, `firstName`, `lastName`, `email`, `managerId`, `status`, `departmentCode`, `positionCode`, `jobCode`, `country`, `onLeave`

Use this as a **DelimitedFile** application that creates/updates identities.

### `EmployeeData.txt` → Downstream / target access feed

Columns include:

`userName`, `firstName`, `lastName`, `email`, `jobTitle`, `itAccess`

`itAccess` values (`ODS`, `AWS`, `IBSI`, `ELDAP`, `Ecom`, `SalesForce`, `AS500`, `SAP`, …) simulate entitlements across bank systems. In early lessons you can model this as one multi-entitlement app; later you can split by system.

### `email.txt` → Certification communications

Shows the kind of messages managers get when reviews are assigned or delegations complete. Useful when you configure email in a later lesson (or inspect notification templates).

---

## 7. Local vs production infrastructure

| Topic | Local lab | Production-like |
| --- | --- | --- |
| Hosts | One laptop | Separate app / DB / (often) UI vs task hosts |
| Database | MySQL on localhost | Hardened MySQL/Oracle/SQL Server/Postgres with backups |
| Secrets | Often plaintext temporarily | Encrypted via `iiq encrypt` + keystore practices |
| Connectors | Flat files | AD, LDAP, JDBC, SaaS, mainframe, PAM, cloud |
| Email | Console / file / local SMTP | Enterprise SMTP with templates |
| High availability | No | Load-balanced Tomcats, DB HA |
| Change control | Import XML freely | SSB / deployment pipelines / controlled promotions |

**Learn on the lab. Think like production.** The lessons deliberately use files first so you master governance concepts before fighting network/firewall issues.

---

## 8. Major product areas (where to click later)

Once logged in as `spadmin`, you will gradually use:

| Area | Why it matters |
| --- | --- |
| **Identities** | Inspect cubes, accounts, risk, activity |
| **Applications** | Connect systems, schemas, aggregation |
| **Tasks** | Run aggregations, refreshes, certifications |
| **Roles** | Model job-based access |
| **Policies** | SoD and other controls |
| **Certifications** | Access reviews for auditors |
| **Lifecycle Manager / Quicklinks** | Requests, approvals, lifecycle |
| **Debug / Console** | Import XML, troubleshoot objects |
| **Reports / Advanced Analytics** | Evidence and investigation |

Exact menu labels can vary slightly with LCM activation and UI configuration—use search inside the product when needed.

---

## 9. How IdentityIQ stores “configuration”

Almost everything interesting is an **IIQ object** (Application, TaskDefinition, Bundle/Role, Workflow, Rule, …) stored in the database and exportable as XML.

That is why the console `import` command is so important: it is how labs (and many real projects) load configuration.

Practical habits:

1. Build in UI until it works.
2. Export the object XML.
3. Keep XML in version control for your real projects.
4. Re-import to rebuild environments.

(This training repo starts with docs + sample data; your exported objects can live beside the lessons as you progress.)

---

## 10. Suggested study order

1. Finish [LOCAL_SETUP.md](LOCAL_SETUP.md) until `spadmin` can log in.  
2. Skim this file once (you are here).  
3. Start [lessons/README.md](lessons/README.md) Lesson 01.  
4. Keep official PDFs under `identityiq-8.5/doc/` as reference, not as your first read.

---

## 11. Glossary cheat sheet

| Term | One-line meaning |
| --- | --- |
| IGA | Identity Governance and Administration |
| IIQ | IdentityIQ |
| Authoritative source | System trusted for “who people are” (usually HR) |
| Target / account source | System where accounts/entitlements live |
| Aggregation | Read from a system into IIQ |
| Provisioning | Write from IIQ into a system |
| Correlation | Match accounts to identities |
| Certification | Periodic access attestation |
| SoD | Separation of Duties |
| Work item | Human task inbox item |
| LCM | Lifecycle Manager |
| SSB | Services Standard Build (pro deployment pattern) |
