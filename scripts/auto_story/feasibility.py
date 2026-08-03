"""Feasibility gate: LLM + optional read MCP → DECIDE."""

from __future__ import annotations

import json
import re
from typing import Any

from .ledger import RunLedger
from .llm.loop import run_tool_agent
from .llm.provider import LlmProvider
from .mcp_wrap import WrappedMcp
from .prompts_loader import compose_system


def _extract_json(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def infer_story_type(labels: list[str], allowlist: list[str]) -> str | None:
    for lab in labels:
        if lab in allowlist:
            return lab
    return None


def heuristic_feasibility(issue: dict[str, Any], allowlist: list[str]) -> dict[str, Any]:
    """Offline / no-LLM fallback."""
    labels = list(issue.get("labels") or [])
    summary = str(issue.get("summary") or "").lower()
    desc = str(issue.get("description") or "").lower()
    blob = summary + " " + desc

    if any(x in labels for x in ("ui-branding", "branding")) or "logo" in blob or "theme" in blob:
        return {
            "mode": "HYBRID",
            "story_type": "ui-branding",
            "confidence": 0.7,
            "reasons": ["Branding signals → web/ overlays"],
            "missing_dor": [],
            "planned_tools": [],
            "risks": ["Not MCP_E2E"],
        }
    if "rule" in blob and "workflow" in blob:
        return {
            "mode": "HYBRID",
            "story_type": "automation-rule-workflow",
            "confidence": 0.6,
            "reasons": ["Rule/Workflow SSD"],
            "missing_dor": [],
            "planned_tools": [],
            "risks": ["update_rule_source excluded"],
        }

    st = infer_story_type(labels, allowlist)
    if not st:
        # keyword map
        if any(k in blob for k in ("unlock", "password", "capability")):
            st = "identity-admin"
        elif any(k in blob for k in ("application", "onboard", "delimited", "aggregate")):
            st = "app-onboarding"
        elif any(k in blob for k in ("refresh", "task", "schedule")):
            st = "task-ops"
        elif any(k in blob for k in ("grant", "revoke", "access request")):
            st = "access-request"
        elif "population" in blob or "workgroup" in blob:
            st = "governance-admin"
        elif "certif" in blob:
            st = "certification"
        elif "sod" in blob or "segregation" in blob:
            st = "policy-sod"
        elif any(k in blob for k in ("joiner", "leaver", "mover", "jml")):
            st = "jml-lifecycle"

    if st and st in allowlist:
        return {
            "mode": "MCP_E2E",
            "story_type": st,
            "confidence": 0.55,
            "reasons": [f"Heuristic allowlist match: {st}"],
            "missing_dor": [],
            "planned_tools": [],
            "risks": ["Heuristic only — confirm DoR"],
        }
    return {
        "mode": "BLOCKED",
        "story_type": st or "other",
        "confidence": 0.4,
        "reasons": ["Not on MCP_E2E allowlist or DoR unclear"],
        "missing_dor": ["Clarify story type and acceptance"],
        "planned_tools": [],
        "risks": ["Do not auto-claim"],
    }


def run_feasibility(
    *,
    provider: LlmProvider | None,
    mcp: WrappedMcp,
    ledger: RunLedger,
    issue: dict[str, Any],
    cfg: dict[str, Any],
    use_llm: bool = True,
) -> dict[str, Any]:
    allowlist = list(cfg.get("story_allowlist") or [])
    agent_cfg = cfg.get("agent") or {}
    max_steps = min(int(agent_cfg.get("max_steps") or 24), 8)
    verbose = bool(agent_cfg.get("verbose_think"))

    ledger.emit("STATUS", message="Feasibility starting", summary=issue.get("key"))

    if not use_llm or provider is None or not provider.api_key:
        decision = heuristic_feasibility(issue, allowlist)
        ledger.emit(
            "DECIDE",
            summary=f"{decision.get('mode')} / {decision.get('story_type')}",
            **decision,
        )
        ledger.write_json("feasibility.json", decision)
        return decision

    system = compose_system(None, "feasibility.md")
    user = (
        "Classify this Jira issue for auto-story.\n\n"
        + json.dumps(issue, indent=2)
        + "\n\nAllowlist: "
        + ", ".join(allowlist)
    )

    # Feasibility: read-only tools (fallback to heuristic if MCP down / empty)
    try:
        tools = mcp.openai_tools(allow_writes=False)
    except Exception as exc:  # noqa: BLE001
        ledger.emit("STATUS", message=f"MCP tools unavailable: {exc}", summary=str(exc))
        tools = []

    if not tools:
        decision = heuristic_feasibility(issue, allowlist)
        decision["reasons"] = list(decision.get("reasons") or []) + ["No MCP tools — heuristic only"]
        ledger.emit(
            "DECIDE",
            summary=f"{decision.get('mode')} / {decision.get('story_type')}",
            **{k: decision.get(k) for k in ("mode", "story_type", "confidence")},
        )
        ledger.write_json("feasibility.json", decision)
        return decision

    def on_event(etype: str, payload: dict[str, Any]) -> None:
        if etype == "thought":
            ledger.emit("THINK", text=payload.get("text"), summary=(payload.get("text") or "")[:160])
        elif etype == "tool_start":
            ledger.emit(
                "MCP_CALL",
                tool=payload.get("tool"),
                arguments=payload.get("arguments"),
                dry_run=False,
                phase="feasibility",
                summary=f"call {payload.get('tool')}",
            )
        elif etype == "tool_result":
            ledger.emit(
                "MCP_RESULT",
                tool=payload.get("tool"),
                ok=payload.get("ok"),
                summary=payload.get("summary"),
                phase="feasibility",
            )
        elif etype == "status":
            ledger.emit("STATUS", message=payload.get("message"), summary=payload.get("message"))

    try:
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
        decision = _extract_json(outcome.get("reply") or "") or heuristic_feasibility(issue, allowlist)
        decision["_model"] = outcome.get("model")
        decision["_provider"] = outcome.get("provider")
    except Exception as exc:  # noqa: BLE001
        ledger.emit("ERROR", message=str(exc), summary=f"feasibility LLM failed: {exc}")
        decision = heuristic_feasibility(issue, allowlist)
        decision["reasons"] = list(decision.get("reasons") or []) + [f"LLM fallback: {exc}"]

    # Enforce allowlist
    st = decision.get("story_type")
    if decision.get("mode") == "MCP_E2E" and st not in allowlist:
        decision["mode"] = "BLOCKED"
        decision["reasons"] = list(decision.get("reasons") or []) + [
            f"story_type {st} not in allowlist"
        ]

    ledger.emit(
        "DECIDE",
        summary=f"{decision.get('mode')} / {decision.get('story_type')}",
        mode=decision.get("mode"),
        story_type=decision.get("story_type"),
        confidence=decision.get("confidence"),
    )
    ledger.write_json("feasibility.json", decision)
    return decision
