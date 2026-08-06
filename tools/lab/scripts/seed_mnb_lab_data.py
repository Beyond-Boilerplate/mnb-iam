#!/usr/bin/env python3
"""Seed Meridian lab IIQ data: MNB-HR + MNB-OpenLDAP (+ optional refresh).

Core Path default: authoritative MNB-HR aggregation creates workforce cubes, then OpenLDAP
accounts correlate onto them.

Enterprise Sandbox (--definitions-only): import app definitions only — MNB-HR is
non-authoritative, no aggregation, no cubes. Learners create cubes from MNB-Workday in
Lesson 207.

Uses live MCP tools only (no hardcoded Teller routing). Idempotent with --overwrite.

Prefers durable XML under config/Application and config/TaskDefinition (UI exports)
via import_sailpoint_object (scrub_ids). Falls back to create/onboard when XML is missing.

After MNB-HR aggregation (Core Path), runs rebuild_manager_hierarchy (Link.manager →
Identity.manager) because OOTB managerCorrelationMapping alone often leaves
Identity.manager unset in this lab.

Prereqs:
  - Stack up: ./tools/lab/docker/up.sh  (IIQ :8080, MCP :8766, OpenLDAP)
  - Plugin flags enabled (agentApiEnabled, taskRunEnabled + allowlist, …)

Examples:

  export MCP_API_KEY=mnb-lab-mcp-key
  export IIQ_MCP_URL=http://127.0.0.1:8766/mcp

  # Full seed (HR cubes + OpenLDAP accounts/groups)
  python3 tools/lab/scripts/seed_mnb_lab_data.py

  # Overlay without wipe
  python3 tools/lab/scripts/seed_mnb_lab_data.py --keep-existing

  # Enterprise definitions only (no workforce cubes)
  python3 tools/lab/scripts/seed_mnb_lab_data.py --definitions-only --keep-existing

  # OpenLDAP only (expects identities already present for correlation)
  python3 tools/lab/scripts/seed_mnb_lab_data.py --skip-hr --keep-existing

  # Dry run — print planned MCP calls
  python3 tools/lab/scripts/seed_mnb_lab_data.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

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
DEFAULT_LDAP_GROUP_SEARCH_DN = os.environ.get(
    "MNB_LDAP_GROUP_SEARCH_DN", "ou=groups,dc=meridiannb,dc=com"
)

CONFIG_HR_APP = REPO / "config" / "Application" / "MNB-Application-HR.xml"
CONFIG_LDAP_APP = REPO / "config" / "Application" / "MNB-Application-OpenLDAP.xml"
CONFIG_TASKS = (
    REPO / "config" / "TaskDefinition" / "MNB-TaskDefinition-Acct-Aggregation.xml",
    REPO / "config" / "TaskDefinition" / "MNB-TaskDefinition-Daily-Aggr.xml",
    REPO
    / "config"
    / "TaskDefinition"
    / "MNB-TaskDefinition-OpenLDAP-Group-Aggregation.xml",
)

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


def _read_xml(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def import_xml(
    mcp: McpClient,
    path: Path,
    *,
    dry_run: bool,
    justification: str,
    xml_transform: Callable[[str], str] | None = None,
) -> Any:
    if dry_run:
        xml = f"<!-- dry-run {path} -->"
    else:
        xml = _read_xml(path)
        if xml_transform is not None:
            xml = xml_transform(xml)
    return call(
        mcp,
        "import_sailpoint_object",
        {
            "xml": xml,
            "scrub_ids": True,
            "justification": justification,
        },
        dry_run=dry_run,
    )


def _hr_non_authoritative_xml(xml: str) -> str:
    """Enterprise seed: keep MNB-HR as a CSV contrast app, never cube source."""
    return xml.replace('authoritative="true"', 'authoritative="false"', 1)


def import_task_definitions(mcp: McpClient, *, dry_run: bool) -> None:
    _log("\n=== TaskDefinitions (durable config/) ===")
    for path in CONFIG_TASKS:
        if not path.is_file():
            _log(f"  skip missing {path.relative_to(REPO)}")
            continue
        imported = import_xml(
            mcp,
            path,
            dry_run=dry_run,
            justification=f"seed_mnb_lab_data import {path.name}",
        )
        _log(f"  import {path.name}: {json.dumps(imported, default=str)[:300]}")


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
        last = call(
            mcp,
            "get_task_result",
            {"task_result_id": task_result_id},
            dry_run=False,
        )
        status = (_completion_status(last) or "").lower()
        _log(f"  poll {label}: status={status or '?'}")
        if status in {"success", "complete", "completed", "ok"}:
            return last
        if status in {"error", "failed", "failure", "terminated"}:
            raise SystemExit(f"FAIL task {label} ({task_result_id}): {json.dumps(last, default=str)[:800]}")
        time.sleep(interval_s)
    raise SystemExit(f"TIMEOUT waiting for {label} taskResultId={task_result_id}")


def seed_hr(mcp: McpClient, args: argparse.Namespace) -> None:
    definitions_only = bool(getattr(args, "definitions_only", False))
    hr_non_auth = bool(getattr(args, "hr_non_authoritative", False)) or definitions_only
    mode = "definitions only (non-authoritative)" if hr_non_auth else "authoritative DelimitedFile"
    _log(f"\n=== MNB-HR ({mode}) ===")

    # Prefer durable XML when present. On scrub_ids/Hibernate races after wipe,
    # fall back to create_application (authoritative=false for enterprise defs-only).
    use_xml = CONFIG_HR_APP.is_file() and not args.force_wizard
    created_via_wizard = False

    if use_xml:
        _log(f"  importing {CONFIG_HR_APP.relative_to(REPO)}")
        try:
            imported = import_xml(
                mcp,
                CONFIG_HR_APP,
                dry_run=args.dry_run,
                justification="seed_mnb_lab_data import MNB-Application-HR.xml",
                xml_transform=_hr_non_authoritative_xml if hr_non_auth else None,
            )
            _log(f"  import: {json.dumps(imported, default=str)[:400]}")
            call(
                mcp,
                "update_application_config",
                {
                    "app_id": "MNB-HR",
                    "config_patch": {
                        "attributes": {
                            "file": args.hr_file,
                            "delimiter": ",",
                            "hasHeader": True,
                        }
                    },
                    "justification": "seed_mnb_lab_data ensure HR file path",
                },
                dry_run=args.dry_run,
            )
        except SystemExit as exc:
            if not hr_non_auth:
                raise
            _log(f"  WARN XML import failed ({exc}); falling back to create_application")
            created_via_wizard = True
    else:
        created_via_wizard = True

    if created_via_wizard:
        created = call(
            mcp,
            "create_application",
            {
                "name": "MNB-HR",
                "type": "DelimitedFile",
                "description": (
                    "Meridian HR CSV (lab; non-authoritative under enterprise seed)"
                    if hr_non_auth
                    else "Meridian authoritative HR feed (lab seed)"
                ),
                "overwrite": args.overwrite,
                "authoritative": not hr_non_auth,
                "attributes": {
                    "file": args.hr_file,
                    "delimiter": ",",
                    "hasHeader": True,
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

    if definitions_only:
        _log("  skip aggregation/refresh (definitions-only — cubes come from MNB-Workday in Lesson 207)")
        return

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
    definitions_only = bool(getattr(args, "definitions_only", False))
    _log("\n=== MNB-OpenLDAP" + (" (definitions only)" if definitions_only else "") + " ===")
    if CONFIG_LDAP_APP.is_file() and not args.force_wizard:
        _log(f"  importing {CONFIG_LDAP_APP.relative_to(REPO)}")
        imported = import_xml(
            mcp,
            CONFIG_LDAP_APP,
            dry_run=args.dry_run,
            justification="seed_mnb_lab_data import MNB-Application-OpenLDAP.xml",
        )
        _log(f"  import: {json.dumps(imported, default=str)[:400]}")
        # Overlay live bind / host (XML has lab defaults; env can override).
        call(
            mcp,
            "update_application_config",
            {
                "app_id": "MNB-OpenLDAP",
                "config_patch": {
                    "attributes": {
                        "host": args.ldap_host,
                        "port": str(args.ldap_port),
                        "user": args.ldap_bind,
                        "password": args.ldap_password,
                        "searchDNs": [
                            {
                                "searchDN": args.ldap_people_search_dn,
                                "searchScope": "SUBTREE",
                            }
                        ],
                        "group.searchDNs": [
                            {
                                "searchDN": args.ldap_group_search_dn,
                                "searchScope": "SUBTREE",
                                "objectType": "group",
                                "iterateSearchFilter": "(objectClass=groupOfUniqueNames)",
                            }
                        ],
                    }
                },
                "justification": "seed_mnb_lab_data ensure LDAP bind + group.searchDNs",
            },
            dry_run=args.dry_run,
        )
        tested = call(
            mcp,
            "test_application_connection",
            {"application": "MNB-OpenLDAP"},
            dry_run=args.dry_run,
        )
        _log(f"  test: {json.dumps(tested, default=str)[:400]}")
        if definitions_only:
            _log("  skip account/group aggregation (definitions-only — aggregate in Lesson 204 after Workday cubes)")
            return
        agg = call(
            mcp,
            "trigger_aggregation",
            {
                "app_id": "MNB-OpenLDAP",
                "full_or_delta": "full",
                "justification": "seed_mnb_lab_data after XML import",
            },
            dry_run=args.dry_run,
        )
        poll_task(
            mcp,
            _task_result_id(agg),
            dry_run=args.dry_run,
            timeout_s=args.task_timeout,
            interval_s=args.poll_interval,
            label="MNB-OpenLDAP aggregation",
        )
    else:
        attrs = {
            "host": args.ldap_host,
            "port": str(args.ldap_port),
            "user": args.ldap_bind,
            "password": args.ldap_password,
            "searchDNs": [
                {
                    "searchDN": args.ldap_people_search_dn,
                    "searchScope": "SUBTREE",
                }
            ],
            "group.searchDNs": [
                {
                    "searchDN": args.ldap_group_search_dn,
                    "searchScope": "SUBTREE",
                    "objectType": "group",
                    "iterateSearchFilter": "(objectClass=groupOfUniqueNames)",
                }
            ],
        }
        onboard = call(
            mcp,
            "onboard_application",
            {
                "name": "MNB-OpenLDAP",
                "type": "OpenLDAP - Direct",
                "description": "Meridian lab OpenLDAP directory",
                "overwrite": args.overwrite,
                "run_aggregate": not definitions_only,
                "full_or_delta": "full",
                "attributes": attrs,
                "justification": "seed_mnb_lab_data",
            },
            dry_run=args.dry_run,
        )
        _log(f"  onboard: {json.dumps(onboard, default=str)[:500]}")
        if definitions_only:
            _log("  skip aggregation poll (definitions-only)")
            return
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


def run_backup_and_reset(*, mcp_url: str, mcp_api_key: str, dry_run: bool) -> None:
    """Export live MNB-* via MCP, then wipe so seed starts clean."""
    if dry_run:
        _log("DRY-RUN would: backup_and_reset_lab.py (extract → wipe)")
        return
    if os.environ.get("MNB_LAB_RESET_DONE", "").lower() in ("1", "true", "yes"):
        _log("Skip backup/wipe (MNB_LAB_RESET_DONE already set)")
        return
    script = REPO / "tools" / "lab" / "scripts" / "backup_and_reset_lab.py"
    cmd = [
        sys.executable,
        str(script),
        "--mcp-url",
        mcp_url,
        "--mcp-api-key",
        mcp_api_key,
    ]
    _log("==> Backup live Meridian objects, then wipe leftovers before seed")
    env = os.environ.copy()
    env["IIQ_MCP_URL"] = mcp_url
    env["MCP_API_KEY"] = mcp_api_key
    proc = subprocess.run(cmd, cwd=str(REPO), env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"backup/wipe failed (exit {proc.returncode})")
    os.environ["MNB_LAB_RESET_DONE"] = "1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="Print planned MCP calls only")
    p.add_argument("--overwrite", action="store_true", default=True, help="Overwrite apps if present (default)")
    p.add_argument("--no-overwrite", action="store_false", dest="overwrite")
    p.add_argument(
        "--keep-existing",
        action="store_true",
        help="Skip backup+wipe; seed/overlay on current IIQ objects",
    )
    p.add_argument("--skip-hr", action="store_true", help="Skip MNB-HR create/aggregate")
    p.add_argument("--skip-ldap", action="store_true", help="Skip MNB-OpenLDAP onboard")
    p.add_argument("--skip-group-agg", action="store_true", help="Skip Account Group Aggregation")
    p.add_argument("--skip-refresh", action="store_true", help="Skip Refresh Identity Cube")
    p.add_argument("--skip-verify", action="store_true")
    p.add_argument(
        "--definitions-only",
        action="store_true",
        help=(
            "Import app definitions + TaskDefinitions only — no account aggregation, "
            "no Identity Refresh, no workforce cubes (Enterprise Sandbox Path)"
        ),
    )
    p.add_argument(
        "--hr-non-authoritative",
        action="store_true",
        help="Import/create MNB-HR with authoritative=false (implied by --definitions-only)",
    )
    p.add_argument(
        "--skip-tasks",
        action="store_true",
        help="Skip importing TaskDefinitions from config/",
    )
    p.add_argument(
        "--force-wizard",
        action="store_true",
        help="Ignore config/Application XML; use create/onboard wizard path",
    )
    p.add_argument("--hr-file", default=DEFAULT_HR_FILE, help="Path inside IIQ container")
    p.add_argument("--ldap-host", default=DEFAULT_LDAP_HOST)
    p.add_argument("--ldap-port", type=int, default=int(os.environ.get("MNB_LDAP_PORT", "389")))
    p.add_argument("--ldap-bind", default=DEFAULT_LDAP_BIND)
    p.add_argument("--ldap-password", default=DEFAULT_LDAP_PASSWORD)
    p.add_argument("--ldap-search-dn", default=DEFAULT_LDAP_SEARCH_DN)
    p.add_argument(
        "--ldap-people-search-dn",
        default=os.environ.get("MNB_LDAP_PEOPLE_SEARCH_DN", "ou=people,dc=meridiannb,dc=com"),
    )
    p.add_argument(
        "--ldap-group-search-dn",
        default=DEFAULT_LDAP_GROUP_SEARCH_DN,
    )
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

    keep_existing = args.keep_existing or os.environ.get(
        "MNB_LAB_KEEP_EXISTING", ""
    ).lower() in ("1", "true", "yes")

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

    if not keep_existing:
        try:
            run_backup_and_reset(
                mcp_url=args.mcp_url,
                mcp_api_key=args.mcp_api_key,
                dry_run=args.dry_run,
            )
        except RuntimeError as exc:
            _log(f"FAIL {exc}")
            return 1
    else:
        _log("Keeping existing IIQ objects (--keep-existing)")

    try:
        if not args.skip_hr:
            seed_hr(mcp, args)
        if not args.skip_ldap:
            seed_ldap(mcp, args)
        if not args.skip_tasks:
            import_task_definitions(mcp, dry_run=args.dry_run)
        if args.definitions_only:
            _log(
                "\nDefinitions-only seed complete — Identity Warehouse should only have "
                "spadmin until Lesson 207 aggregates MNB-Workday."
            )
        elif not args.skip_verify:
            verify(mcp, dry_run=args.dry_run)
            if not args.dry_run and not args.skip_ldap:
                ents = call(
                    mcp,
                    "list_managed_entitlements",
                    {"application": "MNB-OpenLDAP", "limit": 50},
                    dry_run=False,
                )
                data = ents.get("data") if isinstance(ents, dict) else {}
                items = (data or {}).get("items") or []
                n = (data or {}).get("returned") or len(items)
                _log(f"  MNB-OpenLDAP managed group entitlements → {n}")
                if isinstance(items, list) and items:
                    sample = [i.get("displayName") or i.get("value") for i in items[:5]]
                    _log(f"    sample: {sample}")
                if int(n) < 8:
                    raise SystemExit(
                        f"FAIL expected >=8 OpenLDAP group entitlements, got {n}"
                    )
    except McpError as exc:
        _log(f"FAIL MCP: {exc}")
        return 1

    _log("\nDone. Try Teller: “Who is Anita Rao?” / “Show executive digest”.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
