# 30-Day Agentic IAM Lab — Claude Code Mastery

Progressive curriculum to **master Claude Code skills, agents, hooks, and MCPs** while automating the daily friction of an enterprise SailPoint IdentityIQ engineer — using this Meridian National Bank SSD/SSB workspace as the live lab.

| | |
| --- | --- |
| **Audience** | IAM engineers who already touch IIQ (or are learning Meridian labs in parallel) |
| **Daily time** | 2+ hours (deep track) |
| **Lab** | Local IIQ via `./tools/lab/up.sh` or `./tools/lab/docker/up.sh` |
| **Claude setup** | [`../setup-cc-free.sh`](../setup-cc-free.sh) + project `CLAUDE.md` at repo root |
| **Companion** | Meridian lessons in [`docs/lessons/`](../../../docs/lessons/) — IIQ craft; **this track** = agentic automation |

---

## What you will own by Day 30

An **IAM Ops Desk** pack under this folder’s `artifacts/`:

| Artifact | Purpose |
| --- | --- |
| Project + personal **skills** | Repeatable rituals (export/tokenize, SoD review, leaver drill, CAB pack) |
| **Hooks** | Guardrails (no secrets in logs, block `base/ga` edits, evidence reminders) |
| **Agents** | Specialist subagents (XML reviewer, BeanShell auditor, cert campaign assistant) |
| **MCPs** | Jira/GitHub/IIQ-verify bridges so tickets, PRs, and lab checks flow without copy-paste |
| **Runbooks** | Prompt playbooks you can re-run under on-call pressure |

---

## Curriculum map

### Week 1 — Fluency + Meridian context (Days 01–07)

| Day | Title | Claude focus | IAM pain automated |
| --- | --- | --- | --- |
| [01](day-01-bootstrap-and-mental-model.md) | Bootstrap & mental model | CLI, modes, CCR/OpenRouter | “Where do I even start?” |
| [02](day-02-claude-md-and-repo-memory.md) | CLAUDE.md & repo memory | `/init`, memory, context budgets | Wrong Ant/IIQ paths every session |
| [03](day-03-permissions-and-safe-ops.md) | Permissions & safe ops | Allow/deny, Ctrl+E risk | Accidental prod-shaped commands |
| [04](day-04-lab-health-orchestration.md) | Lab health orchestration | Multi-step prompts, plans | Up/down Tomcat, Forgotten `SPTARGET` |
| [05](day-05-ssb-build-deploy-loop.md) | SSB build–deploy–import loop | Shell discipline with Claude | Clean war → deploy → importdynamic friction |
| [06](day-06-config-xml-hygiene.md) | Config XML hygiene | Diff-aware edits | Naming, tokens, dirty Debug exports |
| [07](day-07-evidence-and-verify.md) | Evidence & verify | Structured outputs | Examiner/CAB “prove it” tax |

### Week 2 — Skills (Days 08–14)

| Day | Title | Claude focus | IAM pain automated |
| --- | --- | --- | --- |
| [08](day-08-skill-anatomy.md) | Skill anatomy | SKILL.md design | One-off prompts that don’t transfer |
| [09](day-09-skill-lab-bootstrap.md) | Skill: lab bootstrap | Personal vs project skills | 15-minute morning stack check |
| [10](day-10-skill-export-tokenize.md) | Skill: export → tokenize | Progressive disclosure | Manual token hunt in XML |
| [11](day-11-skill-aggregation-triage.md) | Skill: aggregation triage | Trigger descriptions | “Aggregation failed — now what?” |
| [12](day-12-skill-sod-and-policy-review.md) | Skill: SoD / policy review | Domain checklists | Policy XML review before CAB |
| [13](day-13-skill-joiner-mover-leaver.md) | Skill: JML ticket pack | Multi-file skills + scripts | Lifecycle ticket prep chaos |
| [14](day-14-skill-catalog-and-eval.md) | Skill catalog & eval | Skill index, A/B prompts | Skills that never get used |

### Week 3 — Hooks + Agents (Days 15–21)

| Day | Title | Claude focus | IAM pain automated |
| --- | --- | --- | --- |
| [15](day-15-hooks-fundamentals.md) | Hooks fundamentals | Pre/PostToolUse, Stop | Unguarded dangerous shell |
| [16](day-16-hooks-iiq-guardrails.md) | IIQ guardrail hooks | Matchers, deny rules | Editing `base/ga`, committing secrets |
| [17](day-17-hooks-evidence-automation.md) | Evidence automation hooks | SessionStart / Stop | Forgotten screenshots & CHANGELOG |
| [18](day-18-agents-specialists.md) | Specialist agents | Subagent prompts | One mega-agent doing everything poorly |
| [19](day-19-agent-xml-beanshell-review.md) | XML + BeanShell review agents | Parallel Task agents | Rule regressions before import |
| [20](day-20-agent-cert-and-provisioning.md) | Cert + provisioning agents | Multi-step workflows | Campaign / ProvTx rabbit holes |
| [21](day-21-agent-teams-orchestration.md) | Agent teams orchestration | Handoffs, resumable agents | “Investigate → fix → verify” loop |

### Week 4 — MCPs + Ops Desk Capstone (Days 22–30)

| Day | Title | Claude focus | IAM pain automated |
| --- | --- | --- | --- |
| [22](day-22-mcp-fundamentals.md) | MCP fundamentals | `claude mcp`, auth scopes | Tool sprawl without standards |
| [23](day-23-mcp-jira-ticket-bridge.md) | Jira MCP bridge | Ticket → lab plan | Copy-paste from tickets to Claude |
| [24](day-24-mcp-github-pr-discipline.md) | GitHub MCP + PR discipline | Review + SSB CI awareness | Blind merges of config XML |
| [25](day-25-mcp-iiq-verify-bridge.md) | IIQ verify MCP (custom) | Wrap `iiq-verify` | Manual lesson/regression checks |
| [26](day-26-compose-skill-hook-mcp.md) | Compose skill + hook + MCP | Full stack glue | Pieces that don’t talk |
| [27](day-27-oncall-playbooks.md) | On-call playbooks | Prompt packs + agents | 2am orphan / leaver fire drills |
| [28](day-28-promotion-cab-automation.md) | Promotion / CAB automation | Multi-env tokens | sandbox → prod fear |
| [29](day-29-ops-desk-integration.md) | Ops Desk integration day | Wire everything | Friction still between tools |
| [30](day-30-capstone-demo-and-retro.md) | Capstone demo & retro | Teach-back | Prove mastery with a live demo |

---

## How to use this track

1. Complete [Day 01](day-01-bootstrap-and-mental-model.md) setup once (Claude Code + IIQ lab healthy).
2. Work **one day file per calendar day** (or batch only if you keep acceptance checkboxes honest).
3. Store **every deliverable** under `artifacts/` (skills, hooks, agent defs, MCP configs, playbooks).
4. Tick boxes in [progress.md](progress.md).
5. When an exercise mentions a Meridian IIQ lesson (e.g. Lesson 04 HR app), either reuse objects you already built or follow the linked `docs/lessons/` tutorial first.

## Dual runtime note (Cursor vs Claude Code CLI)

You may work inside **Cursor** and/or the **Claude Code CLI** (`cc` from the free installer). Concepts map:

| Concept | Claude Code | Cursor analogue |
| --- | --- | --- |
| Project instructions | `CLAUDE.md` | rules / `CLAUDE.md` |
| Skills | `.claude/skills/` or `~/.claude/skills/` | `.cursor/skills/` / `~/.cursor/skills/` |
| Hooks | Claude Code hooks in settings | `.cursor/hooks.json` |
| Agents | Subagents / agent definitions | Task tool / custom agents |
| MCPs | `claude mcp add` | Cursor MCP settings |

**Primary target of this curriculum:** Claude Code CLI patterns. Cursor ports are stretch goals on each relevant day.

## Style & contribution

See [_STYLE.md](_STYLE.md). Day files are tutorials (teach → do → verify), not bare checklists.

## Quick links

- Repo guidance: [`../../../CLAUDE.md`](../../../CLAUDE.md)
- Lab setup: [`../../../docs/LOCAL_SETUP.md`](../../../docs/LOCAL_SETUP.md)
- SSB: [`../../../docs/SSD.md`](../../../docs/SSD.md)
- Config workflow: [`../../../config/README.md`](../../../config/README.md)
- Lesson verify: [`../../../docs/LESSON_VERIFY.md`](../../../docs/LESSON_VERIFY.md)
- Free installer: [`../README.md`](../README.md)
