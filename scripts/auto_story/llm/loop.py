"""Teller-class tool-calling agent loop over a swappable LlmProvider."""

from __future__ import annotations

import json
from typing import Any, Callable

from .provider import LlmError, LlmProvider

EventCallback = Callable[[str, dict[str, Any]], None]


def _emit(cb: EventCallback | None, etype: str, **payload: Any) -> None:
    if cb:
        cb(etype, payload)


def _extract_thought(msg: dict[str, Any]) -> str:
    for key in ("reasoning", "reasoning_content"):
        v = msg.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def run_tool_agent(
    provider: LlmProvider,
    *,
    system_prompt: str,
    user_message: str,
    openai_tools: list[dict[str, Any]],
    call_tool: Callable[[str, dict[str, Any]], Any],
    max_steps: int = 24,
    on_event: EventCallback | None = None,
    verbose_think: bool = False,
) -> dict[str, Any]:
    """Multi-step OpenAI-compatible tool loop (Teller-class)."""
    if not openai_tools:
        raise LlmError("No tools available for agent loop")

    allowed = {t["function"]["name"] for t in openai_tools if "function" in t}
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    steps: list[dict[str, Any]] = []
    models = [provider.model] + [m for m in provider.fallback_models if m != provider.model]
    last_err: Exception | None = None

    for model in models:
        try:
            reply, steps = _loop(
                provider,
                model,
                messages,
                openai_tools,
                allowed,
                call_tool,
                max_steps,
                on_event=on_event,
                verbose_think=verbose_think,
            )
            return {
                "ok": True,
                "reply": reply,
                "model": model,
                "provider": provider.provider,
                "steps": steps,
            }
        except LlmError as exc:
            last_err = exc
            _emit(on_event, "status", message=f"Model {model} failed: {exc}")
            continue
    raise LlmError(f"All models failed: {last_err}")


def _loop(
    provider: LlmProvider,
    model: str,
    base_messages: list[dict[str, Any]],
    openai_tools: list[dict[str, Any]],
    allowed: set[str],
    call_tool: Callable[[str, dict[str, Any]], Any],
    max_steps: int,
    *,
    on_event: EventCallback | None,
    verbose_think: bool,
) -> tuple[str, list[dict[str, Any]]]:
    msgs = [dict(m) for m in base_messages]
    steps: list[dict[str, Any]] = []

    for round_i in range(max_steps):
        _emit(on_event, "status", message=f"LLM round {round_i + 1}", model=model)
        raw = provider.chat_completions(model=model, messages=msgs, tools=openai_tools)
        choices = raw.get("choices") or []
        if not choices:
            raise LlmError(f"Empty choices from model {model}")
        msg = choices[0].get("message") or {}
        content = (msg.get("content") or "").strip()
        thought = _extract_thought(msg)
        if thought:
            text = thought if verbose_think else (thought[:400] + ("…" if len(thought) > 400 else ""))
            _emit(on_event, "thought", text=text, round=round_i + 1)

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            if content:
                return content, steps
            if steps:
                last = steps[-1]
                return f"(no final text) last tool={last.get('tool')}", steps
            return "No tools invoked and empty reply.", steps

        msgs.append(
            {
                "role": "assistant",
                "content": content or None,
                "tool_calls": tool_calls,
            }
        )

        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = str(fn.get("name") or "")
            raw_args = fn.get("arguments") or "{}"
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except json.JSONDecodeError:
                args = {}
            if not isinstance(args, dict):
                args = {}

            _emit(on_event, "tool_start", tool=name, arguments=args, index=len(steps))
            if name not in allowed:
                result: Any = {"ok": False, "error": f"Tool not allowed: {name}"}
            else:
                try:
                    result = call_tool(name, args)
                except Exception as exc:  # noqa: BLE001
                    result = {"ok": False, "error": str(exc)}

            ok = not (isinstance(result, dict) and result.get("ok") is False)
            steps.append({"tool": name, "arguments": args, "result": result, "ok": ok})
            _emit(
                on_event,
                "tool_result",
                tool=name,
                ok=ok,
                index=len(steps) - 1,
                summary=str(result)[:200],
            )
            msgs.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id") or f"call_{len(steps)}",
                    "content": json.dumps(result, default=str)[:50000],
                }
            )

    return "Max agent steps reached without final answer.", steps
