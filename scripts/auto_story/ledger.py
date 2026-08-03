"""Append-only run ledger + optional colored tail."""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TextIO

EVENT_TYPES = frozenset(
    {
        "RUN_START",
        "THINK",
        "DECIDE",
        "PLAN",
        "MCP_CALL",
        "MCP_RESULT",
        "JIRA",
        "VERIFY",
        "HANDOFF",
        "ERROR",
        "STATUS",
    }
)

_COLORS = {
    "THINK": "\033[36m",
    "DECIDE": "\033[35m",
    "PLAN": "\033[34m",
    "MCP_CALL": "\033[33m",
    "MCP_RESULT": "\033[32m",
    "JIRA": "\033[35m",
    "VERIFY": "\033[36m",
    "HANDOFF": "\033[32m",
    "ERROR": "\033[31m",
    "STATUS": "\033[90m",
    "RUN_START": "\033[1m",
}
_RESET = "\033[0m"


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]


class RunLedger:
    def __init__(
        self,
        run_dir: Path,
        *,
        tail: bool = False,
        stream: TextIO | None = None,
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.run_dir / "events.jsonl"
        self.mcp_audit_path = self.run_dir / "mcp-audit.jsonl"
        self.tail = tail
        self.stream = stream or sys.stderr
        self.on_event = on_event
        self._use_color = hasattr(self.stream, "isatty") and self.stream.isatty()

    def emit(self, event_type: str, **payload: Any) -> dict[str, Any]:
        et = event_type.upper()
        if et not in EVENT_TYPES:
            et = "STATUS"
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": et,
            **payload,
        }
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        if et in {"MCP_CALL", "MCP_RESULT"}:
            with self.mcp_audit_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, default=str) + "\n")
        if self.tail:
            self._print(row)
        if self.on_event:
            self.on_event(row)
        return row

    def _print(self, row: dict[str, Any]) -> None:
        t = str(row.get("type") or "")
        color = _COLORS.get(t, "") if self._use_color else ""
        reset = _RESET if self._use_color else ""
        summary = row.get("summary") or row.get("message") or row.get("text") or ""
        if not summary:
            # compact payload without ts/type
            slim = {k: v for k, v in row.items() if k not in {"ts", "type"} and v is not None}
            summary = json.dumps(slim, default=str)[:240]
        self.stream.write(f"{color}{t}{reset} {summary}\n")
        self.stream.flush()

    def write_json(self, name: str, data: Any) -> Path:
        path = self.run_dir / name
        path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
        return path

    def write_text(self, name: str, text: str) -> Path:
        path = self.run_dir / name
        path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
        return path


def delivery_run_dir(repo_root: Path, issue_key: str, run_id: str | None = None) -> Path:
    rid = run_id or new_run_id()
    return repo_root / ".ai-delivery" / issue_key / "runs" / rid
