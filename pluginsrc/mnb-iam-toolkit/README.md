# Meridian Custom APIs (`mnb_iam_toolkit`)

Version **1.3.17** · Plugin **name** must be letters/numbers/`_` only (`mnb_iam_toolkit`).  
Display name: **Meridian Custom APIs**. Repo folder may stay `pluginsrc/mnb-iam-toolkit/`.

Owner: **helen.ross** / `MNB-WG-IAM-Ops`

| Version | Closes |
| --- | --- |
| 1.0.0 | GAP-PLUGIN-001 (ping) |
| 1.1.0 | UIAPI-01/02 (allowlisted task run) |
| 1.2.x | UIAPI-03…19 + reject postures for 07/08/20–26 |
| 1.3.0 | UIAPI-07/08/20–26 implemented; rename to Meridian Custom APIs |
| 1.3.1 | UIAPI-07 wizard clones ConnectorRegistry template (real DelimitedFile connector defaults); accessRequests rejects empty items / failed launches |
| 1.3.12 | UIAPI-60…80 MCP parity wave: console desks, SoD list/delete/constraints, workgroup/QL/email CRUD, schema/correlation, lifecycle, ObjectConfig/PasswordPolicy, role requirements, form→workflow |
| 1.3.13 | UIAPI-81…83: provisioning policy Forms, SoD simulate, GroupFactory upsert/run |
| 1.3.14 | UIAPI-84…86 + accessRequest sunset/formAnswers: capability rights, role selector, cert definition patch |
| 1.3.16 | UIAPI-97/98/105–107/139: workflow patch, form upsert, connector deep config, SoD matrix import; gaps honesty for 91–167 |
| 1.3.15 | UIAPI-87…90: identity forwarding/OOO, risk score weights, TaskDefinition upsert, aggregation stop |

## Build + install

```bash
# Preferred (uses ssdplugins zip, or stages jars from running mnb-identityiq, or SSB extract)
./pluginsrc/mnb-iam-toolkit/ensure-plugin-zip.sh
./pluginsrc/mnb-iam-toolkit/install.sh
# Reinstall clears setting values — re-check:
./pluginsrc/mnb-iam-toolkit/enable-settings.sh
```

`./tools/lab/docker/up.sh` calls the same path automatically. Version is centralized in [`version.env`](version.env).

| Helper | Role |
| --- | --- |
| `ensure-plugin-zip.sh` | dist ← ssdplugins, else `stage-iiq-libs` + `package.sh` |
| `stage-iiq-libs.sh` | Fill `build/extract/WEB-INF/lib` from SSB WAR or `docker cp` from `mnb-identityiq` |
| `package.sh` / `compile.sh` | Rebuild from source when no committed zip |

### Settings

| Setting | Purpose | Default |
| --- | --- | --- |
| `taskRunEnabled` | Task launch kill switch | false |
| `allowedTaskNames` | Comma patterns | empty |
| `agentApiEnabled` | Master switch for `/mnbToolkit/agent/*` | false |
| `mutateGovernanceEnabled` | Work items / certs / SoD / LCM / capabilities | false |
| `passwordResetEnabled` | Password set / unlock | false |
| `advancedOpsEnabled` | App config, NCD, system config write, object import, plugin enable/install | false |

```bash
curl -sS -u 'spadmin:admin' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/ping'

curl -sS -u 'spadmin:admin' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/agent/gaps'
```

## REST contracts

| Op | Path | Right |
| --- | --- | --- |
| Ping | `GET /mnbToolkit/ping` | `MNBToolkitAccess` |
| Tasks | `/mnbToolkit/tasks/*` | `MNBToolkitTaskRun` |
| Custom APIs | `/mnbToolkit/agent/*` | `MNBToolkitAgent` |

OpenAPI: [`docs/api/openapi/openapi-meridian-agent.yaml`](../../docs/api/openapi/openapi-meridian-agent.yaml) · MCP: [`docs/api/MCP-TOOLS.md`](../../docs/api/MCP-TOOLS.md).
