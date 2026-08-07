# Playbook: incident triage (on-call pack)

**Trigger:** an alert fires or a teammate reports "something's wrong" and you're the first responder.

**Composes:** skill (triage checklist) + background task (log/metric tailing) + optional MCP (paging/monitoring) + a hard human escalation gate.

## Steps

1. **Skill — run the triage checklist.**
   - Invoke a triage skill that asks the standard first questions: what changed recently (deploys, config, traffic), what's the blast radius (one service, one region, everything), is this a known failure mode.
   - **Why a skill and not a fresh prompt each time:** under incident stress, you want a checklist you don't have to reconstruct from memory.

2. **Background task — tail logs/metrics without blocking you.**
   - Start log tailing or a metrics query as a background task (`run_in_background: true`) so you can keep asking Claude questions while evidence streams in, instead of waiting on one long-running command.
   - Check progress with `/tasks`; stop it once you have enough signal.

3. **Correlate, don't conclude.**
   - Ask Claude to correlate the triage checklist answers with what the background task surfaced (e.g., "does the error spike line up with the 2:14pm deploy?").
   - **Why this order:** you want evidence before a root-cause guess, not a plausible-sounding story built on the first alert message alone.

4. **Human escalation gate — decide who else needs to know, now.**
   - Based on blast radius from step 1, a human decides: handle solo, page a second responder, or declare a full incident.
   - **This is never automated.** Paging the wrong severity (too high: alarm fatigue; too low: slow response) is an organizational judgment call, not a classifier decision.

5. **(Optional) MCP — page or update a status page live.**
   - If a paging/monitoring MCP is configured, trigger the page or status update directly instead of switching tools.
   - **Fallback if MCP is down:** the human on the escalation gate pages manually through the normal on-call tool — the triage work up to this point isn't wasted.

## What "it worked" looks like

- You have a timestamped answer to "what changed recently" before you have a root-cause theory.
- The background task gave you log/metric evidence without blocking your ability to keep investigating.
- A specific human made the escalation call, and it's recorded (who, when, why that severity).

## Known gaps / open questions

<!-- Fill in after your dry run: what did this playbook get wrong about your real on-call setup? -->
