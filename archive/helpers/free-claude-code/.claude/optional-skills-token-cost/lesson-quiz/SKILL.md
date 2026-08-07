---
name: lesson-quiz
description: >-
  Quiz a learner on one Staff Claude Code curriculum module (01-11) using only
  references/question-bank.md. Use for /lesson-quiz 03 or "quiz me on hooks".
  Do not invent questions. Prefer 5-question default (token-aware); offer 8 if asked.
---

# Lesson quiz

Test understanding of one module under `lessons/NN-*/`.

> **Token note:** Default **5 questions**. Longer quizzes cost more.

## Prerequisites

- Curriculum checkout with `lessons/01-slash-commands/` … `lessons/11-ops-playbooks/`
- This skill’s `references/question-bank.md`

## Guardrails

- **Never invent questions.** Only ask from the question bank for that lesson.
- If the bank lacks entries, say so — do not fabricate.
- Score accurately against the bank’s Correct field.
- Confirm timing: before / during / after the lesson (changes framing of results).

## Step 1 — Lesson

Map argument to folder:

| Input | Module |
| --- | --- |
| 01, slash, commands | 01-slash-commands |
| 02, memory | 02-memory |
| 03, skills | 03-skills |
| 04, subagents, agents | 04-subagents |
| 05, mcp | 05-mcp |
| 06, hooks | 06-hooks |
| 07, plugins | 07-plugins |
| 08, checkpoints | 08-checkpoints |
| 09, advanced | 09-advanced |
| 10, cli | 10-cli |
| 11, ops, playbooks | 11-ops-playbooks |

If missing, ask the user to pick.

## Step 2 — Load questions

Read `references/question-bank.md` for that lesson. Shuffle option order when presenting, but track the correct letter after shuffle.

Default: first 5 questions. If user wants deep: up to 8 if available.

## Step 3 — Ask one at a time

For each question: show stem + options; wait for answer; brief correct/incorrect + explanation from the bank; continue.

## Step 4 — Results

- Score X/N  
- Weak categories  
- Point to module README sections to review  
- Offer `/mark-complete NN` only if score ≥ 80% **and** user claims acceptance criteria done (quiz alone is not enough)
