# IdentityIQ MCP Server

Python **FastMCP** server that exposes SailPoint IdentityIQ to agents over **streamable HTTP**.
Phase 1–4 tools are wired to SCIM, OOTB REST, and Meridian Custom APIs; only three permanent
exclusions remain as stubs (`update_rule_source`, `grant_capability`, `update_scope`).

## Quick start (lab)

**Preferred (Docker stack includes MCP + OpenAPI):**

```bash
./tools/lab/docker/up.sh
# MCP → http://127.0.0.1:8766/mcp  (Bearer mnb-lab-mcp-key)
# OpenAPI → http://localhost:8765/swagger/
```

**Host path (venv on the laptop):**

```bash
cd tools/iiq-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install '.[dev]'          # prefer regular install (editable .pth is flaky on some Pythons)
# for local iteration: ./run.sh always sets PYTHONPATH=src

# Regenerate OpenAPI operation index (optional; committed artifact included)
python -m iiq_mcp.client.generate_index

cp .env.example .env
# set IIQ_PASSWORD (and preferably MCP_API_KEY)

./run.sh
# listens on http://127.0.0.1:8766/mcp
```

Or via the lab helper: `./tools/lab/up.sh --sidecars-only` (creates venv + `.env` if missing).

Health check: `GET http://127.0.0.1:8766/healthz`

### Claude Code (user or project MCP)

The server speaks **HTTP** (`http://127.0.0.1:8766/mcp`). Start it first (Compose `up.sh` or `./run.sh`), then register:

```bash
# Docker lab stack (default key)
claude mcp add --scope user --transport http identityiq http://127.0.0.1:8766/mcp \
  --header "Authorization: Bearer mnb-lab-mcp-key"

# Host loopback with empty MCP_API_KEY (no header)
claude mcp add --scope user --transport http identityiq http://127.0.0.1:8766/mcp
```

Restart Claude Code (or start a new session). Verify with `/mcp` inside Claude Code, or:

```bash
claude mcp list
claude mcp get identityiq
```

Then ask naturally, e.g. “List SCIM users named helen” or “Run Identity Refresh via the toolkit.”

IIQ credentials stay in `tools/iiq-mcp/.env` — Claude Code never sees them.

## Phase gating

| Env | Default | Meaning |
| --- | --- | --- |
| `IIQ_MCP_ENABLED_PHASES` | `1,2,3,4` | Comma-separated phases whose tools may execute |

Use `1` alone for read-only. Include `2`+ for Custom API writes (`create_application`, access requests, …) and `4` for admin/advanced ops (NCD, plugins, system config, object import).

Higher-phase tools remain **visible** but return `{ ok: false, error: { code: "phase_disabled" } }`
or `not_implemented` for permanent exclusions.

## Phase 1 — implemented

Identity (SCIM Users/Accounts), Applications (SCIM), Certifications (OOTB REST, experimental),
PolicyViolations (SCIM), Work items (partial OOTB read), TaskResults + `run_task_now` (Meridian
plugin). Response lists are trimmed + paginated; pass `raw=true` for full payloads.

## Extended catalog (phases 2–4)

Previously stubbed tools are wired to SCIM, OOTB REST, and/or Meridian
`/plugin/rest/mnbToolkit/agent/*` (requires `agentApiEnabled` and domain flags). Enable with
`IIQ_MCP_ENABLED_PHASES=1,2,3,4`. Writes still carry `[REQUIRES_CONFIRMATION]` and write-audit JSONL.

High-ROI OOTB/SCIM extensions live in `impl_ops_ext.py` (platform ping/status/hosts, SCIM
Schemas/ObjectConfigs, managed entitlements/roles via agent, work-item archive, workflow
metadata, provisioning status counts, …).

## Permanent exclusions (still stubs)

| Tool | Why |
| --- | --- |
| `update_rule_source` | Runtime code change — not an agent tool |
| `grant_capability` | Excluded *name* — use **`assign_identity_capability`** (Custom APIs + `mutateGovernanceEnabled`) |
| `update_scope` | Data-segmentation admin |

Custom API gap tools (wizard, forms, plugins, NCD, object XML, system config merge, …) are in
`src/iiq_mcp/tools/impl_custom_apis.py` — see [`docs/api/MCP-TOOLS.md`](../../docs/api/MCP-TOOLS.md).

Some best-effort tools (forward/escalate work item, campaign launch, provisioning retry) return
structured errors when the lab IIQ path is missing — keep Meridian toolkit flags enabled.

## Tests & smoke

```bash
pytest
python scripts/smoke_phase1.py   # skips if IIQ is down
```

## Layout

See `src/iiq_mcp/` — client (httpx + OpenAPI index), cross-cutting (errors, shaping, rate limit,
audit JSONL, idempotency SQLite), tools (phase1_* + `catalog.yaml` stubs), `server.py`.

Never backs tools on `/ui/rest`. Pin against IdentityIQ **8.5** lab surfaces in `docs/api/openapi/`.
