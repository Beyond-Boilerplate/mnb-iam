"""Unit tests for Teller blackbox assert engine (no LLM / network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

EVAL_ROOT = Path(__file__).resolve().parents[1] / "eval"
CHAT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHAT_ROOT))
sys.path.insert(0, str(EVAL_ROOT))

from assert_engine import evaluate_case, evaluate_expect  # noqa: E402
from runner import filter_cases, load_cases  # noqa: E402


def test_load_cases_nonempty():
    cases = load_cases()
    assert len(cases) >= 20
    ids = {c["id"] for c in cases}
    assert "smoke-who-anita" in ids
    assert "access-grant-wire-initiator" in ids
    assert "jml-joiner-dry-run-new" in ids
    assert "cert-create-from-template" in ids


def test_filter_tier_smoke_subset():
    cases = load_cases()
    smoke = filter_cases(cases, tier="smoke", tags=None, ids=None, include_xfail=True, mutate=None)
    assert smoke
    assert all((c.get("tier") or "core") == "smoke" for c in smoke)


def test_filter_exclude_mutate():
    cases = load_cases()
    read = filter_cases(cases, tier="full", tags=None, ids=None, include_xfail=True, mutate=False)
    assert read
    assert all(not c.get("mutate") for c in read)


def test_reply_contains_and_tools():
    resp = {
        "ok": True,
        "reply": "Anita Rao is an active identity in Technology.",
        "steps": [
            {"tool": "search_identities", "arguments": {"query": "Anita Rao"}, "result": {"ok": True}},
            {"tool": "get_identity", "arguments": {"id": "x"}, "result": {"ok": True}},
        ],
    }
    r = evaluate_expect(
        {
            "tools_any_of": ["search_identities", "get_identity"],
            "reply_contains_any": ["Anita"],
            "no_tool_errors": True,
            "min_tools": 1,
        },
        resp,
    )
    assert r.ok, r.failures


def test_forbidden_scim_filter_detected():
    resp = {
        "ok": True,
        "reply": "search_entitlements failed",
        "steps": [
            {
                "tool": "search_entitlements",
                "arguments": {"query": "Wire Initiator"},
                "result": {
                    "ok": False,
                    "error": {
                        "code": "validation",
                        "http_status": 400,
                        "message": "Invalid filter, attribute not found:displayName",
                    },
                },
            }
        ],
    }
    r = evaluate_case(
        {
            "id": "access-grant-wire-initiator",
            "expect": {
                "tools_any_of": ["search_entitlements", "grant_access"],
                "reply_not_contains_any": ["Invalid filter"],
                "no_tool_errors": True,
            },
        },
        resp,
    )
    assert not r.ok
    assert any("tool errors" in f or "filter" in f.lower() for f in r.failures)


def test_pass_if_any_or_logic():
    resp = {
        "ok": True,
        "reply": "Dry-run joiner preview for Helen Ross completed.",
        "steps": [
            {
                "tool": "run_jml_event",
                "arguments": {"dry_run": True},
                "result": {"ok": True, "data": {"dryRun": True}},
            }
        ],
    }
    r = evaluate_case(
        {
            "pass_if_any": [
                {"tools_any_of": ["missing_tool"], "reply_contains": ["never"]},
                {"tools_any_of": ["run_jml_event"], "reply_contains_any": ["dry"]},
            ]
        },
        resp,
    )
    assert r.ok


def test_require_ok_tools_ignores_incidental_404():
    resp = {
        "ok": True,
        "reply": "Digest shows 81 identities across MNB applications.",
        "steps": [
            {
                "tool": "get_iiq_status",
                "result": {"ok": False, "error": {"code": "not_found", "http_status": 404}},
            },
            {
                "tool": "get_executive_digest",
                "result": {"ok": True, "data": {"identities": 81}},
            },
        ],
    }
    r = evaluate_expect(
        {
            "tools_any_of": ["get_executive_digest"],
            "require_ok_tools_any_of": ["get_executive_digest"],
            "reply_contains_any": ["81", "identit"],
            "no_tool_errors": True,
        },
        resp,
    )
    assert r.ok, r.failures


def test_xfail_cases_present_for_regressions():
    cases = load_cases()
    xf = {c["id"] for c in cases if c.get("xfail")}
    assert "access-grant-wire-initiator" in xf
    assert "jml-joiner-dry-run-new" in xf
    assert "cert-create-from-template" in xf


def test_cases_json_valid():
    cases_dir = EVAL_ROOT / "cases"
    for path in cases_dir.glob("*.json"):
        data = json.loads(path.read_text())
        assert isinstance(data, list), path.name
        for item in data:
            assert item.get("id"), path.name
            assert item.get("query"), item.get("id")
            assert item.get("expect") or item.get("pass_if_any"), item.get("id")
