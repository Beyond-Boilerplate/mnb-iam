# IdentityIQ API catalog (`docs/api`)

Bytecode-mined OpenAPI 3 documentation for **SailPoint IdentityIQ 8.5** as packaged in this SSD lab, plus Meridian/plugin REST from `pluginsrc/`.

## Browse (Swagger + CORS-safe proxy)

Do **not** use bare `python -m http.server` if you want Try-it-out against IIQ — the browser blocks `localhost:8765` → `localhost:8080` (CORS). Prefer the lab stack:

```bash
./tools/lab/docker/up.sh          # includes api-docs on :8765
# or host path:
./tools/lab/up.sh --sidecars-only # or full ./tools/lab/up.sh
# open http://127.0.0.1:8765/swagger/
```

Manual (no Compose):

```bash
./docs/api/serve.py
# open http://127.0.0.1:8765/swagger/
# Spec dropdown defaults to **Meridian Custom APIs**
```

1. Select **SCIM 2.0 /scim/v2** (or another spec).
2. Click **Authorize** → Basic auth (`spadmin` / lab password, or `mnb.api.lab`).
3. Execute — requests go to **same origin** `/identityiq/...` and are proxied to `:8080`.

| Entry | Purpose |
| --- | --- |
| [swagger/index.html](swagger/index.html) | Swagger UI (CDN) over the YAML specs |
| [serve.py](serve.py) | Static docs + `/identityiq/*` reverse proxy |
| [openapi/](openapi/) | Per-surface OpenAPI YAML |
| [openapi/openapi-meridian-agent.yaml](openapi/openapi-meridian-agent.yaml) | Meridian Custom APIs |
| [MCP-TOOLS.md](MCP-TOOLS.md) | MCP tool ↔ OpenAPI map for UIAPI gaps |
| [CATEGORIES.md](CATEGORIES.md) | Category × surface cross-cut |
| [inventory/mined-endpoints.json](inventory/mined-endpoints.json) | Raw mined inventory |
| [GAPS.md](GAPS.md) | Completeness + tracked gaps (incl. sample API) |
| [UI-VS-API-GAPS.md](UI-VS-API-GAPS.md) | UI can do X but no clean agentic API |

## Working curl (no CORS)

SCIM Accounts (empty list is a valid 200 when no accounts are aggregated yet):

```bash
curl -sS -u 'spadmin:admin' \
  -H 'Accept: application/scim+json' \
  'http://localhost:8080/identityiq/scim/v2/Accounts' | python3 -m json.tool
```

Users example:

```bash
curl -sS -u 'spadmin:admin' \
  -H 'Accept: application/scim+json' \
  --get 'http://localhost:8080/identityiq/scim/v2/Users' \
  --data-urlencode 'filter=userName eq "helen.ross"'
```

Prefer `mnb.api.lab` + `--netrc-file` in shared labs (Lesson 100).

## MCP server (agent tools)

Lab/agent HTTP MCP for IdentityIQ lives in [`tools/iiq-mcp/`](../../tools/iiq-mcp/) (FastMCP,
Phase 1 SCIM/REST tools + full catalog stubs).

**Preferred:** start with the lab stack so MCP comes up with IIQ:

```bash
./tools/lab/docker/up.sh
# MCP → http://127.0.0.1:8766/mcp  (Bearer mnb-lab-mcp-key)
```

Host-only: `./tools/lab/up.sh --sidecars-only` or from that directory `pip install .` then `./run.sh`.
See its README for Cursor wiring and phase gating.

## Specs by type / surface

| File | Mount | Type |
| --- | --- | --- |
| `openapi-ootb-rest.yaml` | `/identityiq/rest` | Product integration REST |
| `openapi-ui-rest.yaml` | `/identityiq/ui/rest` | Product UI backend (not ITSM contract) |
| `openapi-scim-v2.yaml` | `/identityiq/scim/v2` | SCIM 2.0 server |
| `openapi-oauth2.yaml` | `/identityiq/oauth2` | OAuth clients/tokens |
| `openapi-external-rest.yaml` | `/identityiq/external/rest` | Limited external helpers |
| `openapi-plugins.yaml` | `/identityiq/plugin/rest` | Custom plugins (Meridian toolkit + study) |
| `openapi-meridian-agent.yaml` | `/identityiq/plugin/rest` | Meridian Custom APIs (UIAPI-01…27) |
| `openapi-iiq-bundle.yaml` | — | Index of the above |

Within each file, operations are **tagged by category** (identities, certifications, workflows, …) inferred from resource class/path names.

## Regenerate (continuous mining)

Requires extracted WAR libs (`build/extract/WEB-INF/lib/identityiq.jar`, `scim-server.jar`):

```bash
./tools/iiq-api-mine/run.sh
```

Techniques used:

1. Java **class-file constant pool** parse  
2. `RuntimeVisibleAnnotations` / `RuntimeVisibleParameterAnnotations`  
3. Mount map from product `web.xml` prefixes  
4. `pluginsrc` Java source mining for custom REST  
5. Gap report synthesis  

## Sample APIs

### Ping (GAP-PLUGIN-001)

```http
GET /identityiq/plugin/rest/mnbToolkit/ping
```

### Task run — aggregation / refresh (UIAPI-01/02)

```bash
curl -sS -u 'spadmin:admin' -H 'Content-Type: application/json' \
  -d '{"taskName":"Refresh Identity Cube","sync":false,"args":{}}' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/tasks/run'
```

Requires plugin **installed** in IIQ (`./pluginsrc/mnb-iam-toolkit/install.sh`), then settings `taskRunEnabled=true` and `allowedTaskNames=…`. See `pluginsrc/mnb-iam-toolkit/README.md`.

### Agent orchestration (UIAPI-03…27)

```bash
# Discovery matrix + flags
curl -sS -u 'spadmin:admin' \
  'http://localhost:8080/identityiq/plugin/rest/mnbToolkit/agent/gaps' | python3 -m json.tool
```

Requires toolkit **1.2.1+**, right `MNBToolkitAgent`, and `agentApiEnabled=true`. OpenAPI: [openapi-meridian-agent.yaml](openapi/openapi-meridian-agent.yaml). MCP tools: [MCP-TOOLS.md](MCP-TOOLS.md). Gap register: [UI-VS-API-GAPS.md](UI-VS-API-GAPS.md).

Regenerate agent OpenAPI:

```bash
python3 tools/iiq-api-mine/generate_meridian_agent_openapi.py
```

## Auth reminder

Prefer dedicated API identities (`mnb.api.*`), least privilege, TLS outside pure local lab — Lesson 100.
