# Style guide — Agentic IAM / Claude Code days

Voice: **senior IAM engineer pair-programming with a teammate on Claude Code**, not a buzzword pitch deck.

## Required sections (every day file)

1. **Title block** — Day, title, week, time (2–3h), prereq, artifacts path  
2. **Learning objectives** — 4–7 measurable bullets  
3. **IAM pain (today’s tax)** — Concrete Meridian scenario + why humans hate this work  
4. **Claude concept** — Definition, when to use, anti-patterns  
5. **Before you start** — Checklist  
6. **Lab procedure** — Numbered tasks with framing + expected result  
7. **Deliverable** — Exact path under `artifacts/`  
8. **Acceptance criteria** — Checkboxes  
9. **Troubleshooting** — 3–5 items  
10. **Stretch** — Optional harder practice  
11. **Knowledge check** — 3–5 Qs + Answers  
12. **Navigation** — Prev / Next  

## Naming & Meridian conventions

- Objects: `MNB-*`; export files: `config/<Type>/MNB-<Type>-<Business>.xml`
- Tokens: `%%TOKEN%%` from `*.target.properties`
- Lab: `http://localhost:8080/identityiq`, `SPTARGET=sandbox`
- Evidence: `~/iiq-lab-evidence/YYYY-MM-DD/`
- Personas: `helen.ross`, `priya.wire`, `nina.joiner`, `sofia.torres`, etc. (`@meridiannb.com`)

## Safety rules baked into every day

- Never edit `base/ga/`
- Never commit secrets / `iiq.properties` passwords
- Prefer `./build.sh` over system Ant
- Prefer verify scripts over “looks fine in UI”
- Hooks deny > hope

## Deliverable layout

```text
lessons/artifacts/
  skills/          # SKILL.md trees
  hooks/           # hook scripts + settings snippets
  agents/          # agent prompt defs
  mcp/             # mcp configs / wrappers
  playbooks/       # reusable prompts
  demos/           # Day 30 demo notes
```
