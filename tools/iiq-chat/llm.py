"""OpenRouter agent loop: native tool-calling over live MCP tools."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# on_event(event_type, payload) — used by SSE /api/chat/stream for live UX
EventCallback = Callable[[str, dict[str, Any]], None]

DEFAULT_MODELS = [
    "openrouter/free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
]

# Role + safety only — no tool routing heuristics.
SYSTEM_PROMPT = """You are Meridian Teller, a SailPoint IdentityIQ lab assistant for Meridian National Bank.
You help operators query and operate a local IIQ lab via MCP tools.

Rules:
- Use the provided tools to answer factual questions about identities, apps, access, certs, and ops.
- Prefer read tools. Use write/mutate tools only when the user clearly asks to change something.
- Never invent tool names or fabricate IIQ data — only use tool results.
- Call tools immediately for factual questions. Do not write long speculation about what an ID might mean.
- Lab identity keys are real identifiers: dotted logins (anita.rao), employee numbers (MNB00002),
  and display names like "Christopher Hayes (MNB00002)". These are NOT ticket/request numbers.
- "Who reports to / under / direct reports of X" → use list_transitive_reports (manager=X) or
  get_manager_hierarchy. Prefer list_transitive_reports for "all individuals who report under".
- When a search returns candidates, follow up with detail tools if needed to answer fully.
- People in answers: always use human display names (e.g. Raj Ross). Prefer `label` / `displayName`
  / `reportLabels` / `peopleLabels` / `tellerCard` / `*Label` fields from tool results.
  Put the key in parentheses only when useful: Raj Ross (MNB00026).
  Never list bare MNB##### / login keys as the only identifier when a display name is available.
- Final answers: GitHub-flavored Markdown the UI will render. Use a short intro sentence, then
  ## headings and bullet lists for people/apps. Prefer headings over bold-for-structure.
  Keep lists scannable; stay concise unless the user asks for detail.
- If no tool is needed (greetings / pure how-to), answer directly without tools.
"""

MAX_AGENT_STEPS = int(os.environ.get("TELLER_MAX_AGENT_STEPS", "5"))


class LlmError(RuntimeError):
    pass


class LlmCancelled(LlmError):
    """Raised when the client aborts an in-flight agent run."""


def _emit(on_event: EventCallback | None, event_type: str, **payload: Any) -> None:
    if not on_event:
        return
    try:
        on_event(event_type, payload)
    except Exception:  # noqa: BLE001
        pass


def _extract_thought(msg: dict[str, Any]) -> str:
    """Pull model reasoning / interim text (not the final user-facing reply alone)."""
    bits: list[str] = []
    content = (msg.get("content") or "").strip()
    if content:
        bits.append(content)
    for key in ("reasoning", "reasoning_content"):
        val = msg.get(key)
        if isinstance(val, str) and val.strip():
            bits.append(val.strip())
    details = msg.get("reasoning_details")
    if isinstance(details, list):
        for item in details:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                if isinstance(text, str) and text.strip():
                    bits.append(text.strip())
            elif isinstance(item, str) and item.strip():
                bits.append(item.strip())
    # Dedupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for b in bits:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return "\n\n".join(out)


def _brief_tool_result(result: Any) -> str:
    if isinstance(result, dict):
        if result.get("ok") is False:
            err = result.get("error") or "failed"
            return f"error: {err}" if not isinstance(err, dict) else "error"
        data = result.get("data", result)
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            total = data.get("totalResults", len(data["items"]))
            return f"{len(data['items'])} shown · {total} total"
        if isinstance(data, dict) and isinstance(data.get("reports"), list):
            n = data.get("count", len(data["reports"]))
            labels = data.get("reportLabels") or [
                (r.get("label") or r.get("displayName") or r.get("name"))
                for r in data["reports"]
                if isinstance(r, dict)
            ]
            sample = ", ".join(str(x) for x in labels[:6] if x)
            more = f" (+{n - 6} more)" if n > 6 else ""
            return f"{n} report(s)" + (f": {sample}{more}" if sample else "")
        if isinstance(data, list):
            return f"{len(data)} item(s)"
        if isinstance(data, dict):
            if data.get("count") is not None and not isinstance(data.get("count"), bool):
                return f"{data['count']} result(s)"
            name = data.get("displayName") or data.get("userName") or data.get("name")
            if name:
                return str(name)
            return f"{len(data)} fields"
        if isinstance(data, str):
            return data[:120]
    return "done"


def _skippable_model_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if "no endpoints found" in msg:
        return True
    if "http 404" in msg and ("endpoint" in msg or "model" in msg or "not found" in msg):
        return True
    if "tool" in msg and ("not support" in msg or "unsupported" in msg):
        return True
    return False


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 90.0,
    ) -> None:
        raw = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        self.api_key = (raw or "").strip().strip("\"'")
        self.model = model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODELS[0]
        self.timeout = timeout
        self.fallback_models = [
            m.strip()
            for m in (os.environ.get("OPENROUTER_FALLBACK_MODELS") or ",".join(DEFAULT_MODELS)).split(
                ","
            )
            if m.strip()
        ]

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def validate_key(self) -> dict[str, Any]:
        if not self.api_key:
            return {"ok": False, "error": "OPENROUTER_API_KEY is empty"}
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            hint = ""
            if exc.code == 401:
                hint = (
                    " Create a new key at https://openrouter.ai/keys then recreate "
                    "iiq-chat with OPENROUTER_API_KEY=sk-or-v1-…"
                )
            return {"ok": False, "error": f"OpenRouter HTTP {exc.code}: {detail}{hint}"}
        except urllib.error.URLError as exc:
            return {"ok": False, "error": f"OpenRouter unreachable: {exc}"}
        data = body.get("data") or body
        return {
            "ok": True,
            "label": data.get("label"),
            "is_free_tier": data.get("is_free_tier"),
            "limit_remaining": data.get("limit_remaining"),
        }

    def run_agent(
        self,
        user_message: str,
        openai_tools: list[dict[str, Any]],
        call_tool: Callable[[str, dict[str, Any]], Any],
        *,
        history: list[dict[str, str]] | None = None,
        allowed_names: set[str] | None = None,
        max_steps: int | None = None,
        on_event: EventCallback | None = None,
        is_cancelled: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        """Multi-step tool-calling loop. call_tool(name, args) → result."""
        if not self.api_key:
            raise LlmError(
                "OPENROUTER_API_KEY is not set. Use the tools rail for MCP without an LLM."
            )
        if not openai_tools:
            raise LlmError("No MCP tools available — is the MCP server up?")

        allowed = allowed_names or {t["function"]["name"] for t in openai_tools if "function" in t}
        steps: list[dict[str, Any]] = []
        limit = max_steps if max_steps is not None else MAX_AGENT_STEPS

        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in (history or [])[-6:]:
            role = turn.get("role")
            content = turn.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        model_used: str | None = None
        last_err: Exception | None = None
        models = [self.model] + [m for m in self.fallback_models if m != self.model]

        def _check_cancel() -> None:
            if is_cancelled and is_cancelled():
                raise LlmCancelled("Stopped by operator")

        _emit(on_event, "status", message="Planning next step…", phase="start")

        for model in models:
            _check_cancel()
            short = model.split("/")[-1]
            _emit(
                on_event,
                "status",
                message=f"Consulting {short}…",
                phase="llm",
                model=model,
            )
            try:
                reply, model_used, steps = self._agent_loop(
                    model,
                    messages,
                    openai_tools,
                    call_tool,
                    allowed,
                    limit,
                    on_event=on_event,
                    is_cancelled=is_cancelled,
                )
                return {
                    "ok": True,
                    "reply": reply,
                    "model": model_used,
                    "steps": steps,
                    "tool": steps[-1]["tool"] if steps else None,
                    "result": steps[-1]["result"] if steps else None,
                }
            except LlmCancelled:
                raise
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                _emit(
                    on_event,
                    "status",
                    message=f"{short} unavailable — trying another model…",
                    phase="fallback",
                    model=model,
                    error=str(exc)[:200],
                )
                if _skippable_model_error(exc):
                    continue
                continue
        raise LlmError(f"OpenRouter agent failed across models: {last_err}")

    def _agent_loop(
        self,
        model: str,
        messages: list[dict[str, Any]],
        openai_tools: list[dict[str, Any]],
        call_tool: Callable[[str, dict[str, Any]], Any],
        allowed: set[str],
        max_steps: int,
        *,
        on_event: EventCallback | None = None,
        is_cancelled: Callable[[], bool] | None = None,
    ) -> tuple[str, str, list[dict[str, Any]]]:
        steps: list[dict[str, Any]] = []
        # Copy so retries with another model start clean
        msgs = [dict(m) for m in messages]
        short = model.split("/")[-1]

        def _check_cancel() -> None:
            if is_cancelled and is_cancelled():
                raise LlmCancelled("Stopped by operator")

        for round_i in range(max_steps):
            _check_cancel()
            # After tools run, the next OpenRouter round is usually the slowest step
            # (free models + large tool schemas). Label it clearly — that wait is NOT
            # local "writing", it's the model synthesizing the reply.
            if steps:
                _emit(
                    on_event,
                    "status",
                    message=f"Waiting on {short} for the answer…",
                    phase="llm",
                    model=model,
                    round=round_i + 1,
                )
            else:
                _emit(
                    on_event,
                    "status",
                    message=f"Waiting on {short}…",
                    phase="llm",
                    model=model,
                    round=round_i + 1,
                )

            msg = self._complete_message(model, msgs, tools=openai_tools)
            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()
            thought = _extract_thought(msg)

            if not tool_calls:
                if thought and content and thought != content:
                    # reasoning separate from final answer
                    _emit(on_event, "thought", text=thought.replace(content, "").strip() or thought)
                # No separate "Finishing…" pause — return immediately so the UI can
                # show the answer (the slow work already happened in Waiting on…).
                if content:
                    return content, model, steps
                if steps:
                    # Model returned empty after tools — fall back to local summary
                    last = steps[-1]
                    return _local_summary(last["tool"], last["result"]), model, steps
                return "I need a bit more detail to help with that.", model, steps

            if thought:
                _emit(on_event, "thought", text=thought, round=round_i + 1)

            n = len(tool_calls)
            _emit(
                on_event,
                "status",
                message=f"Running {n} tool{'s' if n != 1 else ''}…",
                phase="tools",
                model=model,
                count=n,
            )

            # Append assistant message with tool_calls for the protocol
            msgs.append(
                {
                    "role": "assistant",
                    "content": content or None,
                    "tool_calls": tool_calls,
                }
            )

            for tc in tool_calls:
                _check_cancel()
                fn = tc.get("function") or {}
                name = str(fn.get("name") or "")
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                except json.JSONDecodeError:
                    args = {}
                if not isinstance(args, dict):
                    args = {}

                index = len(steps)
                _emit(
                    on_event,
                    "tool_start",
                    tool=name,
                    arguments=args,
                    index=index,
                )

                if name not in allowed:
                    result: Any = {"ok": False, "error": f"Tool not in live MCP catalog: {name}"}
                else:
                    try:
                        result = call_tool(name, args)
                    except LlmCancelled:
                        raise
                    except Exception as exc:  # noqa: BLE001
                        result = {"ok": False, "error": str(exc)}

                ok = not (isinstance(result, dict) and result.get("ok") is False)
                _emit(
                    on_event,
                    "tool_result",
                    tool=name,
                    arguments=args,
                    index=index,
                    ok=ok,
                    summary=_brief_tool_result(result),
                )

                fixed_args = args
                last_fixed = getattr(call_tool, "last_fixed", None)
                if isinstance(last_fixed, dict) and last_fixed:
                    fixed_args = last_fixed
                steps.append(
                    {
                        "tool": name,
                        "arguments": args,
                        "normalizedArguments": fixed_args,
                        "result": result,
                    }
                )
                msgs.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.get("id") or name,
                        "content": json.dumps(result, default=str)[:12000],
                    }
                )

        # Max steps exhausted — summarize last tool result
        _emit(
            on_event,
            "status",
            message="Max tool steps reached — summarizing…",
            phase="limit",
            model=model,
        )
        if steps:
            last = steps[-1]
            return _local_summary(last["tool"], last["result"]), model, steps
        return "Stopped after maximum tool steps without an answer.", model, steps

    def _complete_message(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1200,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "http://localhost:4180"),
                "X-Title": "Meridian IIQ Teller",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:400]
            if exc.code == 401:
                raise LlmError(
                    "OpenRouter rejected the API key (401). "
                    "Create a new key at https://openrouter.ai/keys and recreate iiq-chat."
                ) from exc
            raise LlmError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LlmError(f"OpenRouter unreachable: {exc}") from exc

        choices = payload.get("choices") or []
        if not choices:
            raise LlmError(f"OpenRouter empty response: {payload}")
        message = choices[0].get("message") or {}
        if not isinstance(message, dict):
            raise LlmError("OpenRouter message missing")
        return message


def _bad_summary(text: str) -> bool:
    if not text or len(text) < 12:
        return True
    low = text.lower().strip()
    if low in {"safe", "unsafe", "yes", "no", "ok", "true", "false"}:
        return True
    if "user safety" in low or low.startswith("safety"):
        return True
    if "as an ai" in low and "cannot" in low and len(low) < 80:
        return True
    return False


def _local_summary(tool: str, result: Any, user_message: str = "") -> str:
    del user_message  # kept for call-site compatibility
    if isinstance(result, dict):
        if result.get("ok") is False:
            err = result.get("error") or result
            return f"{tool} failed: {err}"
        data = result.get("data", result)

        if isinstance(data, dict):
            hints = data.get("profileHints") or {}
            if isinstance(hints, dict) and hints.get("resolvedTitle"):
                who = (data.get("identity") or {}).get("userName") or ""
                prefix = f"{who}: " if who else ""
                return f"{prefix}Job title: {hints['resolvedTitle']}"

        if tool in ("search_identities", "search_profiles") and isinstance(data, dict):
            items = data.get("items") or []
            total = data.get("totalResults", len(items))
            via = data.get("matchedVia")
            if not items:
                return f"No identities matched that search ({total} results)."
            labels: list[str] = []
            for i in items[:8]:
                if not isinstance(i, dict):
                    continue
                name = str(i.get("displayName") or i.get("userName") or i.get("id") or "")
                ph = i.get("profileHints") if isinstance(i.get("profileHints"), dict) else {}
                bits: list[str] = []
                for k in ("resolvedTitle", "title", "jobTitle", "location", "departmentName"):
                    if ph.get(k) and str(ph[k]) not in bits:
                        bits.append(str(ph[k]))
                labels.append(f"{name} ({', '.join(bits)})" if bits else name)
            suffix = " via HR profile attrs" if via == "account_profile" else ""
            return f"Found {total} identity(ies){suffix}: {', '.join(labels)}"

        if tool == "list_transitive_reports" and isinstance(data, dict):
            reports = data.get("reports") or []
            mgr = data.get("managerLabel") or data.get("manager") or "manager"
            labels = data.get("reportLabels") or [
                (r.get("label") or r.get("displayName") or r.get("name"))
                for r in reports
                if isinstance(r, dict)
            ]
            body = "\n".join(f"- {x}" for x in labels if x)
            return (
                f"{mgr} has {len(labels)} people reporting under them:\n\n"
                f"## Direct reports\n\n{body}"
            )

        if isinstance(data, list):
            return f"{tool} returned {len(data)} item(s)."
        if isinstance(data, dict):
            un = data.get("userName") or data.get("displayName")
            if un:
                return f"{tool} succeeded for {un}."
            keys = ", ".join(list(data.keys())[:8])
            return f"{tool} succeeded. Keys: {keys}"
    return f"{tool} completed."
