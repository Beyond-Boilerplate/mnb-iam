# Repository layout

Meridian IdentityIQ **8.5** SSD repo with lab tooling. Prefer Docker for day-to-day:

```bash
./tools/lab/docker/up.sh          # IIQ + LDAP + MCP + Teller + seed
./tools/lab/docker/down.sh        # full wipe (volumes too)
```

Host Tomcat path (alternate): `./tools/lab/up.sh`

## Live paths

| Path | Role |
| --- | --- |
| `base/` | GA IdentityIQ (do not edit `base/ga/`) |
| `config/` | Durable Meridian XML (Rules, Applications, …) |
| `web/` | UI branding / custom CSS |
| `pluginsrc/mnb-iam-toolkit/` | Meridian Custom APIs plugin source |
| `ssdplugins/mnb_iam_toolkit/` | Built plugin ZIP drop (from `package.sh`) |
| `lab-data/` | HR CSV, OpenLDAP LDIF, connector notes |
| `docker/` + `docker-compose.iiq.yml` | Lab stack images / Compose |
| `tools/lab/` | Lab bootstrap (Docker + host) |
| `tools/iiq-mcp/` | IdentityIQ MCP server |
| `tools/iiq-chat/` | Teller chatbot (+ Auto-story UI at `/auto-story.html`, `eval/` suite) |
| `tools/iiq-verify/` | Lesson verify helpers |
| `docs/` | Lessons, LOCAL_SETUP, MCP tools, SSD |
| `learn/` | Academy site builder |
| `deploy/` | Helm / CD |
| `jira-stories/` | Offline ticket fixtures for agents |
| `scripts/` | Stock SSB Ant scripts (+ `iiq-delivery/`, `jira/`, `auto_story/`) |

## Archive (not runtime)

See [`archive/README.md`](../archive/README.md):

- `archive/compat-park/` — parked SSD/SSF samples and draft XML (was `tools/compat-park/`)
- `archive/ssd-stock/` — stock `Split/`, `samples/`, `TaskResulter`
- `archive/helpers/free-claude-code/` — optional Claude Code free-tier helper

Do not import archive XML/Java into `config/` or `src/` without IIQ 8.5 validation.

## Local-only (gitignored)

`build/`, `var/`, `IIQDBDump/`, `learn/dist/`, `tools/iiq-mcp/.venv/`, plugin build classes under `pluginsrc/**/build/`.
