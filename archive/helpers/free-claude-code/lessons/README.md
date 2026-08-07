# Staff Claude Code — engineering curriculum

**Primary learning surface:** the static site (zero model tokens).

```bash
cd archive/helpers/free-claude-code/site
npm install
npm run dev
```

Then open the printed localhost URL → **Get started**.

| | |
| --- | --- |
| **Audience** | Staff / senior engineers who already ship |
| **Time** | ~11–13 hours full path |
| **Lab** | Any mid-size repo — **IIQ not required** |
| **Learn** | Static Starlight site under [`../site/`](../site/) |
| **Progress** | Site [/progress/](../site/) + [`progress.md`](progress.md) |
| **Style** | [`_STYLE.md`](_STYLE.md) |

> **Token note:** Reading the site and these markdown files is free. Opening Claude to practice templates is optional and is the only step that spends credits.

---

## The problem

You installed Claude Code. You ran a few prompts. Now what?

- Official docs describe features — not how staff engineers **combine** them.
- Toy examples do not survive a real monorepo.

This guide is a **structured, example-driven path** with production-shaped templates — delivered as a static website with search, steppers on the get-started path, and a visual progress board.

---

## Curriculum map

| Order | Module | Level | Time |
| --- | --- | --- | --- |
| 1 | [Slash commands](01-slash-commands/) | Beginner | ~30–45 min |
| 2 | [Memory](02-memory/) | Beginner+ | ~45 min |
| 3 | [Skills](03-skills/) | Intermediate | ~1 h |
| 4 | [Subagents](04-subagents/) | Intermediate+ | ~1–1.5 h |
| 5 | [MCP](05-mcp/) | Intermediate+ | ~1 h |
| 6 | [Hooks](06-hooks/) | Intermediate | ~1 h |
| 7 | [Plugins](07-plugins/) | Advanced | ~45 min |
| 8 | [Checkpoints](08-checkpoints/) | Intermediate | ~45 min |
| 9 | [Advanced](09-advanced/) | Advanced | ~1–2 h |
| 10 | [CLI](10-cli/) | Beginner+ / Advanced | ~45 min |
| 11 | [Ops playbooks](11-ops-playbooks/) | Advanced | ~2 h |

Full path: [`LEARNING-ROADMAP.md`](LEARNING-ROADMAP.md) · Catalog: [`CATALOG.md`](CATALOG.md)

---

## Get started in 15 minutes (no Claude required)

1. `cd ../site && npm run dev`
2. Open **Get started** → follow the on-page steps
3. Copy templates from `01-slash-commands/` into a project when ready
4. Optionally launch Claude later to try `/optimize` / `/pr`

---

## Dual runtime (Claude Code vs Cursor)

| Concept | Claude Code | Cursor analogue |
| --- | --- | --- |
| Project instructions | `CLAUDE.md` | rules / `CLAUDE.md` |
| Skills | `.claude/skills/` | `.cursor/skills/` |
| Hooks | settings hooks | `.cursor/hooks.json` |
| Agents | `.claude/agents/` | Task / custom agents |
| MCPs | `claude mcp add` | Cursor MCP settings |

---

## Archive

Previous **30-day Agentic IAM** day files: [`_archive/days-v1-iam/`](_archive/days-v1-iam/).

Optional in-Claude quiz skills (token cost): [`../.claude/optional-skills-token-cost/`](../.claude/optional-skills-token-cost/) — **not** on the critical path.
