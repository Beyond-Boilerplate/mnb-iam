"""Implement stage: Teller-class MCP agent."""

from __future__ import annotations

import json
from typing import Any

from .ledger import RunLedger
from .llm.loop import run_tool_agent
from .llm.provider import LlmProvider
from .mcp_wrap import WrappedMcp
from .prompts_loader import compose_system


def run_implement(
    *,
    provider: LlmProvider,
    mcp: WrappedMcp,
    ledger: RunLedger,
    issue: dict[str, Any],
    decision: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    story_type = str(decision.get("story_type") or "other")
    agent_cfg = cfg.get("agent") or {}
    max_steps = int(agent_cfg.get("max_steps") or 24)
    verbose = bool(agent_cfg.get("verbose_think"))
    dry = bool(mcp.dry_run)

    plan_lines = [
        f"# Plan for {issue.get('key')} ({story_type})",
        "",
        f"Mode: {decision.get('mode')}",
        f"Dry-run: {dry}",
        "",
        "## Intended tools",
    ]
    for t in decision.get("planned_tools") or []:
        plan_lines.append(f"- `{t}`")
    if not decision.get("planned_tools"):
        plan_lines.append("- (model will choose from allowlisted MCP catalog)")
    plan_lines.extend(
        [
            "",
            "## Acceptance hints",
            *(f"- {r}" for r in (decision.get("reasons") or [])),
        ]
    )
    plan_text = "\n".join(plan_lines)
    ledger.write_text("plan.md", plan_text)
    ledger.emit("PLAN", summary=f"plan written for {story_type}", story_type=story_type, dry_run=dry)

    system = compose_system(story_type, "implement.md")
    user = (
        f"Implement Jira {issue.get('key')} as MCP_E2E story_type={story_type}.\n"
        f"dry_run={dry}\n\n"
        f"Issue:\n{json.dumps(issue, indent=2)}\n\n"
        f"Feasibility:\n{json.dumps(decision, indent=2)}\n"
    )

    tools = mcp.openai_tools(allow_writes=True)
    if not tools:
        raise RuntimeError("No MCP tools available for implement")

    def on_event(etype: str, payload: dict[str, Any]) -> None:
        if etype == "thought":
            ledger.emit("THINK", text=payload.get("text"), summary=(payload.get("text") or "")[:160])
        elif etype == "tool_start":
            ledger.emit(
                "MCP_CALL",
                tool=payload.get("tool"),
                arguments=payload.get("arguments"),
                dry_run=dry,
                summary=f"call {payload.get('tool')}",
            )
        elif etype == "tool_result":
            ledger.emit(
                "MCP_RESULT",
                tool=payload.get("tool"),
                ok=payload.get("ok"),
                summary=payload.get("summary"),
            )
        elif etype == "status":
            ledger.emit("STATUS", message=payload.get("message"), summary=payload.get("message"))

    outcome = run_tool_agent(
        provider,
        system_prompt=system,
        user_message=user,
        openai_tools=tools,
        call_tool=mcp.call,
        max_steps=max_steps,
        on_event=on_event,
        verbose_think=verbose,
    )
    ledger.write_json(
        "implement.json",
        {
            "reply": outcome.get("reply"),
            "model": outcome.get("model"),
            "provider": outcome.get("provider"),
            "steps": [
                {
                    "tool": s.get("tool"),
                    "ok": s.get("ok"),
                    "arguments": s.get("arguments"),
                    "summary": s.get("summary"),
                    "error": s.get("error"),
                    "result": s.get("result"),
                }
                for s in (outcome.get("steps") or [])
            ],
        },
    )
    return outcome
