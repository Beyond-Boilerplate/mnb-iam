"""Unit tests for smart identity resolution helpers."""

from __future__ import annotations

import pytest

from iiq_mcp.identity_resolve import (
    account_matches_profile_query,
    build_identity_search_filter,
    coalesce_profiles,
    extract_account_profile,
    identity_from_account,
    identity_key,
    prefer_identity,
    profile_query_tokens,
    to_dotted_username,
)


def test_to_dotted_username_from_display_name():
    assert to_dotted_username("Anita Rao") == "anita.rao"
    assert to_dotted_username("Helen Ross") == "helen.ross"
    assert to_dotted_username("anita.rao") == "anita.rao"
    assert to_dotted_username("  ") is None


def test_build_identity_search_filter_includes_dotted_form():
    filt = build_identity_search_filter("Anita Rao")
    assert 'userName eq "anita.rao"' in filt
    assert 'userName co "Anita Rao"' in filt
    assert 'userName co "Anita"' in filt
    assert 'userName co "Rao"' in filt


def test_prefer_identity_prefers_dotted_over_spaced_username():
    candidates = [
        {"id": "1", "userName": "Helen Ross", "displayName": "Helen Ross"},
        {"id": "2", "userName": "helen.ross", "displayName": "helen.ross"},
    ]
    chosen = prefer_identity(candidates, "Helen Ross")
    assert chosen is not None
    assert chosen["userName"] == "helen.ross"


def test_prefer_identity_exact_dotted():
    candidates = [
        {"id": "1", "userName": "anita.ross", "displayName": "anita.ross"},
        {"id": "2", "userName": "anita.rao", "displayName": "anita.rao"},
        {"id": "3", "userName": "anthony.rao", "displayName": "anthony.rao"},
    ]
    chosen = prefer_identity(candidates, "Anita Rao")
    assert chosen is not None
    assert chosen["userName"] == "anita.rao"


def test_identity_key_accepts_name_alias():
    assert identity_key(name="Anita Rao") == "Anita Rao"
    assert identity_key(id="anita.rao") == "anita.rao"
    with pytest.raises(ValueError):
        identity_key()


def test_extract_and_coalesce_hr_title():
    acct = {
        "application": {"displayName": "MNB-HR"},
        "urn:ietf:params:scim:schemas:sailpoint:1.0:Application:Schema:MNB-HR:account": {
            "title": "Site Reliability Engineer",
            "departmentName": "Technology Platforms",
            "email": "anita.rao@meridiannb.com",
            "fullName": "Anita Rao",
        },
    }
    prof = extract_account_profile(acct)
    assert prof["title"] == "Site Reliability Engineer"
    assert prof["application"] == "MNB-HR"

    merged = coalesce_profiles([acct])
    assert merged["resolvedTitle"] == "Site Reliability Engineer"
    assert merged["departmentName"] == "Technology Platforms"


def test_profile_query_tokens_strips_nl_filler():
    assert profile_query_tokens("list all identities from Kathmandu") == ["kathmandu"]
    assert profile_query_tokens("Site Reliability Engineer") == [
        "site",
        "reliability",
        "engineer",
    ]


def test_account_matches_kathmandu_nl_query():
    acct = {
        "application": {"displayName": "MNB-HR"},
        "identity": {
            "displayName": "anita.rao",
            "userName": "anita.rao",
            "value": "id-1",
        },
        "urn:ietf:params:scim:schemas:sailpoint:1.0:Application:Schema:MNB-HR:account": {
            "city": "Kathmandu",
            "location": "NP-KTM",
            "rfLocationName": "Kathmandu Hub",
            "title": "Site Reliability Engineer",
            "fullName": "Anita Rao",
        },
    }
    assert account_matches_profile_query(acct, "Kathmandu")
    assert account_matches_profile_query(acct, "list all identities from Kathmandu")
    assert account_matches_profile_query(acct, "NP-KTM")
    assert not account_matches_profile_query(acct, "Reykjavik")

    item = identity_from_account(acct)
    assert item is not None
    assert item["userName"] == "anita.rao"
    assert item["profileHints"]["resolvedTitle"] == "Site Reliability Engineer"
