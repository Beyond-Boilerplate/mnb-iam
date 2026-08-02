"""Load role-scoped playbooks / suggest chips from config/playbooks.json."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_PATH = ROOT / "config" / "playbooks.json"


def load_playbook_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or Path(os.environ.get("TELLER_PLAYBOOKS_PATH") or DEFAULT_PATH)
    if not cfg_path.is_file():
        return {
            "defaultRole": "operator",
            "roles": {
                "operator": {
                    "label": "Operator",
                    "suggest": [],
                    "playbooks": [],
                }
            },
        }
    with cfg_path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


def resolve_role(requested: str | None = None) -> str:
    cfg = load_playbook_config()
    roles = cfg.get("roles") if isinstance(cfg.get("roles"), dict) else {}
    env_role = (os.environ.get("TELLER_PLAYBOOK_ROLE") or "").strip()
    role = (requested or env_role or cfg.get("defaultRole") or "operator").strip()
    if role not in roles:
        role = str(cfg.get("defaultRole") or "operator")
    if role not in roles and roles:
        role = next(iter(roles.keys()))
    return role


def playbooks_for_role(role: str | None = None) -> dict[str, Any]:
    cfg = load_playbook_config()
    roles = cfg.get("roles") if isinstance(cfg.get("roles"), dict) else {}
    resolved = resolve_role(role)
    bundle = roles.get(resolved) if isinstance(roles.get(resolved), dict) else {}
    playbooks = bundle.get("playbooks") if isinstance(bundle.get("playbooks"), list) else []
    suggest = bundle.get("suggest") if isinstance(bundle.get("suggest"), list) else []
    return {
        "ok": True,
        "role": resolved,
        "roleLabel": bundle.get("label") or resolved,
        "roles": [
            {"id": rid, "label": (rval.get("label") if isinstance(rval, dict) else rid)}
            for rid, rval in roles.items()
        ],
        "suggest": suggest,
        "playbooks": playbooks,
        "source": "config/playbooks.json",
    }
