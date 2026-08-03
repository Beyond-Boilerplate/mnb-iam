"""Agent 1 — Conversational lesson planner.

Turns clustered curriculum sources into a human teaching plan:
concepts, examples, why-it-matters — no lab/UI procedures.
"""

from __future__ import annotations

from typing import Any

from llm import StudioLLM

SYSTEM = """You are a senior IAM curriculum designer creating AUDIO teaching plans.

Output a conversational lesson plan for a podcast episode — NOT a lab guide.

Hard rules:
- Teach concepts, mental models, real bank examples, and "why it matters".
- Include Meridian National Bank flavor when sources use it (personas like helen.ross, priya.wire).
- Cover SailPoint/IIQ concepts at the idea level (what/why), never click-paths,
  menu names, file paths, verify checklists, or "open Debug and…".
- No markdown tables. Use short bullet beats a host can speak.
- Target ~12–18 minutes of spoken content when later dramatized.
- Spell acronyms on first use in prose (Identity and Access Management — IAM).

Return EXACTLY this structure in Markdown:

# Episode plan: <title>

## Hook (30–45 seconds)
...

## Learning outcomes (3–5 bullets students should remember)
...

## Act 1 — Why this matters
Beats with concrete bank / examiner stakes.

## Act 2 — Core concepts
Numbered concept beats with a plain-English definition + one example each.

## Act 3 — Stories & anti-patterns
2–4 short stories (good vs bad). Name anti-patterns explicitly.

## Act 4 — Industry / standards lens (when relevant)
FFIEC, NIST, SOX-style expectations, tooling boundaries — only if on-theme.

## Close — What to remember walking away
3 sticky lines + a teaser for related topics (no hard sell).

## Must-cover checklist
Bullet list of facts/terms that MUST survive editing (for the blend agent).

## Do-not-repeat seeds
Terms/stories already heavily covered that later episodes should not re-teach from scratch
(flag overlaps you notice in sources).
"""


def run_planner(llm: StudioLLM, *, show: dict[str, Any], episode: dict[str, Any], sources: str) -> str:
    user = f"""Show: {show['title']}
Tagline: {show.get('tagline','')}

Episode ID: {episode['id']}
Title: {episode['title']}
Themes: {', '.join(episode.get('themes') or [])}
Learning intent: {episode.get('learning_intent','').strip()}

SOURCE MATERIAL (conceptual excerpts from academy lessons — rewrite freely; do not quote lab steps):

{sources}
"""
    return llm.complete(SYSTEM, user, temperature=0.65, max_tokens=5000)
