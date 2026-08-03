"""Evidence pack + handoff comment body (In Review)."""

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


def _comment_from_reply(reply: str, parsed: dict[str, Any] | None) -> str:
    """Prefer structured comment; otherwise Markdown before the JSON fence/object."""
    if parsed:
        for key in ("comment", "jira_comment", "body"):
            val = parsed.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    text = (reply or "").strip()
    if not text:
        return ""
    # Drop trailing fenced JSON or raw JSON object so Jira stays human-readable.
    fence = re.search(r"```(?:json)?\s*\n\{", text, flags=re.IGNORECASE)
    if fence:
        return text[: fence.start()].strip()
    brace = re.search(r"\n\{[\s\S]*\}\s*$", text)
    if brace:
        return text[: brace.start()].strip()
    return text


def build_evidence(
    *,
    ledger: RunLedger,
    issue: dict[str, Any],
    decision: dict[str, Any],
    implement: dict[str, Any] | None,
    verify: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    steps = (implement or {}).get("steps") or []
    tools = []
    for s in steps:
        t = s.get("tool")
        if t and t not in tools:
            tools.append(t)
    evidence = {
        "issue": issue.get("key"),
        "dry_run": dry_run,
        "mode": decision.get("mode"),
        "story_type": decision.get("story_type"),
        "verify_ok": verify.get("ok"),
        "mcp_tools_used": tools,
        "implement_model": (implement or {}).get("model"),
        "run_dir": str(ledger.run_dir),
    }
    ledger.write_json("evidence.json", evidence)
    return evidence


def run_handoff(
    *,
    provider: LlmProvider | None,
    mcp: WrappedMcp,
    ledger: RunLedger,
    issue: dict[str, Any],
    decision: dict[str, Any],
    implement: dict[str, Any] | None,
    verify: dict[str, Any],
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    dry = bool(evidence.get("dry_run"))
    residual = "Residual risk: dry_run skips writes." if dry else "Residual risk: lab-only; PM owns Done."
    default_comment = (
        f"{issue.get('key')}: ready for review ({decision.get('story_type')}, "
        f"{'PASS' if verify.get('ok') else 'FAIL'}).\n"
        f"How to test: open the objects named in the story and confirm live IIQ matches acceptance.\n"
        f"{residual}"
    )

    handoff: dict[str, Any] = {
        "ready_for_review": bool(verify.get("ok")) and decision.get("mode") == "MCP_E2E",
        "summary": (implement or {}).get("reply") or default_comment,
        "comment": default_comment,
        "how_to_test": ["Validate acceptance criteria on the live lab"],
        "residual_risk": ["Dry-run" if dry else "Lab environment"],
        "mcp_tools_used": evidence.get("mcp_tools_used") or [],
    }

    if provider and provider.api_key:
        system = compose_system(str(decision.get("story_type") or ""), "handoff.md")
        user = json.dumps(
            {
                "issue": issue,
                "decision": decision,
                "implement_reply": (implement or {}).get("reply"),
                "verify": verify,
                "evidence": evidence,
            },
            indent=2,
        )
        tools = mcp.openai_tools(allow_writes=False)

        def on_event(etype: str, payload: dict[str, Any]) -> None:
            if etype == "thought":
                ledger.emit("THINK", text=payload.get("text"), summary=(payload.get("text") or "")[:120])

        try:
            outcome = run_tool_agent(
                provider,
                system_prompt=system,
                user_message=user,
                openai_tools=tools
                or [
                    {
                        "type": "function",
                        "function": {
                            "name": "noop",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
                call_tool=mcp.call,
                max_steps=4,
                on_event=on_event,
            )
            reply = outcome.get("reply") or ""
            parsed = _extract_json(reply)
            if parsed:
                # Keep evidence tools; LLM may omit or invent mcp_tools_used.
                tools_used = handoff.get("mcp_tools_used") or []
                handoff.update(parsed)
                if not handoff.get("mcp_tools_used"):
                    handoff["mcp_tools_used"] = tools_used
            comment = _comment_from_reply(reply, parsed) or default_comment
            handoff["comment"] = comment[:4000]
            if not str(handoff.get("summary") or "").strip():
                handoff["summary"] = comment.splitlines()[0][:240] if comment else default_comment
        except Exception as exc:  # noqa: BLE001
            ledger.emit("ERROR", message=str(exc), summary=f"handoff LLM: {exc}")

    ledger.write_json("handoff.json", handoff)
    ledger.emit(
        "HANDOFF",
        summary=f"ready_for_review={handoff.get('ready_for_review')}",
        ready_for_review=handoff.get("ready_for_review"),
    )
    return handoff
