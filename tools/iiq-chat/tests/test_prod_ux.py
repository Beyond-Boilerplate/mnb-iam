"""Tests for cards, playbooks, observability, and grounding helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CHAT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAT_ROOT))

from cards import build_cards, citation_footer  # noqa: E402
from llm import _ensure_sources_footer, _tool_failure_note  # noqa: E402
from observability import METRICS, log_event, new_correlation_id  # noqa: E402
from playbooks_loader import playbooks_for_role  # noqa: E402


def test_build_sod_and_identity_cards():
    steps = [
        {
            "tool": "count_open_sod_violations",
            "result": {"ok": True, "data": {"count": 3, "items": [{"label": "Anita Rao", "conflict": "A vs B"}]}},
        },
        {
            "tool": "get_identity",
            "result": {
                "ok": True,
                "data": {
                    "tellerCard": {
                        "displayName": "Anita Rao",
                        "userName": "anita.rao",
                        "title": "Analyst",
                        "active": True,
                    }
                },
            },
        },
    ]
    cards = build_cards(steps)
    types = {c["type"] for c in cards}
    assert "sod" in types
    assert "identity" in types
    sod = next(c for c in cards if c["type"] == "sod")
    assert sod["fields"]["count"] == 3
    assert sod["source"] == "count_open_sod_violations"


def test_citation_and_refusal():
    steps = [
        {"tool": "get_identity", "result": {"ok": False, "error": "boom"}},
        {"tool": "search_identities", "result": {"ok": False, "error": "down"}},
    ]
    note = _tool_failure_note(steps)
    assert note and "will not invent" in note.lower()
    ok_steps = [{"tool": "get_identity", "result": {"ok": True, "data": {"userName": "a"}}}]
    reply = _ensure_sources_footer("Anita is an analyst.", ok_steps)
    assert "Sources:" in reply and "`get_identity`" in reply
    assert "get_identity" in citation_footer(ok_steps)


def test_playbooks_default_has_no_lab_personas():
    bundle = playbooks_for_role("operator")
    assert bundle["role"] == "operator"
    labels = " ".join(p.get("label", "") for p in bundle["playbooks"]).lower()
    assert "nina" not in labels
    assert "priya" not in labels
    assert "jordan" not in labels
    lab = playbooks_for_role("lab")
    lab_labels = " ".join(p.get("label", "") for p in lab["playbooks"]).lower()
    assert "nina" in lab_labels or "priya" in lab_labels


def test_metrics_and_correlation():
    cid = new_correlation_id()
    assert len(cid) >= 8
    METRICS.inc("test.counter")
    METRICS.observe("test.latency_ms", 12.5)
    METRICS.set_mcp(True)
    snap = METRICS.snapshot()
    assert snap["counters"].get("test.counter", 0) >= 1
    assert "test.latency_ms" in snap["latencies"]
    log_event("unit_test", correlation_id=cid, outcome="success", tool="ping")
