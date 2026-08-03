# Auto-story Jira runner

Visibility-first control plane for an allowlisted **MCP_E2E** lane on Meridian KAN.

**Terminal auto state:** In Review only. **Never** auto-Done.

**Implement agent:** Teller-class (OpenAI-compatible tool loop → IIQ MCP), same shape as `tools/iiq-chat`.  
**LLM:** config-swappable (`openrouter` default; `openai` / `azure_openai` / `gemini_openai_compat` via `base_url` + key).

## Board contract (Phase 0)

| Label | Meaning |
| --- | --- |
| `agent-ready` | Issue may enter the auto-story Ready queue |
| `blocked-needs-human` | Runner escalated; do not re-claim until cleared |
| Work-type (optional) | `identity-admin`, `app-onboarding`, `task-ops`, `access-request`, … |

Ready JQL (also in [`../jira/status_map.yaml`](../jira/status_map.yaml)):

```text
project = KAN AND labels = "agent-ready" AND status = "To Do" ORDER BY created ASC
```

(mnbiam KAN: status name **To Do** is mis-mapped to statusCategory **Done**, so we match on status name.)

Bot identity: `JIRA_SITE`, `JIRA_EMAIL` (or `JIRA_BOT_EMAIL`), `JIRA_API_TOKEN`.

Policy exception vs root `CLAUDE.md`: for **agent-ready** issues only, the runner may auto-transition **To Do → In Progress → In Review** without a human chat confirm. It must never transition to **Done**.

## UI (Teller)

Open **[Auto-story](http://localhost:4180/auto-story.html)** from the Teller masthead (or Console / Org Chart).

- **Queue** — **Poll Jira** for `agent-ready` To Do issues; select one → **Dry-run** or **Start live** (confirm dialog; never Done)
- **Live process banner** — while a job runs, UI attaches to the ledger ASAP and streams THINK / DECIDE / PLAN / MCP / Jira / VERIFY / HANDOFF into **Runs**
- **Runs** — browse `.ai-delivery/<KEY>/runs/*`, filter ledger event types, inspect feasibility / plan / evidence / verify / handoff
- **Stories** — offline fixture catalog with dry-run
- Deep link: `/auto-story.html?issue=KAN-7&run=<runId>` or `?story=MNB-129`

## Quick start

```bash
# Env: copy scripts/auto_story/.env.example (or tools/iiq-chat/.env.example) → .env
# Dry-run (default): feasibility + PLAN + ledger; no IIQ/Jira writes
python3 -m scripts.auto_story run --issue MNB-105 --fixture jira-stories/fixtures --tail --no-llm

# With LLM (OPENROUTER_API_KEY + MCP up)
python3 -m scripts.auto_story run --issue MNB-105 --fixture jira-stories/fixtures --tail

# Poll Ready queue (needs JIRA_*)
python3 -m scripts.auto_story poll

# Live allowlisted run (mutates IIQ + Jira)
python3 -m scripts.auto_story run --issue KAN-1 --live --tail
```

Config: [`config.yaml`](config.yaml). Override with `AUTO_STORY_CONFIG=/path/to.yaml`.

## Visibility

Each run writes `.ai-delivery/<KEY>/runs/<runId>/`:

- `events.jsonl` — `THINK`, `DECIDE`, `PLAN`, `MCP_CALL`, `MCP_RESULT`, `JIRA`, `VERIFY`, `HANDOFF`, …
- `feasibility.json`, `plan.md`, `evidence.json`, `mcp-audit.jsonl`

`--tail` streams colored events to the terminal.

## LLM provider

```yaml
llm:
  provider: openrouter   # openrouter | openai | azure_openai | gemini_openai_compat
  model: openrouter/free
  base_url: null         # set for OpenAI-compat Gemini / Azure
  api_key_env: OPENROUTER_API_KEY
```

## Layout

| Path | Role |
| --- | --- |
| `cli.py` / `__main__.py` | Entry (`python -m scripts.auto_story`) |
| `runner.py` | Control loop |
| `ledger.py` | Append-only events |
| `llm/` | Swappable Chat Completions + tool loop |
| `mcp_wrap.py` | MCP client + dry-run + audit |
| `jira_client.py` | REST assign / transition / comment |
| `lease.py` | SQLite claim lease |
| `prompts/` | System + stage + story-type packs |
| `verify.py` | Acceptance checks |
