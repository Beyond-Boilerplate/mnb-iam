# Style guide — Staff Claude Code curriculum

Voice: **staff engineer pair-programming with a teammate on Claude Code** — judgment, production habits, and failure modes. Not a buzzword pitch deck. Not an IAM onboarding track.

## Audience

Engineers who already ship code and want agentic tooling done well: skills, memory, hooks, subagents, MCP, CLI automation.

## Required sections (every module `README.md`)

1. **At a glance** — level, time, prereq, artifacts path
2. **Why this matters** — concrete staff scenario (PR, CI, secrets, on-call)
3. **Concept primer** — define terms; one comparison table or Mermaid diagram
4. **Hands-on walkthrough** — numbered tasks: framing → exact action → expected result → tip/gotcha
5. **Copy-paste templates** — real files beside the README (or linked under the module folder)
6. **How it works** — short deeper dive
7. **Pitfalls** — 3–6 real failure modes with fixes
8. **Knowledge check** — 4–6 Qs + answers (feeds `/lesson-quiz`)
9. **Recap** — what you built / understand / can do next
10. **Stretch** — optional harder practice
11. **Feedback** — self-check question for the reader
12. **Domain Stretch** — optional, skippable callout; never required for acceptance

## Writing mechanics

- Second person, active voice, short sentences.
- Define every technical term the first time it appears.
- Nest **Why** / **Expect** under the task they belong to (indent or sub-bullets).
- Prefer bullets and short paragraphs over walls of text.
- Encapsulate commands in fenced code blocks with language tags.
- Callouts: `> **Tip:**` / `> **Watch out:**` / `> **Important:**` / `> **Token note:**`
- Hands-on tech/UI tasks only — no paper/notebook assignments.
- State what “it worked” looks like after every non-trivial step.

## Safety rules (every module)

- Never commit secrets, API keys, or credential files.
- Confirm before destructive or irreversible git/cloud/prod actions.
- Prefer verify scripts and tests over “looks fine.”
- Hooks deny > hope.

## Token-aware design

**Default learning path is the static site** (`../site/` — `npm run dev`). Reading markdown and using the progress board costs **zero** model tokens.

Optional in-Claude coaching skills under `../.claude/optional-skills-token-cost/` are **not** required and do consume tokens if you enable them.

## Deliverable layout

```text
lessons/artifacts/
  skills/          # SKILL.md trees
  hooks/           # hook scripts + settings snippets
  agents/          # agent prompt defs
  mcp/             # mcp configs / wrappers
  playbooks/       # reusable prompts
  demos/           # capstone / teach-back notes
```

## Naming

- Modules: `01-slash-commands/` … `11-ops-playbooks/` (number = learning order)
- Templates: kebab-case files next to the module README
- Progress: tick boxes in `progress.md` only when acceptance criteria are done
