"""Unit tests for MCP error taxonomy."""

from iiq_mcp.errors import ErrorCode, map_http_error, not_implemented, phase_disabled


def test_map_404() -> None:
    err = map_http_error(404, {"message": "missing"})
    assert err.body.code == ErrorCode.NOT_FOUND
    assert err.body.http_status == 404


def test_map_401() -> None:
    err = map_http_error(401, "nope")
    assert err.body.code == ErrorCode.UNAUTHORIZED


def test_map_500() -> None:
    err = map_http_error(500, "boom")
    assert err.body.code == ErrorCode.DOWNSTREAM


def test_not_implemented_gap() -> None:
    err = not_implemented("search_audit_events", phase=1, gap_id="UIAPI-18")
    d = err.to_dict()
    assert d["code"] == "not_implemented"
    assert d["gap_id"] == "UIAPI-18"


def test_phase_disabled() -> None:
    err = phase_disabled("create_account", 4)
    assert err.body.code == ErrorCode.PHASE_DISABLED
    assert err.body.phase == 4
