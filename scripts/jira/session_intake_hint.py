#!/usr/bin/env python3
"""SessionStart hint for Jira intake — never print fixture keys as live To Do."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLLER = ROOT / "scripts" / "jira" / "todo_poll.py"


def main() -> int:
    site = os.environ.get("JIRA_SITE", "").strip()
    email = os.environ.get("JIRA_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()
    project = os.environ.get("JIRA_PROJECT_KEY", "KAN").strip() or "KAN"

    if site and email and token and project:
        return subprocess.call([sys.executable, str(POLLER)], cwd=str(ROOT))

    print("JIRA_TODO_KEYS: (none — live board not polled)")
    print(
        "JIRA_INTAKE_HINT: Use Atlassian MCP — prefer "
        f'`project = {project} AND status = "To Do"` '
        "(statusCategory is unreliable on this Kanban board). "
        "Board: https://mnbiam.atlassian.net · project KAN. "
        "Or set JIRA_* for REST. Fixtures are not live To Do."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
