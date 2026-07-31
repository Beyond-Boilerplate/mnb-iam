#!/usr/bin/env python3
"""Poll Jira Cloud for issues in To Do; print issue keys.

Designed for Claude Code SessionStart hooks (MCP may not be connected yet).
Fail-open: exit 0 even when Jira is unreachable (prints JIRA_POLL_SKIPPED).

Env:
  JIRA_SITE          e.g. https://mnbiam.atlassian.net
  JIRA_EMAIL         Atlassian account email
  JIRA_API_TOKEN     API token
  JIRA_PROJECT_KEY   e.g. KAN (mnbiam board)
  JIRA_TODO_STATUS   default "To Do"

Usage:
  python3 scripts/jira/todo_poll.py              # new keys only (requires JIRA_*)
  python3 scripts/jira/todo_poll.py --all
  python3 scripts/jira/todo_poll.py --fixture jira-stories/fixtures   # offline ONLY
  python3 scripts/jira/todo_poll.py --mark-seen

Fixtures are NEVER used unless --fixture is passed. Missing env → JIRA_POLL_SKIPPED
(use Atlassian MCP against project KAN instead).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_DB = REPO_ROOT / ".ai-delivery" / "_state" / "todo_seen.sqlite"
DEFAULT_FIXTURE_DIR = REPO_ROOT / "jira-stories" / "fixtures"


def _die_open(msg: str) -> int:
    print(f"JIRA_POLL_SKIPPED: {msg}", file=sys.stderr)
    print("JIRA_POLL_SKIPPED")
    return 0


def connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen (
            issue_key TEXT PRIMARY KEY,
            first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_seen_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    return conn


def load_seen(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT issue_key FROM seen").fetchall()
    return {r[0] for r in rows}


def mark_seen(conn: sqlite3.Connection, keys: list[str]) -> None:
    for key in keys:
        conn.execute(
            """
            INSERT INTO seen (issue_key) VALUES (?)
            ON CONFLICT(issue_key) DO UPDATE SET last_seen_at = datetime('now')
            """,
            (key,),
        )
    conn.commit()


def jira_search(site: str, email: str, token: str, project: str, status: str) -> list[str]:
    # Prefer full JQL override (Kanban-friendly statusCategory)
    jql = os.environ.get("JIRA_TODO_JQL", "").strip()
    if not jql:
        # statusCategory is more reliable than exact status name across board configs
        use_category = os.environ.get("JIRA_TODO_USE_CATEGORY", "1").strip() not in ("0", "false", "no")
        if use_category:
            jql = f'project = "{project}" AND statusCategory = "To Do" ORDER BY created ASC'
        else:
            jql = f'project = "{project}" AND status = "{status}" ORDER BY created ASC'
    params = urllib.parse.urlencode(
        {
            "jql": jql,
            "fields": "key",
            "maxResults": "100",
        }
    )
    url = f"{site.rstrip('/')}/rest/api/3/search?{params}"
    req = urllib.request.Request(url, method="GET")
    import base64

    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload: dict[str, Any] = json.loads(resp.read().decode())
    issues = payload.get("issues") or []
    return [str(i.get("key")) for i in issues if i.get("key")]


def load_fixture_keys(fixture_path: Path, status: str) -> list[str]:
    paths: list[Path]
    if fixture_path.is_dir():
        paths = sorted(fixture_path.glob("*.json"))
    elif fixture_path.is_file():
        paths = [fixture_path]
    else:
        raise FileNotFoundError(f"fixture not found: {fixture_path}")

    keys: list[str] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Support single issue or { "issues": [ ... ] }
        items = data.get("issues") if isinstance(data, dict) and "issues" in data else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            key = item.get("key") or item.get("issue_key")
            fields = item.get("fields") or {}
            st = (
                fields.get("status", {}).get("name")
                if isinstance(fields.get("status"), dict)
                else fields.get("status") or item.get("status")
            )
            if not key:
                continue
            if st and str(st) != status:
                continue
            keys.append(str(key))
    # stable unique order
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Poll Jira To Do and print issue keys")
    parser.add_argument("--all", action="store_true", help="Print all To Do keys (not only new)")
    parser.add_argument(
        "--fixture",
        nargs="?",
        const=str(DEFAULT_FIXTURE_DIR),
        default=None,
        help="Load keys from fixture JSON instead of live Jira",
    )
    parser.add_argument(
        "--state-db",
        default=str(DEFAULT_STATE_DB),
        help="SQLite path for seen keys",
    )
    parser.add_argument(
        "--status",
        default=os.environ.get("JIRA_TODO_STATUS", "To Do"),
        help='Jira status name to poll (default "To Do")',
    )
    parser.add_argument(
        "--mark-seen",
        action="store_true",
        help="Persist keys into seen DB (default when printing new keys)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not update seen DB",
    )
    args = parser.parse_args()

    try:
        if args.fixture is not None:
            keys = load_fixture_keys(Path(args.fixture), args.status)
        else:
            site = os.environ.get("JIRA_SITE", "").strip()
            email = os.environ.get("JIRA_EMAIL", "").strip()
            token = os.environ.get("JIRA_API_TOKEN", "").strip()
            project = os.environ.get("JIRA_PROJECT_KEY", "").strip()
            if not (site and email and token and project):
                return _die_open(
                    "missing JIRA_* env (site/email/token/project). "
                    "Prefer Atlassian MCP for project KAN, or pass --fixture explicitly. "
                    "Do not treat local MNB-* fixtures as the live board."
                )
            else:
                try:
                    keys = jira_search(site, email, token, project, args.status)
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
                    return _die_open(str(exc))
    except Exception as exc:  # noqa: BLE001 — fail-open for hooks
        return _die_open(str(exc))

    conn = connect_db(Path(args.state_db))
    seen = load_seen(conn)
    if args.all:
        out = keys
    else:
        out = [k for k in keys if k not in seen]

    if out:
        print("JIRA_TODO_KEYS:")
        for k in out:
            print(k)
    else:
        print("JIRA_TODO_KEYS: (none new)" if not args.all else "JIRA_TODO_KEYS: (empty)")

    # Default: SessionStart marks whatever we printed as new so keys aren't re-announced.
    # --all lists without marking unless --mark-seen. --dry-run never marks.
    if not args.dry_run:
        if args.mark_seen and keys:
            mark_seen(conn, keys)
        elif not args.all and out:
            mark_seen(conn, out)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
