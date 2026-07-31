# Jira To Do poller (mnbiam / KAN)

**Live board:** https://mnbiam.atlassian.net · project **KAN**  
**Primary intake:** Atlassian MCP in Claude Code (`/intake`) — see `.claude/commands/intake.md`.

## Prefer MCP (no API token needed in repo)

```text
JQL: project = KAN AND statusCategory = "To Do" ORDER BY created ASC
```

## Optional REST poller

```bash
export JIRA_SITE=https://mnbiam.atlassian.net
export JIRA_EMAIL=you@example.com
export JIRA_API_TOKEN=...          # Atlassian API token
export JIRA_PROJECT_KEY=KAN
# optional override:
# export JIRA_TODO_JQL='project = KAN AND statusCategory = "To Do" ORDER BY created ASC'

python3 scripts/jira/todo_poll.py --all
```

Missing env → `JIRA_POLL_SKIPPED` (SessionStart prints an MCP hint).  
**Fixtures are opt-in only:** `--fixture jira-stories/fixtures` (never silent).

Seen keys: `.ai-delivery/_state/todo_seen.sqlite` (gitignored).  
Config: [`status_map.yaml`](status_map.yaml).
