# Classic 01–110 → Sandbox coverage map (author / planner)

Internal map for enriching Sandbox Path lessons. Enterprise **201–258** is the standalone learner path; classic 01–110 is archive/reference.

| Status | Meaning |
| --- | --- |
| `strong` | Sandbox lesson carries the concept live |
| `partial` | Covered lightly; deepen or extend later |
| `replaced-by-live` | Classic CSV/native path replaced by enterprise targets on purpose |
| `theory` | Honest theory companion (no live IQService/LDIF agent required) |
| `gap` | No honest sandbox counterpart yet (future 259+) |

## Core (01–50)

| Classic | Topic | Sandbox | Status |
| --- | --- | --- | --- |
| 01–03 | Briefing / org / hygiene | 201–202 | partial |
| 04–06 | Auth HR / schema / cubes | 202, 207 | partial |
| 07–08 / 08b | Populations / tasks / triage | **228**, **233**, 245 | strong |
| 09–15 | Delimited onboard | 204–210 | replaced-by-live |
| 10 | Entitlement dictionary | **221**, **227** | strong |
| 16 / 16b | Multi-app agg / Task Results | **233** | strong |
| 17–18 | Correlation | **214** | strong |
| 19 / 19b | Uncorrelated / dirty data | **214** | strong |
| 20 | Orphan / dormant hunt | **219** | strong |
| 21 | Manager hierarchy | **214**, 218, 226 | strong |
| 22 | Attribute sync | **215** | strong |
| 23–28 | Roles (birthright→priv) | **216** | strong |
| 29–34b | JML / LCM | **217–220**, 242 | strong |
| 35–38b | Requests / approvals | **221–223** | strong |
| 38 | IdentityRequest audit | **222**, 230–231 | strong |
| 39–41 | SoD / violations | **224–225** | strong |
| 42 | Risk scores | **225** | strong (prioritize ≠ enforce) |
| 43–46 | Certifications | **226–229** | strong |
| 47–49 | Ops / mail / reports | **230–232**, 203 | strong |
| 50 / 50b | Capstone I | **250** | strong |

## Specialist (51–110)

| Classic | Topic | Sandbox | Status |
| --- | --- | --- | --- |
| 51–52 | Connector registry / selection | **256** | theory |
| 53 | IQService architecture | **257** | theory |
| 54 | Aggregation patterns | **233** | strong |
| 55 | Provisioning feature matrix | **256**, 230, 219 | theory + live |
| 56–58 | AD / LDAP | **204–205**, **234–235** | strong |
| 59 | Entra | 252 | partial (shaped) |
| 60 | LDIF | **258** | theory |
| 61–62 | Passwords / auth vs target | 206, **254** | strong |
| 63–64 | JDBC | **208**, **236** | strong |
| 65–67 | MSSQL / Oracle / SQLLoader | — | gap |
| 68–70 | WS / SCIM | **209–210**, **237–238** | strong |
| 71 | Salesforce native | 210 | replaced-by-live |
| 72 | ITSM | **239** | strong |
| 73 | Okta / IdP | **211–213**, 253 | strong (Keycloak) |
| 74–76 | Google / M365 / AWS | — | gap |
| 77 | Workday | **207** | strong (shaped) |
| 78–82 | SAP / PS / EBS / RACF | — | gap |
| 83–84 | Linux / Windows local | **251** | partial |
| 85 | Logical apps | **240** | strong |
| 86 | PAM / CyberArk | **255** | strong (shaped) |
| 87–88 | Duo / Cloud Gateway | — | gap |
| 89–92 | Rule catalog / BeanShell / IdAttr | **241** | strong |
| 91 / 93–96 | Prov rules, WF, forms, QL, scopes | **241–245** | strong |
| 97–99 | Plugins / console | **246** | partial |
| 100–101 / 108 | REST / SSD | **247–248** | strong |
| 102–103 | Custom Java / branding | **248**, 201 | strong (branding); Java gap |
| 104 | Audit / SIEM | **231** | partial |
| 105–109 | Partition / perf / DR / harden | **249** | partial (lite) |
| 110 | Blueprint capstone | **250** | strong |

## Net-new (beyond classic)

| Sandbox | Focus |
| --- | --- |
| 212–213, 251, 253 | Portal / Gitea / workstation / intranet SSO proofs |
| 255 | Vault + pam-lab checkout |
| 256–258 | Theory: registry, IQService, LDIF |

## Suggested later (259+)

Native Google/M365/AWS, SAP Direct, MFA gate (87), plugin authoring depth, DR recovery drill, live IQService Windows lab (optional beyond 257 theory).
