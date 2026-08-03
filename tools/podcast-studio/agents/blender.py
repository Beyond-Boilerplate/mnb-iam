"""Agent 2 — Continuity / blend editor.

Dedupes repetitive teaching across the show so episodes don't re-explain
the same six constructs every time.
"""

from __future__ import annotations

from typing import Any

from llm import StudioLLM

SYSTEM = """You are the continuity editor for a multi-episode IAM podcast show.

You receive:
1) The current episode's lesson plan
2) Continuity notes / must-cover claims from OTHER episodes (may be empty for E01)

Your job:
- Remove or compress repeated foundational explanations that earlier episodes already own.
- Keep a ONE-SENTENCE callback when a prior concept is needed ("as we covered when we
  talked about identity cubes…") instead of a full re-teach.
- Protect this episode's unique payload (its must-cover checklist).
- Tighten fluff; keep bank stories and examiner stakes.
- Still NO lab/UI/click-path content.

Return the FULL revised lesson plan in the SAME Markdown structure as the input plan
(Hook through Do-not-repeat seeds). Add a short final section:

## Continuity edits
- Bullets describing what you compressed, cut, or callback'd (for humans auditing the pipeline).
"""


def run_blender(
    llm: StudioLLM,
    *,
    episode: dict[str, Any],
    plan: str,
    prior_continuity: str,
) -> str:
    user = f"""Episode: {episode['id']} — {episode['title']}

CURRENT PLAN:
{plan}

PRIOR SHOW CONTINUITY (claims already taught elsewhere; compress overlaps):
{prior_continuity or '(none yet — first or isolated episode; still tighten internal repetition)'}
"""
    return llm.complete(SYSTEM, user, temperature=0.4, max_tokens=5000)
