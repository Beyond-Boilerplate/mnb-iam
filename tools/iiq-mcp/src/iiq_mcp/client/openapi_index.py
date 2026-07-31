"""Load / query the OpenAPI-derived IIQ operation index."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

INDEX_PATH = Path(__file__).with_name("op_index.json")


@lru_cache
def load_index(path: str | None = None) -> dict[str, Any]:
    p = Path(path) if path else INDEX_PATH
    if not p.exists():
        return {"generated": None, "operations": [], "by_operation_id": {}, "surfaces": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def find_operation(operation_id: str) -> dict[str, Any] | None:
    idx = load_index()
    return idx.get("by_operation_id", {}).get(operation_id)


def list_operations(*, surface: str | None = None, tag: str | None = None) -> list[dict[str, Any]]:
    ops = list(load_index().get("operations") or [])
    if surface:
        ops = [o for o in ops if o.get("surface") == surface]
    if tag:
        ops = [o for o in ops if tag in (o.get("tags") or [])]
    return ops


def resolve_path(operation_id: str, **path_params: str) -> tuple[str, str]:
    """Return ``(method, absolute_iiq_path)`` for a known operationId."""
    op = find_operation(operation_id)
    if not op:
        raise KeyError(f"Unknown operationId: {operation_id}")
    path = op["path"]
    for key, value in path_params.items():
        path = path.replace("{" + key + "}", str(value))
    mount = op.get("mount") or ""
    full = f"{mount.rstrip('/')}{path}" if mount else path
    return op["method"].upper(), full
