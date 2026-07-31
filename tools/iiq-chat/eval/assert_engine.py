"""Pure assertion engine for Teller blackbox responses (no LLM / network)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AssertResult:
    ok: bool
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def merge(self, other: "AssertResult") -> "AssertResult":
        return AssertResult(
            ok=self.ok and other.ok,
            failures=self.failures + other.failures,
            notes=self.notes + other.notes,
        )


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _reply_text(response: dict[str, Any]) -> str:
    return str(response.get("reply") or "")


def _tools_used(response: dict[str, Any]) -> list[str]:
    steps = response.get("steps") if isinstance(response.get("steps"), list) else []
    names: list[str] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        tool = step.get("tool")
        if tool:
            names.append(str(tool))
    # Compat: single last tool field
    if not names and response.get("tool"):
        names.append(str(response["tool"]))
    return names


def _step_blob(response: dict[str, Any]) -> str:
    """Lowercased JSON-ish dump of steps for error scanning."""
    steps = response.get("steps") or []
    try:
        import json

        return json.dumps(steps, default=str).lower()
    except Exception:  # noqa: BLE001
        return str(steps).lower()


def _tool_error_messages(response: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    steps = response.get("steps") if isinstance(response.get("steps"), list) else []
    for step in steps:
        if not isinstance(step, dict):
            continue
        tool = step.get("tool") or "?"
        result = step.get("result")
        if not isinstance(result, dict):
            continue
        if result.get("ok") is False:
            errs.append(f"{tool}: {result.get('error') or result}")
            continue
        # Nested MCP/IIQ error envelopes
        err = result.get("error")
        if isinstance(err, dict) and (err.get("code") or err.get("message")):
            errs.append(f"{tool}: {err}")
        data = result.get("data")
        if isinstance(data, dict) and data.get("success") is False:
            errs.append(f"{tool}: success=false {data}")
        # SCIM-style failures surfaced in message
        msg = str(result.get("message") or "")
        if "invalid filter" in msg.lower() or "http_status" in str(result).lower():
            if '"ok": false' in str(result).lower() or "invalid" in msg.lower():
                errs.append(f"{tool}: {msg or result}")
    return errs


def _tool_results_by_name(response: dict[str, Any]) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {}
    steps = response.get("steps") if isinstance(response.get("steps"), list) else []
    for step in steps:
        if not isinstance(step, dict):
            continue
        tool = step.get("tool")
        if not tool:
            continue
        out.setdefault(str(tool), []).append(step.get("result"))
    return out


def _result_looks_ok(result: Any) -> bool:
    if not isinstance(result, dict):
        return True
    if result.get("ok") is False:
        return False
    err = result.get("error")
    if isinstance(err, dict) and (err.get("code") or err.get("http_status")):
        return False
    return True


def evaluate_expect(expect: dict[str, Any], response: dict[str, Any]) -> AssertResult:
    """Evaluate a single expect block against a Teller /api/chat JSON body."""
    failures: list[str] = []
    notes: list[str] = []
    reply = _reply_text(response)
    reply_l = reply.lower()
    tools = _tools_used(response)
    tools_set = set(tools)
    blob = _step_blob(response)
    by_name = _tool_results_by_name(response)

    if expect.get("http_ok", True):
        if response.get("ok") is False:
            failures.append(f"response.ok is false: {response.get('error') or response}")
        if response.get("mode") == "llm" and not reply and not tools:
            failures.append("empty reply and no tools used")

    if "min_tools" in expect:
        n = int(expect["min_tools"])
        if len(tools) < n:
            failures.append(f"expected >= {n} tool call(s), got {len(tools)}: {tools}")

    if "max_tools" in expect:
        n = int(expect["max_tools"])
        if len(tools) > n:
            failures.append(f"expected <= {n} tool call(s), got {len(tools)}: {tools}")

    for needle in _as_list(expect.get("reply_contains")):
        if str(needle).lower() not in reply_l:
            failures.append(f"reply missing required text: {needle!r}")

    any_needles = _as_list(expect.get("reply_contains_any"))
    if any_needles and not any(str(n).lower() in reply_l for n in any_needles):
        failures.append(f"reply matched none of reply_contains_any={any_needles!r}; reply={reply[:240]!r}")

    for needle in _as_list(expect.get("reply_not_contains")):
        if str(needle).lower() in reply_l:
            failures.append(f"reply must not contain: {needle!r}")

    for needle in _as_list(expect.get("reply_not_contains_any")):
        if str(needle).lower() in reply_l:
            failures.append(f"reply must not contain (any-list): {needle!r}")

    for pattern in _as_list(expect.get("reply_regex")):
        if not re.search(str(pattern), reply, flags=re.IGNORECASE | re.DOTALL):
            failures.append(f"reply regex not matched: {pattern!r}")

    any_tools = _as_list(expect.get("tools_any_of"))
    if any_tools and not any(t in tools_set for t in any_tools):
        failures.append(f"none of tools_any_of={any_tools} used; got {tools}")

    for t in _as_list(expect.get("tools_all_of")):
        if t not in tools_set:
            failures.append(f"required tool missing: {t}; got {tools}")

    for t in _as_list(expect.get("tools_forbidden")):
        if t in tools_set:
            failures.append(f"forbidden tool used: {t}")

    ok_any = _as_list(expect.get("require_ok_tools_any_of"))
    if ok_any:
        ok_hit = False
        for t in ok_any:
            for res in by_name.get(str(t), []):
                if _result_looks_ok(res):
                    ok_hit = True
                    break
            if ok_hit:
                break
        if not ok_hit:
            failures.append(f"none of require_ok_tools_any_of={ok_any} returned ok; got {tools}")

    if expect.get("no_tool_errors"):
        # If require_ok_tools_any_of is set, only flag errors on those tools / last step.
        focus = {str(t) for t in ok_any} if ok_any else None
        errs = []
        for e in _tool_error_messages(response):
            if focus is None or any(t in e for t in focus):
                errs.append(e)
        quirk_needles = _as_list(
            expect.get("forbidden_step_substrings")
            or [
                "invalid filter",
                "attribute not found",
                "method not allowed",
                "http_status': 400",
                '"http_status": 400',
                "http_status': 405",
                '"http_status": 405',
            ]
        )
        allow = {str(a).lower() for a in _as_list(expect.get("allow_step_substrings"))}
        # When focusing on primary tools, scan only those steps for quirks
        scan_blob = blob
        if focus:
            focused_steps = [
                s
                for s in (response.get("steps") or [])
                if isinstance(s, dict) and str(s.get("tool")) in focus
            ]
            try:
                import json

                scan_blob = json.dumps(focused_steps, default=str).lower()
            except Exception:  # noqa: BLE001
                scan_blob = str(focused_steps).lower()
        for q in quirk_needles:
            ql = str(q).lower()
            if ql in allow:
                continue
            if ql in scan_blob:
                errs.append(f"step dump contains forbidden substring: {q!r}")
        if errs:
            failures.append("tool errors / quirks: " + " | ".join(str(e)[:200] for e in errs[:5]))

    for needle in _as_list(expect.get("steps_contain_any")):
        if str(needle).lower() not in blob:
            failures.append(f"steps missing required substring: {needle!r}")

    if failures:
        notes.append(f"tools={tools}")
        notes.append(f"reply_preview={reply[:180]!r}")
    return AssertResult(ok=not failures, failures=failures, notes=notes)


def evaluate_case(case: dict[str, Any], response: dict[str, Any]) -> AssertResult:
    """Evaluate a golden case. Supports expect OR pass_if_any (OR of expect blocks)."""
    if case.get("skip"):
        return AssertResult(ok=True, notes=["skipped"])

    alts = case.get("pass_if_any")
    if isinstance(alts, list) and alts:
        results = [evaluate_expect(a if isinstance(a, dict) else {}, response) for a in alts]
        if any(r.ok for r in results):
            winners = [i for i, r in enumerate(results) if r.ok]
            return AssertResult(ok=True, notes=[f"pass_if_any matched branch {winners[0]}"])
        # Aggregate failures from all branches
        failures = []
        for i, r in enumerate(results):
            failures.append(f"branch[{i}]: " + "; ".join(r.failures[:3]))
        return AssertResult(ok=False, failures=failures, notes=[f"tools={_tools_used(response)}"])

    expect = case.get("expect") if isinstance(case.get("expect"), dict) else {}
    return evaluate_expect(expect, response)
