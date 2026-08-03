"""SQLite claim leases so two runners don't grab the same issue."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any


class LeaseStore:
    def __init__(self, db_path: Path, *, ttl_seconds: int = 3600, worker_id: str = "auto-story") -> None:
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        self.worker_id = worker_id
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leases (
                issue_key TEXT PRIMARY KEY,
                worker_id TEXT NOT NULL,
                state TEXT NOT NULL,
                expires_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def try_claim(self, issue_key: str) -> bool:
        now = time.time()
        self._expire(now)
        row = self._conn.execute(
            "SELECT worker_id, expires_at, state FROM leases WHERE issue_key = ?",
            (issue_key,),
        ).fetchone()
        if row:
            worker, expires, state = row
            if expires > now and state in {"claimed", "running"} and worker != self.worker_id:
                return False
        self._conn.execute(
            """
            INSERT INTO leases (issue_key, worker_id, state, expires_at, updated_at)
            VALUES (?, ?, 'claimed', ?, ?)
            ON CONFLICT(issue_key) DO UPDATE SET
                worker_id = excluded.worker_id,
                state = 'claimed',
                expires_at = excluded.expires_at,
                updated_at = excluded.updated_at
            """,
            (issue_key, self.worker_id, now + self.ttl_seconds, now),
        )
        self._conn.commit()
        return True

    def mark_running(self, issue_key: str) -> None:
        now = time.time()
        self._conn.execute(
            """
            UPDATE leases SET state = 'running', expires_at = ?, updated_at = ?
            WHERE issue_key = ? AND worker_id = ?
            """,
            (now + self.ttl_seconds, now, issue_key, self.worker_id),
        )
        self._conn.commit()

    def release(self, issue_key: str, *, state: str = "done") -> None:
        now = time.time()
        self._conn.execute(
            """
            UPDATE leases SET state = ?, expires_at = ?, updated_at = ?
            WHERE issue_key = ? AND worker_id = ?
            """,
            (state, now, now, issue_key, self.worker_id),
        )
        self._conn.commit()

    def _expire(self, now: float) -> None:
        self._conn.execute(
            "DELETE FROM leases WHERE expires_at < ? AND state IN ('claimed', 'running')",
            (now,),
        )
        self._conn.commit()

    def status(self, issue_key: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT worker_id, state, expires_at, updated_at FROM leases WHERE issue_key = ?",
            (issue_key,),
        ).fetchone()
        if not row:
            return None
        return {
            "worker_id": row[0],
            "state": row[1],
            "expires_at": row[2],
            "updated_at": row[3],
        }
