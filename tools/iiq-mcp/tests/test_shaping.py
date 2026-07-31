"""Unit tests for response shaping helpers."""

from iiq_mcp.shaping import (
    clamp_page,
    list_envelope,
    pick,
    scim_page_params,
    trim_application,
    trim_identity,
)


def test_clamp_page_defaults() -> None:
    start, count = clamp_page(None, None)
    assert start == 0
    assert count == 25


def test_clamp_page_caps() -> None:
    start, count = clamp_page(-5, 9999)
    assert start == 0
    assert count == 100


def test_scim_page_params_one_based() -> None:
    p = scim_page_params(10, 5)
    assert p == {"startIndex": 11, "count": 5}


def test_pick() -> None:
    assert pick({"a": 1, "b": 2}, ("a", "c")) == {"a": 1}


def test_trim_identity_raw_passthrough() -> None:
    user = {"id": "1", "userName": "a", "extra": {"x": 1}}
    assert trim_identity(user, raw=True) == user


def test_list_envelope() -> None:
    env = list_envelope([1, 2], start=0, count=10, total=2, raw=False)
    assert env["returned"] == 2
    assert env["items"] == [1, 2]


def test_trim_application_drops_java_array_tostring_features() -> None:
    app = {
        "id": "1",
        "name": "MNB-HR",
        "type": "DelimitedFile",
        "features": ["[Ljava.lang.String;@58bbde74"],
    }
    out = trim_application(app)
    assert out["features"] == []


def test_trim_application_falls_back_to_features_string() -> None:
    app = {
        "id": "1",
        "name": "MNB-HR",
        "features": ["[Ljava.lang.String;@deadbeef"],
        "featuresString": "DIRECT_PERMISSIONS, DISCOVER_SCHEMA",
    }
    out = trim_application(app)
    assert out["features"] == ["DIRECT_PERMISSIONS", "DISCOVER_SCHEMA"]
    assert out["featuresString"] == "DIRECT_PERMISSIONS, DISCOVER_SCHEMA"
