# Lessons 51–110 — Exhaustive connector & enterprise customization catalog

Follow `docs/lessons/_STYLE.md`. Lab-without-live-target is mandatory for every connector lesson.
Personas/objects: Meridian `MNB-*`, `~/iiq-lab-data/connectors/`, `docker-compose.connectors.yml`.
Prev of 51 = `50-capstone-exam-readiness.md`. After 110 = curriculum complete (ultimate blueprint).

## Connector Architecture — 51–55
51 connector-landscape-and-registry — ConnectorRegistry, featuresString, template apps
52 connector-selection-for-meridian — matrix CSV; map every Meridian system
53 iqservice-architecture — Windows IQService, TLS, AD dependency
54 aggregation-patterns-advanced — full/delta/partition/filter/multi-host
55 provisioning-feature-matrix — ENABLE/PASSWORD/UNLOCK/SYNC; test matrix

## Directory & Cloud IdP — 56–62
56 active-directory-connector — AD Direct app shell + checklist
57 ad-groups-ous-exchange — OU moves, group types, mailbox notes
58 ldap-openldap-connector — OpenLDAP Direct; LDIF bootstrap
59 azure-entra-id-connector — Azure AD / Entra ID
60 ldif-connector — offline directory dumps
61 password-management-interceptor — password policies + interceptor design
62 directory-authoritative-vs-target — AD as target not HR truth

## Databases — 63–67
63 jdbc-connector-fundamentals — JDBC app + SQL fixtures
64 jdbc-provisioning-policies — create/update/delete SQL / procs
65 mssql-direct-connector — Microsoft SQL Server Direct
66 oracle-db-direct-connector — Oracle Database Direct
67 sqlloader-bulk-patterns — SQLLoader / bulk

## Web APIs & SaaS — 68–76
68 web-services-connector — REST ops mapping; Wire Portal OpenAPI
69 scim2-connector — SCIM 2.0
70 scim-custom-schemas — extensions / enterprise attributes
71 salesforce-native-connector — Salesforce connector (not CSV)
72 servicenow-connector — ServiceNow accounts + ticket hooks
73 okta-connector — Okta workforce IdP
74 google-workspace-connector — Google / G Suite
75 m365-sharepoint-online — Office365 / SharePoint Online
76 aws-iam-connector — AWS / AWS IAM

## ERP / HR / Banking platforms — 77–82
77 workday-hcm-connector — Workday authoritative patterns
78 sap-hr-hcm-connector — SAP HR/HCM
79 sap-direct-security — SAP Direct app roles
80 peoplesoft-hcm-connector — PeopleSoft HCM / Direct
81 oracle-ebs-connector — Oracle E-Business
82 mainframe-racf-banking — RACF for core banking security

## Infra, Logical, PAM — 83–88
83 linux-unix-connector — Linux Direct / Unix
84 windows-local-connector — Windows Local
85 logical-applications — Logical composite apps
86 pam-cyberark-module — PAM / CyberArk privileged
87 duo-mfa-integration-patterns — MFA adjacent (Duo) governance notes
88 connector-gateway-cloud-patterns — Cloud Gateway / hybrid patterns

## Rules, Workflows, Forms — 89–96
89 rule-types-catalog — all major rule types
90 beanshell-vs-java-rules — when to compile
91 before-after-provisioning-rules — plan mutation
92 identity-attribute-rules — computed attrs
93 workflow-lcm-customization — LCM workflow edits + versioning
94 forms-and-field-validation — provisioning forms
95 quicklinks-custom-ui — QuickLinks
96 workgroups-capabilities-scopes — who can do what

## Plugins, APIs, SSD — 97–103
97 plugin-framework-basics — manifest, install
98 build-meridian-toolkit-plugin — scaffold plugin
99 iiq-console-and-automation — iiq console scripting
100 iiq-rest-scim-apis — IIQ as API server
101 ssb-ssd-promotion-discipline — export/import SSB
102 custom-java-services — Request processors / services
103 ui-customization-branding — UIConfig / branding / messages

## Enterprise hardening & mastery — 104–110
104 auditconfig-and-siem — AuditConfig, SIEM feed
105 partitioning-task-servers — hosts, partitioning
106 performance-tuning-iiq — caches, indexes, thread pools
107 backup-dr-object-recovery — DR for IIQ objects/DB
108 multi-env-promotion — sandbox→dev→prod
109 hardening-spadmin-capabilities — least privilege admin
110 ultimate-blueprint-capstone — full Meridian production blueprint (longest)

Filename pattern: `NN-slug.md` (e.g. `51-connector-landscape-and-registry.md`).
Level: Intermediate unless noted Advanced for 86,91,93,98,102,106–110.
Time: 60–90 min typical; 110 = 120–150 min.
