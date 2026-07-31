"""Golden intent harness — unit tests (no live MCP required)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

CHAT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAT_ROOT))
sys.path.insert(0, str(CHAT_ROOT / "scripts"))

from golden_intents import GOLDEN_INTENTS, run_probes  # noqa: E402


def test_golden_intents_cover_plan_pilots():
    ids = {i["id"] for i in GOLDEN_INTENTS}
    for required in (
        "nl-who-anita",
        "nl-anyone-anita",
        "nl-paris",
        "ldap-onboard",
        "grant-access",
        "unlock",
        "cert-list",
        "sod-count",
    ):
        assert required in ids


def test_run_probes_read_paths():
    calls: list[tuple[str, dict]] = []

    def call(name: str, args: dict):
        calls.append((name, args))
        if name == "search_identities":
            return {"ok": True, "data": {"items": [{"userName": "anita.rao"}], "totalResults": 1}}
        if name == "search_profiles":
            return {"ok": True, "data": {"items": [], "totalResults": 0}}
        if name == "get_requestable_items":
            return {"ok": True, "data": {"items": []}}
        if name == "list_certifications":
            return {"ok": True, "data": {"items": []}}
        if name == "count_open_sod_violations":
            return {"ok": True, "data": {"count": 0}}
        return {"ok": True, "data": {}}

    rows = run_probes(call, do_writes=False)
    assert all(r["ok"] for r in rows)
    assert any(c[0] == "search_identities" for c in calls)
    assert any(c[0] == "search_profiles" for c in calls)
    assert any(c[0] == "count_open_sod_violations" for c in calls)
    # writes skipped without --write
    assert any(r.get("skipped") for r in rows if r["id"] in ("ldap-onboard", "unlock"))


def test_run_probes_writes():
    wrote: list[str] = []

    def call(name: str, args: dict):
        wrote.append(name)
        return {"ok": True, "data": {"tool": name}}

    rows = run_probes(call, do_writes=True)
    assert "onboard_application" in wrote
    assert "grant_access" in wrote or "unlock_iiq_identity" in wrote
    assert "unlock_iiq_identity" in wrote
    assert all(r["ok"] for r in rows)
