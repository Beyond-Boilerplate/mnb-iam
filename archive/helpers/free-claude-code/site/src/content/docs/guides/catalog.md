---
title: Feature catalog
sidebar:
  order: 3
---

Quick reference for every module. Install from the module folder; details live in each `README.md`.

| Feature | Invocation | Persistence | Best for | Folder |
| --- | --- | --- | --- | --- |
| **Slash / skill commands** | Manual `/cmd` | Session | Quick shortcuts | [01-slash-commands](/modules/01-slash-commands/) |
| **Memory** | Auto-loaded | Cross-session | Team standards | [02-memory](/modules/02-memory/) |
| **Skills** | Auto or `/name` | Filesystem | Repeatable workflows | [03-skills](/modules/03-skills/) |
| **Subagents** | Delegated | Isolated context | Parallel specialists | [04-subagents](/modules/04-subagents/) |
| **MCP** | Tool calls | Live connection | External systems | [05-mcp](/modules/05-mcp/) |
| **Hooks** | Event-triggered | Configured | Guardrails & automation | [06-hooks](/modules/06-hooks/) |
| **Plugins** | Install once | Bundled pack | Team distribution | [07-plugins](/modules/07-plugins/) |
| **Checkpoints** | Esc Esc / `/rewind` | Session | Safe experiments | [08-checkpoints](/modules/08-checkpoints/) |
| **Advanced** | Modes / settings | Session + config | Plan, permissions, background | [09-advanced](/modules/09-advanced/) |
| **CLI** | Terminal | Script / CI | Headless automation | [10-cli](/modules/10-cli/) |
| **Ops playbooks** | Compose all | Your artifacts | Staff workflows | [11-ops-playbooks](/modules/11-ops-playbooks/) |

## Install cheatsheet

```bash
# From a project root — adjust SOURCE to this curriculum path
SOURCE=archive/helpers/free-claude-code/lessons

mkdir -p .claude/skills .claude/agents
cp -R "$SOURCE/01-slash-commands/optimize" .claude/skills/   # example
cp "$SOURCE/02-memory/project-CLAUDE.md" ./CLAUDE.md          # adapt, don't blind-overwrite
cp "$SOURCE/04-subagents/"*.md .claude/agents/                # after you read them
```

Hooks and MCP need settings edits — follow module READMEs; never paste secrets into chat.

