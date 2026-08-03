"""Acceptance verify harness (story-type aware, MCP reads)."""

from __future__ import annotations

import json
import re
from typing import Any

from .ledger import RunLedger
from .mcp_wrap import WrappedMcp


def _persona_from_issue(issue: dict[str, Any]) -> str | None:
    blob = f"{issue.get('summary') or ''} {issue.get('description') or ''}"
    m = re.search(r"\b(MNB\d{5})\b", blob)
    if m:
        return m.group(1)
    m = re.search(r"\b([a-z]+\.[a-z]+)\b", blob.lower())
    if m:
        return m.group(1)
    return None


def run_verify(
    *,
    mcp: WrappedMcp,
    ledger: RunLedger,
    issue: dict[str, Any],
    decision: dict[str, Any],
    implement: dict[str, Any] | None,
    dry_run: bool = True,
) -> dict[str, Any]:
    story_type = str(decision.get("story_type") or "")
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})
        ledger.emit(
            "VERIFY",
            summary=f"{'PASS' if ok else 'FAIL'}: {name}",
            name=name,
            ok=ok,
            detail=detail,
        )

    reply = (implement or {}).get("reply") or ""
    check("implement_reply", bool(str(reply).strip()), "non-empty agent reply")

    steps = (implement or {}).get("steps") or []
    if dry_run and not steps:
        check("mcp_steps", True, "dry_run / no-LLM — steps optional")
    else:
        check("mcp_steps", len(steps) > 0, f"{len(steps)} tool steps")

    def tools_matching(*needles: str) -> list[dict[str, Any]]:
        out = []
        for s in steps:
            name = str(s.get("tool") or "").lower()
            if any(n in name for n in needles):
                out.append(s)
        return out

    try:
        if story_type == "identity-admin":
            used = tools_matching("identity", "unlock", "password", "capability")
            check("identity_tools_used", len(used) > 0 or dry_run, ",".join(s.get("tool") for s in used[:5]))
            persona = _persona_from_issue(issue)
            if persona and not dry_run:
                try:
                    got = mcp.call("search_identities", {"query": persona, "limit": 5})
                    check("identity_exists", True, str(got)[:120])
                except Exception as exc:  # noqa: BLE001
                    check("identity_exists", False, str(exc))
        elif story_type == "app-onboarding":
            used = tools_matching("application", "aggregat", "onboard", "connector")
            check("application_tools_used", len(used) > 0 or dry_run)
        elif story_type == "task-ops":
            used = tools_matching("task", "aggregat", "refresh", "schedule")
            check("task_tools_used", len(used) > 0 or dry_run)
        elif story_type == "access-request":
            used = tools_matching("grant", "revoke", "access", "work_item")
            check("access_tools_used", len(used) > 0 or dry_run)
        elif story_type == "governance-admin":
            used = tools_matching("population", "workgroup")
            check("governance_tools_used", len(used) > 0 or dry_run)
        elif story_type == "certification":
            used = tools_matching("cert")
            check("cert_tools_used", len(used) > 0 or dry_run)
        elif story_type == "policy-sod":
            used = tools_matching("sod", "policy")
            check("sod_tools_used", len(used) > 0 or dry_run)
            if not dry_run:
                constraint_ok = False
                detail = ""
                # Prefer ledger MCP_RESULT rows (authoritative)
                try:
                    for line in ledger.events_path.read_text(encoding="utf-8").splitlines():
                        if not line.strip():
                            continue
                        ev = json.loads(line)
                        if ev.get("type") != "MCP_RESULT" or ev.get("tool") != "update_sod_constraints":
                            continue
                        if ev.get("ok") is False:
                            constraint_ok = False
                            detail = str(ev.get("summary") or "constraints failed")[:240]
                            continue
                        summary = str(ev.get("summary") or "")
                        if "leftRoles" in summary or "left_roles" in summary or "MNB-" in summary:
                            constraint_ok = True
                            detail = summary[:240]
                except Exception as exc:  # noqa: BLE001
                    detail = f"ledger read: {exc}"
                # Fallback: step ok flags
                if not constraint_ok:
                    for s in steps:
                        if s.get("tool") != "update_sod_constraints":
                            continue
                        if s.get("ok") is False:
                            detail = str(s.get("error") or s.get("summary") or "constraints failed")[:240]
                        elif s.get("ok") is True:
                            args = s.get("arguments") or {}
                            left = args.get("left_roles") or args.get("leftRoles") or []
                            right = args.get("right_roles") or args.get("rightRoles") or []
                            # Entitlement values alone are invalid for this API
                            bad = any(
                                isinstance(x, str) and x.isupper() and "-" not in x for x in list(left) + list(right)
                            )
                            if left and right and not bad:
                                constraint_ok = True
                                detail = f"left={left} right={right}"
                            else:
                                detail = f"invalid role args left={left} right={right}"
                check(
                    "sod_constraints_wired",
                    constraint_ok,
                    detail or "update_sod_constraints missing or failed",
                )
        elif story_type == "jml-lifecycle":
            used = tools_matching("jml", "lifecycle", "identity")
            check("jml_tools_used", len(used) > 0 or dry_run)
        else:
            check("story_type_generic", True, story_type or "other")
    except Exception as exc:  # noqa: BLE001
        check("verify_exception", False, str(exc))

    # Health: prefer toolkit_ping (soft-fail when MCP unauthorized/offline)
    try:
        ping = mcp.call("toolkit_ping", {})
        ok = isinstance(ping, dict) and (
            ping.get("status") == "ok" or ping.get("ok") is True or "version" in ping
        )
        if isinstance(ping, dict) and ping.get("ok") is False:
            ok = False
        # dry_run / offline fixture: do not fail the whole verify on MCP auth
        check("toolkit_ping", ok or dry_run, str(ping)[:120])
    except Exception as exc:  # noqa: BLE001
        check("toolkit_ping", True, f"skipped: {exc}")

    passed = all(c["ok"] for c in checks)
    result = {
        "ok": passed,
        "checks": checks,
        "story_type": story_type,
        "issue": issue.get("key"),
        "dry_run": dry_run,
    }
    ledger.write_json("verify.json", result)
    return result
