# Meridian IIQ Teller (chatbot)

Browser chat console over the IdentityIQ **MCP** server.

| Mode | Needs LLM? | What it does |
| --- | --- | --- |
| **Tools rail** | No | Live `tools/list` shortcuts (+ favorites with presets) |
| **Free text** | Yes (OpenRouter) | Native tool-calling agent → MCP `tools/call` (multi-step) |

### Architecture

```
User utterance
  → OpenRouter (tools = live MCP tools/list schemas)
  → tool_calls → MCP tools/call (repeat up to TELLER_MAX_AGENT_STEPS)
  → final model reply (+ optional local summary fallback)
```

There is **no** static LLM tool catalog and **no** hardcoded intent routing.
New MCP tools appear in Teller after cache refresh (`TELLER_TOOL_CACHE_TTL`, default 60s)
or `POST /api/tools/refresh`.

### Operator UX

- Group tabs + collapsible sections (state remembered)
- Collapsible tools rail (desktop + mobile drawer; header toggle)
- Pin up to 8 favorites (★, localStorage)
- Split detail pane for identity/app/JSON (Inspect) — not buried in chat
- Markdown answers, `@` mentions, `/` tool menu, follow-up chips
- Playbooks (JML / SoD / org checks) + `⌘K` / `Ctrl+K` command palette
- Export Q+A+trace from answers (clipboard markdown)
- Tool results enriched with display-name labels for free models
- Free-text chat streams live agent activity (model status, thinking text, tool calls/results) via SSE

## Org Chart

Interactive company hierarchy (zoom / pan / collapse / search / Print-PDF / SVG / PNG):

| URL | Notes |
| --- | --- |
| http://localhost:4180/orgchart.html | Full Meridian layout engine |
| IIQ QuickLink `MNB-QL-Org-Chart` | Opens the same URL |

Data: toolkit `GET /mnbToolkit/agent/orgchart` (UIAPI-59 / MCP `get_orgchart`), with SCIM fallback if the plugin is older.

## Quick start

With the Docker lab stack (preferred):

```bash
export OPENROUTER_API_KEY=sk-or-...   # free models work
./tools/lab/docker/up.sh
open http://localhost:4180/
open http://localhost:4180/orgchart.html
```

Host-only (MCP already on `:8766`):

```bash
export IIQ_MCP_URL=http://127.0.0.1:8766/mcp
export MCP_API_KEY=mnb-lab-mcp-key
export OPENROUTER_API_KEY=sk-or-...
python3 tools/iiq-chat/serve.py
```

## API

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/health` | MCP `/healthz` probe + live tool count + `degraded` |
| GET | `/api/config` | LLM auth + `toolsOnly` / `degraded` + toolCount |
| GET | `/api/actions` | Rail from MCP `tools/list` (+ favorite presets) |
| GET | `/api/playbooks` | Role-scoped suggest + playbooks (`?role=operator\|helpdesk\|lab`) |
| GET | `/api/metrics` | Counters, chat/tool p95 latency, MCP uptime ratio |
| POST | `/api/feedback` | 👍/👎 + reason → `data/feedback.jsonl` |
| POST | `/api/action` | `{ "id": "<tool\|fav:tool>" }` — **no LLM** |
| POST | `/api/chat` | Agent loop (JSON); returns `cards` + `correlationId` |
| POST | `/api/chat/stream` | SSE agent: `run`, `status`, `thought`, `tool_*`, `done` / `error` |
| POST | `/api/chat/cancel` | `{ "runId" }` — stop an in-flight stream |
| POST | `/api/chat/decision` | `{ "runId", "id", "approve" }` — approve/deny a write tool |
| GET | `/api/suggest` | `?q=&kind=all\|identity\|app` — `@` mention autocomplete via MCP |
| GET | `/api/orgchart` | Manager hierarchy forest (`mode`, `root`, `depth`, `includeInactive`) |
| GET | `/api/orgchart/search` | Identity search for chart highlight |
| GET | `/orgchart.html` | Zoomable company org chart UI |
| GET | `/identity/<key>`, `/cert/<id>`, `/app/<name>` | Deep links → Teller + Inspect |
| POST | `/api/tools/refresh` | Force-refresh MCP tool cache |

## Env

| Variable | Default | Purpose |
| --- | --- | --- |
| `CHAT_HOST` / `CHAT_PORT` | `127.0.0.1` / `4180` | Bind |
| `IIQ_MCP_URL` | `http://127.0.0.1:8766/mcp` | MCP endpoint |
| `MCP_API_KEY` | (empty / compose default) | Bearer for Docker MCP |
| `OPENROUTER_API_KEY` | — | Required for free-text |
| `OPENROUTER_MODEL` | `openrouter/free` | Primary free model |
| `OPENROUTER_FALLBACK_MODELS` | several `:free` models | Failover list |
| `TELLER_TOOL_CACHE_TTL` | `60` | Seconds between `tools/list` refreshes |
| `TELLER_MAX_AGENT_STEPS` | `5` | Max LLM↔tool iterations per chat |
| `TELLER_PLAYBOOK_ROLE` | `operator` | Default playbook role (`operator` / `helpdesk` / `lab`) |
| `TELLER_PLAYBOOKS_PATH` | `config/playbooks.json` | Override playbooks file |
| `TELLER_FEEDBACK_PATH` | `data/feedback.jsonl` | Append-only feedback store |

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys). The tools rail works without a key.

### Example utterances

- Who is Anita Rao?
- Do I have anyone named Anita?
- Find me all employees in Paris
- How many open SoD violations are there?

### Tests

```bash
python3 -m pytest tools/iiq-chat/tests -q
```

### Golden intents (live MCP)

```bash
IIQ_MCP_URL=http://127.0.0.1:8766/mcp MCP_API_KEY=mnb-lab-mcp-key \
  python3 tools/iiq-chat/scripts/golden_intents.py
# optional writes (onboard / unlock):
python3 tools/iiq-chat/scripts/golden_intents.py --write
```

### Blackbox agent eval (Teller NL → asserts)

Feeds golden utterances to `POST /api/chat` and asserts on reply + tool steps.
Uses inter-case delay/jitter to stay under free-tier LLM rate limits. See [`eval/README.md`](eval/README.md).

```bash
# list cases
python3 tools/iiq-chat/eval/runner.py --list

# smoke against live Teller (needs OPENROUTER_API_KEY on iiq-chat)
./tools/iiq-chat/scripts/run_teller_eval.sh --tier smoke --delay 12

# core read-only
./tools/iiq-chat/scripts/run_teller_eval.sh --tier core --read-only --delay 10

# open HTML report
open tools/iiq-chat/eval/reports/latest.html   # or xdg-open
```

### Fixing `401 User not found`

That means the key is revoked/invalid. Create a **new** key, then:

```bash
export OPENROUTER_API_KEY='sk-or-v1-...'
docker compose -f docker-compose.iiq.yml up -d --build --force-recreate iiq-chat
```

Confirm: `curl -s http://127.0.0.1:4180/api/config | jq '{llmConfigured,llmAuthOk,agentMode,toolCount}'`
