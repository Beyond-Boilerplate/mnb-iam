# IdentityIQ `config/` — SSD/SSB customization root

This folder is the **source of truth** for IdentityIQ XML objects in the Services Standard Build.

## Academy model

Homelab CD imports **only** the smoke Rule (`Rule/MNB-Rule-HelloWorld.xml`). Learners **build** Meridian applications, tasks, roles, workflows, and policies **in the lessons**, then **export** durable objects here for promotion practice.

See [PACKS.md](PACKS.md).

## How to add a feature (after you built it in IIQ)

1. Export the object from IIQ (Debug → export, or Object Exporter) with **clean** XML.
2. Place it under the matching type folder:

   `MNB-<Type>-<BusinessName>.xml`

   Examples:
   - `Application/MNB-Application-HR.xml`
   - `Bundle/MNB-Bundle-Birthright-Employee.xml`
   - `Rule/MNB-Rule-Correlation-EmployeeId.xml`
   - `Workflow/MNB-Workflow-Joiner.xml`
   - `Policy/MNB-Policy-SOD-Wire-Dual-Control.xml`

3. Use `%%TOKENS%%` from `*.target.properties` for env-specific values (file paths, hosts).
4. Build & import:

```bash
export SPTARGET=sandbox
./build.sh clean war
./build.sh importdynamic
```

## Folder map (SSB standard)

| Folder | Object type |
| --- | --- |
| `Application/` | Applications / connectors |
| `Bundle/` | Roles |
| `Rule/` / `RuleLibrary/` | Rules |
| `Workflow/` | Business processes |
| `TaskDefinition/` | Aggregation, refresh, cert tasks |
| `Policy/` | SoD / policies |
| `EmailTemplate/` | Notifications |
| `Form/` | Forms |
| `IdentityTrigger/` | Lifecycle triggers |
| `QuickLink/` | Quicklinks |
| `Configuration/` / `ObjectConfig/` / `UIConfig/` | System config overlays |
| `Custom/` | Custom objects |

## Verify CD smoke

```bash
./tools/iiq-verify/assert-mnb-objects.sh local
```
