"""Append-only operator feedback for prompt / eval improvements."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_PATH = Path(os.environ.get("TELLER_FEEDBACK_PATH") or (ROOT / "data" / "feedback.jsonl"))

_lock = threading.Lock()


def store_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    path = DEFAULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "id": uuid.uuid4().hex,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rating": payload.get("rating"),  # up | down
        "reason": payload.get("reason"),  # wrong_tool | wrong_answer | other | null
        "comment": (payload.get("comment") or "")[:2000],
        "question": (payload.get("question") or "")[:4000],
        "reply": (payload.get("reply") or "")[:4000],
        "model": payload.get("model"),
        "tools": payload.get("tools") if isinstance(payload.get("tools"), list) else [],
        "runId": payload.get("runId"),
        "correlationId": payload.get("correlationId"),
        "userId": payload.get("userId") or "anonymous",
    }
    line = json.dumps(record, default=str) + "\n"
    with _lock:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
    return {"ok": True, "id": record["id"], "stored": True}
