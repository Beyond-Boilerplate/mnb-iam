# Meridian academy — what CD ships vs what learners build

CD / SSB image ships **only** a smoke Rule so homelab import stays healthy:

| In git (CD) | IIQ name | Purpose |
| --- | --- | --- |
| `Rule/MNB-Rule-HelloWorld.xml` | `MNB-Rule-Hello-World` | Deploy smoke / Lesson 03 SSB awareness |

**Everything else** for Core Path (`MNB-HR`, IT Access, target apps, refresh tasks, roles, LCM, SoD, correlation) is **built by the learner in the lessons**, then optionally exported into the matching `config/<Type>/` folder for promotion practice (Lesson 101+).

## Packs

| Pack | When | Contents |
| --- | --- | --- |
| **Academy (CD)** | Always on image | HelloWorld only |
| **Lab seed** | `./tools/lab/docker/up.sh` (default) | `MNB-HR`, `MNB-OpenLDAP`, CSV stubs, daily agg tasks |
| **Enterprise** | `./tools/lab/docker/up.sh --enterprise` + `seed-enterprise.sh` | Live AD (Samba LDAP), Workday-shaped WS, Okta-shaped SCIM, JDBC Core, CRM SCIM, ITSM WS, LCM triggers/workflows, QuickLinks, cert definitions, birthright bundles |

Enterprise guide: [`docs/ENTERPRISE-LAB-V2.md`](../docs/ENTERPRISE-LAB-V2.md)

### Enterprise objects (git)

| Path | Name |
| --- | --- |
| `Application/MNB-Application-Workday.xml` | `MNB-Workday` |
| `Application/MNB-Application-ActiveDirectory-Live.xml` | `MNB-ActiveDirectory-Live` |
| `Application/MNB-Application-Okta.xml` | `MNB-Okta` |
| `Application/MNB-Application-CoreBanking.xml` | `MNB-CoreBanking` |
| `Application/MNB-Application-Salesforce-CRM-Live.xml` | `MNB-Salesforce-CRM-Live` |
| `Application/MNB-Application-ServiceNow.xml` | `MNB-ServiceNow` |
| `Application/MNB-Application-EntraID.xml` | `MNB-EntraID` (Entra-shaped SCIM mock) |
| `Bundle/MNB-Bundle-Workstation-Access.xml` | Workstation login gate role |
| `Bundle/MNB-Bundle-HR-Intranet.xml` / `Finance-Portal` | Intranet SSO roles |
| `Application/MNB-Application-PAM-CyberArk.xml` | `MNB-PAM-CyberArk` (Vault-backed PAM facade) |
| `Bundle/MNB-Bundle-BreakGlass-Cloud.xml` | Cloud break-glass → PAM safe |
| `PasswordPolicy/MNB-PasswordPolicy-Lab.xml` | Lesson 61 / 254 live policy |
| `IdentityTrigger/MNB-IdentityTrigger-*.xml` | Joiner / Leaver |
| `Workflow/MNB-Workflow-*.xml` | Joiner / Leaver / Access Approval |
| `Bundle/MNB-Bundle-*.xml` | Birthright + Wire Initiator |
| `QuickLink/MNB-QuickLink-*.xml` | Request, work items, certs, portal, toolkit |
| `CertificationDefinition/MNB-CertificationDefinition-*.xml` | Manager + App-owner Wire |

Import: `./tools/lab/enterprise/seed-enterprise.sh`

## Lab CSV truth (not IIQ objects)

Fixtures stay in [`lab-data/`](../lab-data/). Copy to `~/iiq-lab-data/` before Lesson 04. HR uses a **production-style bank header** — see [`lab-data/reference/hr-column-map.md`](../lab-data/reference/hr-column-map.md).

| Concept | Bank column |
| --- | --- |
| Native ID | `userId` |
| Login | `name` |
| Manager | `managersAssociateID` → manager `userId` |
| Leaver | `inactive=true`, `status=Terminated` |
| LOA | `exceptions=LOA` (still Active) |
| Type | `employeeType` / `userType` |
| Org / job | `departmentName`, `division`, `JobCode`, `costCenter` |

IT dumps still use `employeeId` (= HR `userId` for correlation).

Enterprise identity master (unified seed): [`lab-data/enterprise/identity-master.json`](../lab-data/enterprise/identity-master.json).

## Learner export targets (after the lesson that creates them)

| Lesson creates | Suggested git path when exporting |
| --- | --- |
| 04 `MNB-HR` | `config/Application/MNB-Application-HR.xml` |
| 05–06 refresh / maps | TaskDefinitions + ObjectConfig notes |
| 09 `MNB-IT-Access` | `config/Application/MNB-Application-IT-Access.xml` |
| 11–14 target apps | `config/Application/MNB-Application-*.xml` |
| 23–24 roles | `config/Bundle/MNB-Bundle-*.xml` |
| 29–31 LCM | `config/Workflow/…`, EmailTemplate |
| 39–40 SoD | `config/Policy/…` |

Env file paths use `%%MNB_*_FILE%%` tokens in `*.target.properties` once you export Applications.

## Verify CD smoke only

```bash
./tools/iiq-verify/assert-mnb-objects.sh local   # HelloWorld only
```

Enterprise smoke:

```bash
./tools/lab/enterprise/e2e-smoke.sh
./tools/lab/enterprise/contract-tests.sh
```
