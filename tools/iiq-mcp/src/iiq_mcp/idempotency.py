"""Local idempotency key store for write tools (Phase 2+)."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class IdempotencyStore:
    """SQLite-backed request_id → response cache."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency (
                  request_id TEXT PRIMARY KEY,
                  tool TEXT NOT NULL,
                  response_json TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def get(self, request_id: str, tool: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT response_json FROM idempotency WHERE request_id = ? AND tool = ?",
                (request_id, tool),
            ).fetchone()
            if not row:
                return None
            return json.loads(row["response_json"])

    def put(self, request_id: str, tool: str, response: dict[str, Any]) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO idempotency(request_id, tool, response_json)
                VALUES (?, ?, ?)
                """,
                (request_id, tool, json.dumps(response, default=str)),
            )
            conn.commit()
