#!/usr/bin/env python3
"""Seed Meridian lab IIQ data: authoritative MNB-HR + MNB-OpenLDAP (+ optional refresh).

Uses live MCP tools only (no hardcoded Teller routing). Idempotent with --overwrite.

After MNB-HR aggregation, runs rebuild_manager_hierarchy (Link.manager → Identity.manager)
because OOTB managerCorrelationMapping alone often leaves Identity.manager unset in this lab.

Prereqs:
  - Stack up: ./tools/lab/docker/up.sh  (IIQ :8080, MCP :8766, OpenLDAP)
  - Plugin flags enabled (agentApiEnabled, taskRunEnabled + allowlist, …)

Examples:

  export MCP_API_KEY=mnb-lab-mcp-key
  export IIQ_MCP_URL=http://127.0.0.1:8766/mcp

  # Full seed (HR cubes + OpenLDAP accounts/groups)
  python3 tools/lab/scripts/seed_mnb_lab_data.py

  # OpenLDAP only (expects MNB-HR identities already present for correlation)
  python3 tools/lab/scripts/seed_mnb_lab_data.py --skip-hr

  # Dry run — print planned MCP calls
  python3 tools/lab/scripts/seed_mnb_lab_data.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
CHAT_ROOT = REPO / "tools" / "iiq-chat"
sys.path.insert(0, str(CHAT_ROOT))

from mcp_client import McpClient, McpError  # noqa: E402

# —— Defaults (override via CLI / env) ——
DEFAULT_HR_FILE = "/opt/iiq-lab-data/HRApplications.txt"
DEFAULT_LDAP_HOST = os.environ.get("MNB_LDAP_HOST", "openldap")
DEFAULT_LDAP_BIND = os.environ.get(
    "MNB_LDAP_BIND",
    "cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com",
)
DEFAULT_LDAP_PASSWORD = os.environ.get("MNB_LDAP_PASSWORD", "Provision1!")
DEFAULT_LDAP_SEARCH_DN = os.environ.get("MNB_LDAP_SEARCH_DN", "dc=meridiannb,dc=com")

PROBE_IDENTITIES = (
    "Christopher Hayes",
    "Anita Rao",
    "Helen Ross",
    "Meera Torres",
    "Priya Mehta",
)


def _log(msg: str) -> None:
    print(msg, flush=True)


def _ok(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return True
    if payload.get("ok") is False:
        return False
    err = payload.get("error")
    if isinstance(err, dict) and err.get("code"):
        return False
    return True


def _task_result_id(payload: Any) -> str | None:
    """Extract TaskResult id from various MCP/tool envelopes."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        data = payload
    for key in ("taskResultId", "task_result_id", "id"):
        val = data.get(key)
        if isinstance(val, str) and val.strip() and key != "id":
            return val.strip()
        if isinstance(val, dict) and val.get("id"):
            return str(val["id"])
    # trigger_aggregation nests under data.response
    resp = data.get("response")
    if isinstance(resp, dict):
        for key in ("taskResultId", "task_result_id", "id"):
            val = resp.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    # onboard_application nests aggregation
    agg = data.get("aggregation")
    if isinstance(agg, dict):
        return _task_result_id({"data": agg} if "taskResultId" not in agg else agg)
    return None


def _completion_status(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        return None
    for key in ("completionStatus", "status", "CompletionStatus"):
        val = data.get(key)
        if val is not None:
            return str(val)
    return None


def call(mcp: McpClient, tool: str, args: dict[str, Any], *, dry_run: bool) -> Any:
    _log(f"→ {tool}({json.dumps(args, default=str)[:240]})")
    if dry_run:
        return {"ok": True, "dry_run": True, "tool": tool, "arguments": args}
    result = mcp.call(tool, args)
    if not _ok(result):
        raise SystemExit(f"FAIL {tool}: {json.dumps(result, default=str)[:800]}")
    return result


def poll_task(
    mcp: McpClient,
    task_result_id: str | None,
    *,
    dry_run: bool,
    timeout_s: float,
    interval_s: float,
    label: str,
) -> Any:
    if dry_run or not task_result_id:
        if not task_result_id:
            _log(f"  (no taskResultId for {label} — skip poll)")
        return None
    deadline = time.time() + timeout_s
    last: Any = None
    while time.time() < deadline:
        last = call(mcp, "get_task_result", {"task_id": task_result_id}, dry_run=False)
        status = (_completion_status(last) or "").lower()
        _log(f"  poll {label}: status={status or '?'}")
        if status in {"success", "complete", "completed", "ok"}:
            return last
        if status in {"error", "failed", "failure", "terminated"}:
            raise SystemExit(f"FAIL task {label} ({task_result_id}): {json.dumps(last, default=str)[:800]}")
        time.sleep(interval_s)
    raise SystemExit(f"TIMEOUT waiting for {label} taskResultId={task_result_id}")


def seed_hr(mcp: McpClient, args: argparse.Namespace) -> None:
    _log("\n=== MNB-HR (authoritative DelimitedFile) ===")
    created = call(
        mcp,
        "create_application",
        {
            "name": "MNB-HR",
            "type": "DelimitedFile",
            "description": "Meridian authoritative HR feed (lab seed)",
            "overwrite": args.overwrite,
            "authoritative": True,
            "attributes": {
                "file": args.hr_file,
                "delimiter": ",",
                "hasHeader": True,
                # Cubes end up named by displayName in this lab; manager column uses display names.
                "identityAttribute": "name",
                "displayAttribute": "displayName",
                "managerAttribute": "manager",
                "managerCorrelationMapping": {
                    "managerAttribute": "manager",
                    "identityAttribute": "name",
                },
            },
            "justification": "seed_mnb_lab_data",
        },
        dry_run=args.dry_run,
    )
    _log(f"  create: {json.dumps(created, default=str)[:400]}")

    tested = call(
        mcp,
        "test_application_connection",
        {"application": "MNB-HR"},
        dry_run=args.dry_run,
    )
    _log(f"  test: {json.dumps(tested, default=str)[:400]}")
    if isinstance(tested, dict):
        data = tested.get("data") if isinstance(tested.get("data"), dict) else tested
        if isinstance(data, dict) and data.get("success") is False:
            raise SystemExit(f"FAIL MNB-HR test connection: {data}")

    # Pass 1 discovers schema; pass 2 populates Link attributes (needed for managers).
    for pass_no in (1, 2):
        agg = call(
            mcp,
            "trigger_aggregation",
            {
                "app_id": "MNB-HR",
                "full_or_delta": "full",
                "justification": f"seed_mnb_lab_data pass {pass_no}",
            },
            dry_run=args.dry_run,
        )
        poll_task(
            mcp,
            _task_result_id(agg),
            dry_run=args.dry_run,
            timeout_s=args.task_timeout,
            interval_s=args.poll_interval,
            label=f"MNB-HR aggregation pass {pass_no}",
        )

    # OOTB managerCorrelationMapping often does not set Identity.manager in this lab —
    # rebuild from Link.manager → Identity (displayName/name/nativeIdentity).
    rebuilt = call(
        mcp,
        "rebuild_manager_hierarchy",
        {"application": "MNB-HR", "manager_attribute": "manager"},
        dry_run=args.dry_run,
    )
    _log(f"  managers rebuild: {json.dumps(rebuilt, default=str)[:500]}")

    if not args.skip_refresh:
        refresh = call(
            mcp,
            "run_task_now",
            {
                "task_name": "Refresh Identity Cube",
                "sync": False,
                "args": {
                    "promoteAttributes": "true",
                    "refreshManagerStatus": "true",
                },
                "justification": "seed_mnb_lab_data after MNB-HR managers",
            },
            dry_run=args.dry_run,
        )
        poll_task(
            mcp,
            _task_result_id(refresh),
            dry_run=args.dry_run,
            timeout_s=args.task_timeout,
            interval_s=args.poll_interval,
            label="Refresh Identity Cube (post-HR)",
        )


def seed_ldap(mcp: McpClient, args: argparse.Namespace) -> None:
    _log("\n=== MNB-OpenLDAP ===")
    attrs = {
        "host": args.ldap_host,
        "port": str(args.ldap_port),
        "user": args.ldap_bind,
        "password": args.ldap_password,
        "searchDN": args.ldap_search_dn,
    }
    onboard = call(
        mcp,
        "onboard_application",
        {
            "name": "MNB-OpenLDAP",
            "type": "OpenLDAP - Direct",
            "description": "Meridian lab OpenLDAP directory",
            "overwrite": args.overwrite,
            "run_aggregate": True,
            "full_or_delta": "full",
            "attributes": attrs,
            "justification": "seed_mnb_lab_data",
        },
        dry_run=args.dry_run,
    )
    _log(f"  onboard: {json.dumps(onboard, default=str)[:500]}")
    poll_task(
        mcp,
        _task_result_id(onboard),
        dry_run=args.dry_run,
        timeout_s=args.task_timeout,
        interval_s=args.poll_interval,
        label="MNB-OpenLDAP aggregation",
    )

    if not args.skip_group_agg:
        gagg = call(
            mcp,
            "trigger_group_aggregation",
            {"application": "MNB-OpenLDAP"},
            dry_run=args.dry_run,
        )
        poll_task(
            mcp,
            _task_result_id(gagg),
            dry_run=args.dry_run,
            timeout_s=args.task_timeout,
            interval_s=args.poll_interval,
            label="MNB-OpenLDAP group aggregation",
        )

    if not args.skip_refresh:
        refresh = call(
            mcp,
            "run_task_now",
            {
                "task_name": "Refresh Identity Cube",
                "sync": False,
                "justification": "seed_mnb_lab_data after OpenLDAP",
            },
            dry_run=args.dry_run,
        )
        poll_task(
            mcp,
            _task_result_id(refresh),
            dry_run=args.dry_run,
            timeout_s=args.task_timeout,
            interval_s=args.poll_interval,
            label="Refresh Identity Cube (post-LDAP)",
        )


def verify(mcp: McpClient, *, dry_run: bool) -> None:
    _log("\n=== Verify ===")
    digest = call(mcp, "get_executive_digest", {}, dry_run=dry_run)
    _log(f"  digest: {json.dumps(digest, default=str)[:500]}")

    for q in PROBE_IDENTITIES:
        hits = call(
            mcp,
            "search_identities",
            {"query": q, "count": 5},
            dry_run=dry_run,
        )
        n = 0
        if isinstance(hits, dict):
            data = hits.get("data") if isinstance(hits.get("data"), dict) else hits
            items = data.get("items") or data.get("Resources") or []
            if isinstance(items, list):
                n = len(items)
        _log(f"  search_identities({q!r}) → {n} hit(s)")

    hier = call(
        mcp,
        "get_manager_hierarchy",
        {"name": "Christopher Hayes"},
        dry_run=dry_run,
    )
    reports = 0
    if isinstance(hier, dict):
        data = hier.get("data") if isinstance(hier.get("data"), dict) else hier
        reports = len(data.get("directReports") or []) if isinstance(data, dict) else 0
    _log(f"  Christopher Hayes directReports → {reports}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="Print planned MCP calls only")
    p.add_argument("--overwrite", action="store_true", default=True, help="Overwrite apps if present (default)")
    p.add_argument("--no-overwrite", action="store_false", dest="overwrite")
    p.add_argument("--skip-hr", action="store_true", help="Skip MNB-HR create/aggregate")
    p.add_argument("--skip-ldap", action="store_true", help="Skip MNB-OpenLDAP onboard")
    p.add_argument("--skip-group-agg", action="store_true", help="Skip Account Group Aggregation")
    p.add_argument("--skip-refresh", action="store_true", help="Skip Refresh Identity Cube")
    p.add_argument("--skip-verify", action="store_true")
    p.add_argument("--hr-file", default=DEFAULT_HR_FILE, help="Path inside IIQ container")
    p.add_argument("--ldap-host", default=DEFAULT_LDAP_HOST)
    p.add_argument("--ldap-port", type=int, default=int(os.environ.get("MNB_LDAP_PORT", "389")))
    p.add_argument("--ldap-bind", default=DEFAULT_LDAP_BIND)
    p.add_argument("--ldap-password", default=DEFAULT_LDAP_PASSWORD)
    p.add_argument("--ldap-search-dn", default=DEFAULT_LDAP_SEARCH_DN)
    p.add_argument("--task-timeout", type=float, default=300.0)
    p.add_argument("--poll-interval", type=float, default=5.0)
    p.add_argument(
        "--mcp-url",
        default=os.environ.get("IIQ_MCP_URL", "http://127.0.0.1:8766/mcp"),
    )
    p.add_argument(
        "--mcp-api-key",
        default=os.environ.get("MCP_API_KEY") or os.environ.get("IIQ_MCP_API_KEY") or "mnb-lab-mcp-key",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.skip_hr and args.skip_ldap and args.skip_verify:
        _log("Nothing to do (--skip-hr, --skip-ldap, and --skip-verify)")
        return 0

    mcp = McpClient(url=args.mcp_url, api_key=args.mcp_api_key, timeout=120.0)
    try:
        health = mcp.healthz()
        _log(f"MCP health: {health}")
    except Exception as exc:  # noqa: BLE001
        _log(f"WARN: MCP healthz failed: {exc}")

    if not args.dry_run:
        try:
            mcp.init()
        except McpError as exc:
            _log(f"FAIL MCP init: {exc}")
            return 1

    try:
        if not args.skip_hr:
            seed_hr(mcp, args)
        if not args.skip_ldap:
            seed_ldap(mcp, args)
        if not args.skip_verify:
            verify(mcp, dry_run=args.dry_run)
    except McpError as exc:
        _log(f"FAIL MCP: {exc}")
        return 1

    _log("\nDone. Try Teller: “Who is Anita Rao?” / “Show executive digest”.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
