# IdentityIQ `config/` — SSD/SSB customization root

This folder is the **source of truth** for IdentityIQ XML objects in the Services Standard Build.

## How to add a feature

1. Export the object from IIQ (Debug → export, or Object Exporter task) with **clean** XML.  
2. Place it under the matching type folder using the Meridian naming convention:

   `MNB-<Type>-<BusinessName>.xml`

   Examples:
   - `Application/MNB-Application-HR.xml`
   - `Bundle/MNB-Bundle-Birthright-Employee.xml`
   - `Rule/MNB-Rule-Correlation-Email.xml`
   - `Workflow/MNB-Workflow-Joiner.xml`
   - `Policy/MNB-Policy-SOD-Finance-Cloud.xml`

3. Use `%%TOKENS%%` from `sandbox.target.properties` / `dev.target.properties` for env-specific values (hosts, file paths, passwords).  
4. Build & deploy:

```bash
export SPTARGET=sandbox   # or: ./build.sh -Dtarget=sandbox …
./build.sh clean war
./build.sh deploy         # copies into IIQHome from build.properties
```

5. Import dynamic objects (if not using full WAR deploy):

```bash
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
| `SSF_*` / `SSP_*` | SailPoint Services frameworks (enable via `build.properties`) |

## Meridian National Bank

Lesson work should land here as XML exports so CI/CD can promote `sandbox → dev → test → prod` with the same Git history.

**Academy packs:** see [PACKS.md](PACKS.md) for the rightly scoped object inventory (HR slice, inventory, target apps, roles, LCM stubs, SoD). Learner setup imports these packs — same path Meridian Ops uses for promotion.

Ignore environment-only files via `sandbox.ignorefiles.properties` (and siblings).

### Verify after import

```bash
./tools/iiq-verify/assert-mnb-objects.sh local   # laptop IIQ_HOME
./tools/iiq-verify/assert-mnb-objects.sh k8s     # homelab pod
```
