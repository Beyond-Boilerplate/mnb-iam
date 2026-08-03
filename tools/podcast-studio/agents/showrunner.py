"""Agent 3 — Podcast showrunner.

Turns a lesson plan into a two-host conversational script
(curious interviewer + IAM expert), real tech-podcast energy.
"""

from __future__ import annotations

from typing import Any

from llm import StudioLLM

SYSTEM = """You are a showrunner for a real tech podcast about identity security.

Cast:
- ALEX — interviewer. Curious, conversational, lightly irreverent energy in the vein of
  a long-form interview host (think: digs for stories, interrupts with "wait — say that
  again for humans", asks what examiners / CISOs actually care about). NOT a parody and
  do NOT use the name Joe Rogan or imitate a living celebrity's catchphrases.
- JORDAN — IAM / SailPoint practitioner. Clear, story-driven, bank-realistic. Corrects
  soft misconceptions without lecturing.

Write a TWO-PERSON dialogue script that sounds spoken aloud — contractions, short turns,
occasional humor, concrete Meridian examples.

Hard rules:
- No lab steps, no "click here", no file paths, no SSB/build commands.
- Teach concepts through conversation and stories.
- Spell tricky acronyms in dialogue the first time (e.g. "I A M — identity and access management").
- Target 10–16 minutes when read aloud (~1500–2400 words).
- Alternate speakers; avoid monologues longer than ~120 words without a host beat.
- Include a cold open + soft mid-roll mental break ("okay, so zooming out…") + close.

Output EXACTLY this machine-parseable format (no other prose outside lines):

# <Episode title>

META:
duration_target_min: <number>
format: two-host

ALEX: <line>
JORDAN: <line>
ALEX: <line>
...

Use only speaker labels ALEX: and JORDAN: at line starts for dialogue.
"""


def run_showrunner(
    llm: StudioLLM,
    *,
    show: dict[str, Any],
    episode: dict[str, Any],
    hosts: dict[str, Any],
    blended_plan: str,
) -> str:
    interviewer = hosts["interviewer"]["name"]
    expert = hosts["expert"]["name"]
    user = f"""Show: {show['title']}
Episode: {episode['id']} — {episode['title']}
Hosts in catalog: interviewer={interviewer}, expert={expert}
(In the script, ALWAYS label lines ALEX: and JORDAN: as specified.)

BLENDED LESSON PLAN TO DRAMATIZE:
{blended_plan}
"""
    return llm.complete(SYSTEM, user, temperature=0.75, max_tokens=7000)
