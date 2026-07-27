# Meridian academy object packs (`config/`)

Rightly scoped IdentityIQ objects for the Meridian National Bank academy — the same components a forward-deployed IAM engineer would promote, **not** a full HA bank tenant.

Lab CSV fixtures stay in [`lab-data/`](../lab-data/). IIQ **object** truth lives here. Env paths use `%%TOKENS%%` from `*.target.properties`.

## Pack inventory

| Pack | Objects | Lessons |
| --- | --- | --- |
| **Smoke** | `Rule/MNB-Rule-HelloWorld.xml` | CD / Lesson 03 |
| **P1 HR slice** | `Application/MNB-Application-HR.xml`, `CorrelationConfig/MNB-CorrelationConfig-HR-EmployeeId.xml`, `Rule/MNB-Rule-Correlation-EmployeeId.xml`, `TaskDefinition/MNB-TaskDefinition-Aggregate-HR.xml`, `TaskDefinition/MNB-TaskDefinition-Refresh-Attributes.xml`, `TaskDefinition/MNB-TaskDefinition-Refresh-Managers.xml` | 04–06, 08 |
| **Inventory** | `Application/MNB-Application-IT-Access.xml`, `TaskDefinition/MNB-TaskDefinition-Aggregate-IT-Access.xml` | 09–10 |
| **Target apps** | `Application/MNB-Application-CoreBanking.xml`, `Application/MNB-Application-WirePortal.xml`, `Application/MNB-Application-SAP-Finance.xml`, `Application/MNB-Application-AWS-Cloud.xml` + aggregate tasks | 11–16 |
| **Roles** | `Bundle/MNB-Bundle-Birthright-Employee.xml`, `Bundle/MNB-Bundle-IT-Directory-User.xml` | 23–28 |
| **LCM** | `Workflow/MNB-Workflow-Joiner.xml`, `Workflow/MNB-Workflow-Leaver.xml`, `EmailTemplate/MNB-EmailTemplate-Joiner-Notify.xml` | 29–34, 49 |
| **SoD** | `Policy/MNB-Policy-SOD-Wire-Dual-Control.xml` | 39–41 |
| **Refresh shells** | `TaskDefinition/MNB-TaskDefinition-Refresh-Roles.xml`, `TaskDefinition/MNB-TaskDefinition-Refresh-Policies.xml` | 06, 08, 23+, 39+ |

HR CSV uses a **production-style bank header** (`userId`, `managersAssociateID`, `inactive`, `exceptions=LOA`, …). See [`lab-data/reference/hr-column-map.md`](../lab-data/reference/hr-column-map.md).

## Import

```bash
export SPTARGET=sandbox   # or homelab
# Set %%MNB_*_FILE%% tokens to absolute lab-data paths first
./build.sh clean war
./build.sh importdynamic
```

Homelab CD imports `sp.init-custom.xml` after rollout; see [`docs/HOMELAB-CD.md`](../docs/HOMELAB-CD.md) and [`tools/iiq-verify/assert-mnb-objects.sh`](../tools/iiq-verify/assert-mnb-objects.sh).

## Naming

| In git | Typical IIQ display / task name |
| --- | --- |
| `MNB-Application-HR.xml` | Application `MNB-HR` |
| `MNB-TaskDefinition-Aggregate-HR.xml` | Task `Aggregate MNB-HR` |
| `MNB-TaskDefinition-Refresh-Attributes.xml` | Task `Refresh MNB Attributes` |

Lesson UI may still say “create `MNB-HR`”; bank craft exit is: object matches this pack (import-first) or is exported here (UI-first).
