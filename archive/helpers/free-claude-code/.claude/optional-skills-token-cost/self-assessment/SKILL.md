---
name: self-assessment
description: >-
  Staff Claude Code curriculum self-assessment. Quiz across slash/memory/skills/hooks/MCP/subagents/CLI,
  score Beginner/Intermediate/Advanced, and point into LEARNING-ROADMAP.md. Use when asked to assess level,
  find where to start, skill check, or level up. Prefer Quick Assessment (low tokens) unless user asks Deep.
---

# Self-assessment & learning path

Interactive assessment for the curriculum under `lessons/` in this `free-claude-code` tree.

> **Token note:** This skill uses model tokens. Default to **Quick** (2 multi-selects). Offer Deep only if the user asks.

## Guardrails

- Do not invent curriculum paths — link to existing module folders `01-` … `11-`.
- Prefer AskUserQuestion (or clear numbered options) over long monologues.
- After scoring, give a short personalized next-3-modules list.

## Step 1 — Mode

Ask:

1. **Quick** (~2 min, low tokens) — overall level + next modules  
2. **Deep** (~5 min) — per-topic gaps  

## Step 2A — Quick

Two multi-selects (max 4 options each):

**Basics:** Start Claude and chat; created/edited CLAUDE.md; used 3+ slash commands; created a skill/command  

**Advanced:** Configured MCP; set up hooks; used subagents; used `claude -p`

Scoring (total checks):

- 0–2 → Beginner → start `lessons/01-slash-commands/` then `02-memory/`
- 3–5 → Intermediate → start `lessons/03-skills/` then `06-hooks/`
- 6–8 → Advanced → start `lessons/09-advanced/` then `11-ops-playbooks/`

List unchecked items as gaps. Point to `lessons/LEARNING-ROADMAP.md`.

## Step 2B — Deep

Five rounds, 4 options each (2 topics × 2 signals). Score 0–2 per topic.

1. Slash + Memory  
2. Skills + Hooks  
3. MCP + Subagents  
4. Checkpoints + CLI print mode  
5. Plugins + Ops composition  

For each topic with score 0: recommend the matching module. For score 2: mark “optional review.”

## Step 3 — Output

Deliver:

1. Level + one-sentence rationale  
2. Gap list (bullets)  
3. Ordered next modules (3 max) with relative paths  
4. Reminder: reading markdown is free; quizzes/labs with Claude cost tokens  
5. Offer `/start-module NN` for the first recommended module  
