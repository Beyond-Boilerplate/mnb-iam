"""Control plane: poll → feasibility → claim → implement → verify → In Review."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from .config import jira_creds, load_config, mcp_api_key, mcp_url, resolve_path
from .feasibility import run_feasibility
from .handoff import build_evidence, run_handoff
from .implement import run_implement
from .jira_client import JiraClient, JiraError, issue_plain_text
from .lease import LeaseStore
from .ledger import RunLedger, delivery_run_dir, new_run_id
from .llm.provider import LlmProvider
from .mcp_wrap import WrappedMcp
from .verify import run_verify


def _worker_id() -> str:
    return f"auto-story@{socket.gethostname()}"


def load_fixture_issue(fixture_dir: Path, key: str) -> dict[str, Any]:
    path = fixture_dir / f"{key}.json"
    if not path.is_file():
        # try any json containing key
        for p in sorted(fixture_dir.glob("*.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            if str(data.get("key") or data.get("issue_key") or "") == key:
                return _normalize_fixture(data)
        raise FileNotFoundError(f"No fixture for {key} under {fixture_dir}")
    return _normalize_fixture(json.loads(path.read_text(encoding="utf-8")))


def _normalize_fixture(data: dict[str, Any]) -> dict[str, Any]:
    if "fields" in data:
        return issue_plain_text(data)
    return {
        "key": data.get("key") or data.get("issue_key"),
        "summary": data.get("summary") or data.get("title"),
        "description": data.get("description") or data.get("body") or "",
        "labels": data.get("labels") or [],
        "status": data.get("status") or "To Do",
        "assignee": data.get("assignee"),
        "issuetype": data.get("issuetype") or "Story",
    }


def poll_ready(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    site, email, token = jira_creds(cfg)
    client = JiraClient(site, email, token)
    jql = (cfg.get("jira") or {}).get("ready_jql") or ""
    issues = client.search(jql)
    return [issue_plain_text(i) for i in issues]


def run_story(
    *,
    issue_key: str,
    cfg: dict[str, Any] | None = None,
    live: bool = False,
    tail: bool = False,
    fixture_dir: Path | None = None,
    skip_jira: bool = False,
    use_llm: bool = True,
) -> dict[str, Any]:
    cfg = cfg or load_config()
    repo = Path(cfg["_repo_root"])
    agent = cfg.get("agent") or {}
    dry_run = not live
    if live:
        # explicit live overrides config dry_run
        dry_run = False
    elif agent.get("dry_run") is False and live is False:
        # config says dry_run false but CLI default is dry — keep CLI dry unless --live
        dry_run = True

    verbose = bool(agent.get("verbose_think"))
    denylist = list(cfg.get("tool_denylist") or [])

    run_id = new_run_id()
    run_dir = delivery_run_dir(repo, issue_key, run_id)
    ledger = RunLedger(run_dir, tail=tail)
    ledger.emit(
        "RUN_START",
        summary=f"{issue_key} dry_run={dry_run}",
        issue=issue_key,
        run_id=run_id,
        dry_run=dry_run,
        worker=_worker_id(),
    )

    # Load issue
    if fixture_dir:
        issue = load_fixture_issue(fixture_dir, issue_key)
        skip_jira = True
    else:
        site, email, token = jira_creds(cfg)
        if not (site and email and token):
            raise RuntimeError("Jira credentials missing (or pass --fixture)")
        jira = JiraClient(site, email, token)
        issue = issue_plain_text(jira.get_issue(issue_key))

    # MCP + LLM
    mcp = WrappedMcp(
        url=mcp_url(cfg),
        api_key=mcp_api_key(cfg),
        dry_run=dry_run,
        denylist=denylist,
        read_only=False,
        on_call=lambda name, args: ledger.emit(
            "MCP_CALL", tool=name, arguments=args, dry_run=dry_run, summary=f"call {name}"
        ),
        on_result=lambda name, args, result, elapsed, ok: ledger.emit(
            "MCP_RESULT",
            tool=name,
            ok=ok,
            elapsed_ms=int(elapsed * 1000),
            summary=str(result)[:200],
        ),
    )

    provider: LlmProvider | None = None
    if use_llm:
        try:
            provider = LlmProvider.from_config(cfg)
        except Exception as exc:  # noqa: BLE001
            ledger.emit("STATUS", message=f"LLM provider init: {exc}", summary=str(exc))
    else:
        ledger.emit("STATUS", message="LLM disabled (--no-llm)", summary="no-llm")

    # Feasibility
    decision = run_feasibility(
        provider=provider,
        mcp=mcp,
        ledger=ledger,
        issue=issue,
        cfg=cfg,
        use_llm=use_llm,
    )

    if decision.get("mode") != "MCP_E2E":
        if not skip_jira and not dry_run:
            try:
                site, email, token = jira_creds(cfg)
                jira = JiraClient(site, email, token)
                label = (cfg.get("jira") or {}).get("label_blocked") or "blocked-needs-human"
                jira.add_label(issue_key, label)
                jira.add_comment(
                    issue_key,
                    f"[auto-story] Not MCP_E2E ({decision.get('mode')}/{decision.get('story_type')}). "
                    f"Reasons: {decision.get('reasons')}",
                )
                ledger.emit("JIRA", summary=f"labeled {label}", action="escalate")
            except JiraError as exc:
                ledger.emit("ERROR", message=str(exc), summary=f"jira escalate: {exc}")
        ledger.emit("HANDOFF", summary="skipped — not MCP_E2E", ready_for_review=False)
        return {"ok": False, "decision": decision, "run_dir": str(run_dir), "skipped": True}

    # Claim lease
    lease_cfg = cfg.get("lease") or {}
    lease_db = resolve_path(cfg, lease_cfg.get("db_path") or ".ai-delivery/_state/auto_story_leases.sqlite")
    leases = LeaseStore(
        lease_db,
        ttl_seconds=int(lease_cfg.get("ttl_seconds") or 3600),
        worker_id=_worker_id(),
    )
    if not leases.try_claim(issue_key):
        ledger.emit("ERROR", summary="lease held by another worker", message="claim failed")
        return {"ok": False, "error": "lease_conflict", "run_dir": str(run_dir)}
    leases.mark_running(issue_key)

    jira_client: JiraClient | None = None
    if not skip_jira:
        site, email, token = jira_creds(cfg)
        jira_client = JiraClient(site, email, token)

    # Assign + In Progress (live only)
    if jira_client and not dry_run:
        try:
            jira_client.assign(issue_key)
            ledger.emit("JIRA", summary="assigned bot", action="assign")
            ip = (cfg.get("jira") or {}).get("transition_in_progress") or "In Progress"
            jira_client.transition_to(issue_key, ip)
            ledger.emit("JIRA", summary=f"→ {ip}", action="transition", to=ip)
        except JiraError as exc:
            ledger.emit("ERROR", message=str(exc), summary=f"jira start: {exc}")
            leases.release(issue_key, state="error")
            return {"ok": False, "error": str(exc), "run_dir": str(run_dir)}
    elif dry_run:
        ledger.emit("JIRA", summary="dry_run skip assign/In Progress", action="skip", dry_run=True)

    # Implement
    if not provider or not provider.api_key:
        # Heuristic-only implement: optional toolkit ping + plan
        ledger.emit("STATUS", message="No LLM key — minimal dry implement")
        steps: list[dict[str, Any]] = []
        try:
            mcp.call("toolkit_ping", {})
            steps.append({"tool": "toolkit_ping", "ok": True, "arguments": {}})
        except Exception as exc:  # noqa: BLE001
            ledger.emit("STATUS", message=f"MCP ping skipped: {exc}", summary=str(exc)[:160])
            steps.append({"tool": "toolkit_ping", "ok": False, "arguments": {}, "result": {"error": str(exc)}})
        implement = {
            "reply": (
                f"Dry implement without LLM for {issue_key} type={decision.get('story_type')}. "
                f"Feasibility={decision.get('mode')}. MCP may be unavailable in offline fixture runs."
            ),
            "steps": steps,
            "model": None,
        }
        ledger.write_text(
            "plan.md",
            f"# Plan {issue_key}\n\nNo LLM key; feasibility decided as "
            f"{decision.get('mode')}/{decision.get('story_type')}.\n",
        )
        ledger.emit("PLAN", summary="minimal plan (no LLM)")
    else:
        try:
            implement = run_implement(
                provider=provider,
                mcp=mcp,
                ledger=ledger,
                issue=issue,
                decision=decision,
                cfg=cfg,
            )
        except Exception as exc:  # noqa: BLE001
            ledger.emit("ERROR", message=str(exc), summary=f"implement failed: {exc}")
            implement = {
                "reply": f"Implement failed: {exc}",
                "steps": [],
                "model": getattr(provider, "model", None),
            }

    verify = run_verify(
        mcp=mcp,
        ledger=ledger,
        issue=issue,
        decision=decision,
        implement=implement,
        dry_run=dry_run,
    )
    evidence = build_evidence(
        ledger=ledger,
        issue=issue,
        decision=decision,
        implement=implement,
        verify=verify,
        dry_run=dry_run,
    )
    handoff = run_handoff(
        provider=provider,
        mcp=mcp,
        ledger=ledger,
        issue=issue,
        decision=decision,
        implement=implement,
        verify=verify,
        evidence=evidence,
        cfg=cfg,
    )

    # In Review
    if jira_client and not dry_run and handoff.get("ready_for_review"):
        try:
            comment = str(handoff.get("comment") or handoff.get("summary") or "")
            jira_client.add_comment(issue_key, comment)
            ir = (cfg.get("jira") or {}).get("transition_in_review") or "In Review"
            jira_client.transition_to(issue_key, ir)
            ledger.emit("JIRA", summary=f"→ {ir}", action="transition", to=ir)
        except JiraError as exc:
            ledger.emit("ERROR", message=str(exc), summary=f"jira handoff: {exc}")
            leases.release(issue_key, state="error")
            return {
                "ok": False,
                "error": str(exc),
                "run_dir": str(run_dir),
                "decision": decision,
                "verify": verify,
            }
    elif dry_run:
        ledger.emit(
            "JIRA",
            summary="dry_run skip In Review comment/transition",
            action="skip",
            dry_run=True,
        )

    leases.release(issue_key, state="done" if verify.get("ok") else "verify_failed")
    return {
        "ok": bool(verify.get("ok")),
        "run_dir": str(run_dir),
        "decision": decision,
        "verify": verify,
        "evidence": evidence,
        "handoff": handoff,
        "dry_run": dry_run,
    }
