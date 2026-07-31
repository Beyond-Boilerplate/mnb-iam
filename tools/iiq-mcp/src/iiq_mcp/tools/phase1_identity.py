"""Phase 1 — Identity Warehouse (SCIM Users / Accounts)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from iiq_mcp.client.http import IiqHttpClient, encode_path_segment
from iiq_mcp.errors import map_http_error
from iiq_mcp.identity_resolve import (
    account_matches_profile_query,
    build_identity_search_filter,
    coalesce_profiles,
    dedupe_identities,
    identity_from_account,
    identity_key,
    prefer_identity,
    scim_escape,
    to_dotted_username,
)
from iiq_mcp.shaping import (
    list_envelope,
    scim_page_params,
    scim_resources,
    scim_total,
    trim_account,
    trim_identity,
)
from iiq_mcp.tools.meta import Risk, ToolMeta, run_tool, tool_description


async def resolve_user(client: IiqHttpClient, id_or_name: str) -> dict[str, Any]:
    """Resolve SCIM User by id, userName, dotted lab id, or display-name search."""
    hint = (id_or_name or "").strip()
    if not hint:
        raise map_http_error(400, {"message": "Identity id/name is required"})

    try:
        return await client.scim_get(f"/Users/{encode_path_segment(hint)}")
    except Exception:
        pass

    candidates_exact: list[str] = [hint]
    dotted = to_dotted_username(hint)
    if dotted and dotted not in candidates_exact:
        candidates_exact.append(dotted)
    found: list[dict[str, Any]] = []
    for cand in candidates_exact:
        try:
            payload = await client.scim_get(
                "/Users",
                params={"filter": f'userName eq "{scim_escape(cand)}"', "count": 5},
            )
            found.extend(dict(r) for r in scim_resources(payload))
        except Exception:
            continue
    if found:
        chosen = prefer_identity(found, hint)
        if chosen:
            return dict(chosen)

    try:
        payload = await client.scim_get(
            "/Users",
            params={
                "filter": build_identity_search_filter(hint),
                "count": 25,
            },
        )
        resources = scim_resources(payload)
        chosen = prefer_identity(resources, hint)
        if chosen:
            return dict(chosen)
    except Exception:
        pass

    raise map_http_error(404, {"message": f"Identity not found: {hint}"})


async def fetch_application_accounts(
    client: IiqHttpClient,
    application: str = "MNB-HR",
    *,
    page_size: int = 100,
    max_accounts: int = 500,
) -> list[dict[str, Any]]:
    """Page SCIM Accounts for an application (profile attrs live here, not on Users)."""
    app = scim_escape(application)
    filt = f'application.displayName eq "{app}"'
    start = 1
    collected: list[dict[str, Any]] = []
    while len(collected) < max_accounts:
        count = min(page_size, max_accounts - len(collected))
        payload = await client.scim_get(
            "/Accounts",
            params={"filter": filt, "startIndex": start, "count": count},
        )
        batch = [dict(r) for r in scim_resources(payload)]
        if not batch:
            break
        collected.extend(batch)
        total = scim_total(payload) or 0
        start += len(batch)
        if start > total or len(batch) < count:
            break
    return collected


async def search_identities_by_profile(
    client: IiqHttpClient,
    query: str,
    *,
    application: str = "MNB-HR",
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Match identities whose HR/IT account attributes contain the free-text query."""
    accounts = await fetch_application_accounts(client, application)
    matched: list[dict[str, Any]] = []
    for acct in accounts:
        if not account_matches_profile_query(acct, query):
            continue
        item = identity_from_account(acct)
        if item:
            matched.append(item)
    return dedupe_identities(matched)[: max(1, limit)]


def register(mcp: FastMCP, client: IiqHttpClient, **ctx: Any) -> None:
    audit = ctx.get("audit")

    meta_search = ToolMeta(
        name="search_identities",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        description="Search IIQ identities via SCIM Users (+ HR profile fallback).",
    )

    @mcp.tool(
        name=meta_search.name,
        description=tool_description(
            meta_search,
            "Search identities by SCIM filter or free-text. "
            "Matches userName/displayName (including lab first.last forms). "
            "When a free-text query matches no Users, also searches MNB-HR account "
            "profile attributes (city, location, title, department, manager, etc.). "
            "Prefer filter= for structured SCIM User queries.",
        ),
    )
    async def search_identities(
        query: str | None = None,
        filter: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {**scim_page_params(start, count)}
        if filter:
            params["filter"] = filter
        elif query:
            params["filter"] = build_identity_search_filter(query)

        async def _run() -> dict[str, Any]:
            payload = await client.scim_get("/Users", params=params)
            items = [trim_identity(u, raw=raw) for u in scim_resources(payload)]
            if query and " " in query.strip():
                best = prefer_identity(items, query)
                if best:
                    best_id = best.get("id")
                    items = [best] + [i for i in items if i.get("id") != best_id]
            s = params["startIndex"] - 1
            total = scim_total(payload)
            # Workplace attrs (city/title/dept) are on accounts, not Users.
            if query and not filter and not items:
                profile_hits = await search_identities_by_profile(
                    client, query, limit=params["count"]
                )
                if profile_hits:
                    return list_envelope(
                        profile_hits,
                        start=0,
                        count=params["count"],
                        total=len(profile_hits),
                        raw=raw,
                    ) | {"matchedVia": "account_profile"}
            return list_envelope(
                items, start=s, count=params["count"], total=total, raw=raw
            )

        return await run_tool(
            meta_search,
            {"query": query, "filter": filter, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_profiles = ToolMeta(
        name="search_profiles",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        description="Find identities by HR/IT account profile attributes.",
    )

    @mcp.tool(
        name=meta_profiles.name,
        description=tool_description(
            meta_profiles,
            "Find people by workplace/profile attributes on application accounts "
            "(city, location, title, department, manager, cost center, email, …). "
            "Use when the question is about where someone works, their role/org, "
            "or other HR fields — not just userName. Defaults to MNB-HR accounts.",
        ),
    )
    async def search_profiles(
        query: str,
        application: str | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        q = (query or "").strip()
        if not q:
            raise map_http_error(400, {"message": "query is required"})
        limit = count if count and count > 0 else 25
        app = (application or "MNB-HR").strip() or "MNB-HR"

        async def _run() -> dict[str, Any]:
            items = await search_identities_by_profile(
                client, q, application=app, limit=limit
            )
            return list_envelope(
                items, start=0, count=limit, total=len(items), raw=raw
            ) | {"matchedVia": "account_profile", "application": app}

        return await run_tool(
            meta_profiles,
            {"query": query, "application": application, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_get = ToolMeta(
        name="get_identity",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        description="Fetch one identity cube via SCIM.",
    )

    @mcp.tool(
        name=meta_get.name,
        description=tool_description(
            meta_get,
            "Get identity by SCIM id, userName, or display name (``id`` or ``name``). "
            "Returns trimmed cube unless raw=true.",
        ),
    )
    async def get_identity(
        id: str | None = None,
        name: str | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        try:
            key = identity_key(id=id, name=name)
        except ValueError as exc:
            raise map_http_error(400, {"message": str(exc)}) from exc

        async def _run() -> dict[str, Any]:
            user = await resolve_user(client, key)
            return trim_identity(user, raw=raw)

        return await run_tool(meta_get, {"id": id, "name": name, "raw": raw}, _run, audit=audit)

    meta_access = ToolMeta(
        name="get_identity_access",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_access.name,
        description=tool_description(
            meta_access,
            "Return roles/entitlements from the SCIM User cube. "
            "Accepts ``id`` or ``name`` (userName / display name).",
        ),
    )
    async def get_identity_access(
        id: str | None = None,
        name: str | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        try:
            key = identity_key(id=id, name=name)
        except ValueError as exc:
            raise map_http_error(400, {"message": str(exc)}) from exc

        async def _run() -> dict[str, Any]:
            user = await resolve_user(client, key)
            sail = user.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
            access = {
                "id": user.get("id"),
                "userName": user.get("userName"),
                "roles": sail.get("roles") or user.get("roles"),
                "entitlements": sail.get("entitlements") or user.get("entitlements"),
                "bundles": sail.get("bundles"),
                "detectedRoles": sail.get("detectedRoles"),
                "assignedRoles": sail.get("assignedRoles"),
            }
            return access if not raw else {"trimmed": access, "rawUser": user}

        return await run_tool(
            meta_access, {"id": id, "name": name, "raw": raw}, _run, audit=audit
        )

    meta_accts = ToolMeta(
        name="get_identity_accounts",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_accts.name,
        description=tool_description(
            meta_accts,
            "List SCIM Accounts for an identity (``id`` or ``name``). "
            "Always includes ``profileHints`` (title/department/email from HR schemas) "
            "so job-title questions work even when the identity cube lacks title. "
            "Pass raw=true for full account schemas.",
        ),
    )
    async def get_identity_accounts(
        id: str | None = None,
        name: str | None = None,
        start: int | None = None,
        count: int | None = None,
        raw: bool = False,
    ) -> dict[str, Any]:
        try:
            key = identity_key(id=id, name=name)
        except ValueError as exc:
            raise map_http_error(400, {"message": str(exc)}) from exc

        async def _run() -> dict[str, Any]:
            user = await resolve_user(client, key)
            identity_id = user.get("id") or key
            user_name = user.get("userName")
            page = scim_page_params(start, count)
            filters = [
                f'identity.value eq "{identity_id}"',
                f'identity eq "{identity_id}"',
            ]
            if user_name:
                escaped = scim_escape(str(user_name))
                filters.append(f'identity.userName eq "{escaped}"')
                filters.append(f'identity.displayName eq "{escaped}"')
            last_err: Exception | None = None
            payload = None
            for filt in filters:
                try:
                    payload = await client.scim_get(
                        "/Accounts", params={**page, "filter": filt}
                    )
                    break
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
            if payload is None and last_err:
                raise last_err
            raw_accounts = list(scim_resources(payload))
            profile = coalesce_profiles(raw_accounts)
            items = [trim_account(a, raw=raw) for a in raw_accounts]
            envelope = list_envelope(
                items,
                start=page["startIndex"] - 1,
                count=page["count"],
                total=scim_total(payload),
                raw=raw,
            )
            envelope["identity"] = {
                "id": user.get("id"),
                "userName": user.get("userName"),
                "displayName": user.get("displayName"),
            }
            envelope["profileHints"] = profile
            return envelope

        return await run_tool(
            meta_accts,
            {"id": id, "name": name, "start": start, "count": count, "raw": raw},
            _run,
            audit=audit,
        )

    meta_risk = ToolMeta(
        name="get_identity_risk_score",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_risk.name,
        description=tool_description(
            meta_risk,
            "Best-effort risk score from SCIM SailPoint User extension attributes.",
        ),
    )
    async def get_identity_risk_score(
        id: str | None = None, name: str | None = None
    ) -> dict[str, Any]:
        try:
            key = identity_key(id=id, name=name)
        except ValueError as exc:
            raise map_http_error(400, {"message": str(exc)}) from exc

        async def _run() -> dict[str, Any]:
            user = await resolve_user(client, key)
            sail = user.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
            return {
                "id": user.get("id"),
                "userName": user.get("userName"),
                "riskScore": sail.get("riskScore")
                or sail.get("compositeRiskScore")
                or user.get("riskScore"),
                "riskLevel": sail.get("riskLevel"),
                "source": "scim_sailpoint_user_extension",
            }

        return await run_tool(meta_risk, {"id": id, "name": name}, _run, audit=audit)

    meta_hist = ToolMeta(
        name="get_identity_history",
        phase=1,
        risk=Risk.READ,
        implemented=True,
        gap_id="UIAPI-18",
    )

    @mcp.tool(
        name=meta_hist.name,
        description=tool_description(
            meta_hist,
            "Best-effort history: Meridian audit events filtered by identity + accessHistory status probe.",
        ),
    )
    async def get_identity_history(
        id: str | None = None,
        name: str | None = None,
        count: int | None = 50,
    ) -> dict[str, Any]:
        from iiq_mcp.tools.agent_helpers import agent_get

        try:
            key = identity_key(id=id, name=name)
        except ValueError as exc:
            raise map_http_error(400, {"message": str(exc)}) from exc

        async def _run() -> dict[str, Any]:
            user = await resolve_user(client, key)
            uname = user.get("userName") or key
            audits: list[Any] = []
            try:
                rows = await agent_get(client, "/audit/events", params={"limit": count or 50})
                if isinstance(rows, list):
                    audits = [
                        r
                        for r in rows
                        if uname in str(r.get("target", ""))
                        or uname in str(r.get("source", ""))
                        or key in str(r.get("target", ""))
                    ]
            except Exception as exc:  # noqa: BLE001
                audits = [{"error": str(exc)}]
            module_status = None
            try:
                module_status = await agent_get(client, "/accessHistory/status")
            except Exception as exc:  # noqa: BLE001
                module_status = {"error": str(exc)}
            return {
                "identity": uname,
                "audit_events": audits,
                "access_history_module": module_status,
            }

        return await run_tool(
            meta_hist, {"id": id, "name": name, "count": count}, _run, audit=audit
        )

    meta_mgr = ToolMeta(
        name="get_manager_hierarchy",
        phase=1,
        risk=Risk.READ,
        implemented=True,
    )

    @mcp.tool(
        name=meta_mgr.name,
        description=tool_description(
            meta_mgr,
            "Walk manager chain upward via SCIM; also list direct reports (best-effort).",
        ),
    )
    async def get_manager_hierarchy(
        id: str | None = None,
        name: str | None = None,
        max_depth: int = 8,
        raw: bool = False,
    ) -> dict[str, Any]:
        try:
            key = identity_key(id=id, name=name)
        except ValueError as exc:
            raise map_http_error(400, {"message": str(exc)}) from exc

        async def _run() -> dict[str, Any]:
            chain: list[dict[str, Any]] = []
            current_id = key
            seen: set[str] = set()
            for _ in range(max(1, min(max_depth, 20))):
                try:
                    user = await resolve_user(client, current_id)
                except Exception:
                    break
                uid = str(user.get("id") or "")
                if not uid or uid in seen:
                    break
                seen.add(uid)
                chain.append(trim_identity(user, raw=raw))
                sail = user.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
                ent = user.get("urn:ietf:params:scim:schemas:extension:enterprise:2.0:User") or {}
                mgr = sail.get("manager") or ent.get("manager") or user.get("manager")
                if not mgr:
                    break
                if isinstance(mgr, dict):
                    current_id = (
                        mgr.get("value")
                        or mgr.get("id")
                        or mgr.get("displayName")
                        or mgr.get("userName")
                    )
                else:
                    current_id = str(mgr)
                if not current_id:
                    break

            reports: list[dict[str, Any]] = []
            root = chain[0] if chain else {}
            root_id = str(root.get("id") or "")
            root_name = root.get("userName") or root.get("displayName") or key
            # IIQ SCIM resolves direct reports via enterprise manager.value (identity id),
            # not bare manager eq "displayName" / userName.
            filter_candidates: list[str] = []
            if root_id:
                filter_candidates.append(
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:"
                    f'manager.value eq "{root_id}"'
                )
            if root_name:
                filter_candidates.extend(
                    [
                        f'manager eq "{root_name}"',
                        f'manager.displayName eq "{root_name}"',
                    ]
                )
            for filt in filter_candidates:
                try:
                    payload = await client.scim_get(
                        "/Users",
                        params={
                            "filter": filt,
                            **scim_page_params(0, 50),
                        },
                    )
                    found = [trim_identity(u, raw=raw) for u in scim_resources(payload)]
                    if found:
                        reports = found
                        break
                except Exception:
                    continue

            return {"chain": chain, "directReports": reports, "depth": len(chain)}

        return await run_tool(
            meta_mgr,
            {"id": id, "name": name, "max_depth": max_depth, "raw": raw},
            _run,
            audit=audit,
        )
