# Meridian Custom APIs (`mnb_iam_toolkit`)

Version **1.3.0** · Plugin **name** must be letters/numbers/`_` only (`mnb_iam_toolkit`).  
Display name: **Meridian Custom APIs**. Repo folder may stay `pluginsrc/mnb-iam-toolkit/`.

Owner: **helen.ross** / `MNB-WG-IAM-Ops`

| Version | Closes |
| --- | --- |
| 1.0.0 | GAP-PLUGIN-001 (ping) |
| 1.1.0 | UIAPI-01/02 (allowlisted task run) |
| 1.2.x | UIAPI-03…19 + reject postures for 07/08/20–26 |
| 1.3.0 | UIAPI-07/08/20–26 implemented; rename to Meridian Custom APIs |
| 1.3.1 | UIAPI-07 wizard clones ConnectorRegistry template (real DelimitedFile connector defaults); accessRequests rejects empty items / failed launches |

## Build + install

```bash
./pluginsrc/mnb-iam-toolkit/package.sh
./pluginsrc/mnb-iam-toolkit/install.sh
# Reinstall clears setting values — re-check:
./pluginsrc/mnb-iam-toolkit/enable-settings.sh
```

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
