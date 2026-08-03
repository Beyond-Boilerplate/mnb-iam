"""Jira Cloud REST helpers for auto-story (never transitions to Done)."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class JiraError(RuntimeError):
    pass


class JiraClient:
    def __init__(self, site: str, email: str, token: str) -> None:
        if not site or not email or not token:
            raise JiraError("JIRA_SITE, JIRA_EMAIL/JIRA_BOT_EMAIL, and JIRA_API_TOKEN required")
        self.site = site.rstrip("/")
        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _req(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        url = f"{self.site}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self._headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:800]
            raise JiraError(f"Jira HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise JiraError(f"Jira unreachable: {exc}") from exc

    def search(self, jql: str, *, max_results: int = 50) -> list[dict[str, Any]]:
        # GET /rest/api/3/search was removed (HTTP 410). Use enhanced search.
        # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/
        body = {
            "jql": jql,
            "maxResults": max_results,
            "fields": [
                "summary",
                "status",
                "assignee",
                "labels",
                "description",
                "issuetype",
            ],
        }
        payload = self._req("POST", "/rest/api/3/search/jql", body)
        return list(payload.get("issues") or [])

    def get_issue(self, key: str) -> dict[str, Any]:
        return self._req(
            "GET",
            f"/rest/api/3/issue/{urllib.parse.quote(key)}?fields=summary,status,assignee,labels,description,issuetype",
        )

    def assign(self, key: str, account_id: str | None = None, *, name: str | None = None) -> None:
        body: dict[str, Any]
        if account_id:
            body = {"accountId": account_id}
        elif name:
            body = {"name": name}
        else:
            # Assign to self (bot) — Jira Cloud prefers accountId; fall back to null clears
            me = self._req("GET", "/rest/api/3/myself")
            body = {"accountId": me.get("accountId")}
        self._req("PUT", f"/rest/api/3/issue/{urllib.parse.quote(key)}/assignee", body)

    def add_comment(self, key: str, body_text: str) -> None:
        # ADF document
        doc = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": body_text[:30000]}],
                    }
                ],
            }
        }
        self._req("POST", f"/rest/api/3/issue/{urllib.parse.quote(key)}/comment", doc)

    def add_label(self, key: str, label: str) -> None:
        self._req(
            "PUT",
            f"/rest/api/3/issue/{urllib.parse.quote(key)}",
            {"update": {"labels": [{"add": label}]}},
        )

    def transitions(self, key: str) -> list[dict[str, Any]]:
        payload = self._req("GET", f"/rest/api/3/issue/{urllib.parse.quote(key)}/transitions")
        return list(payload.get("transitions") or [])

    def transition_to(self, key: str, target_status_name: str) -> dict[str, Any]:
        """Transition to a named status. Refuses Done."""
        target = target_status_name.strip().lower()
        if target in {"done", "closed", "resolved"}:
            raise JiraError("Refusing to transition to Done/Closed (PM owns Done)")
        for t in self.transitions(key):
            name = str((t.get("to") or {}).get("name") or t.get("name") or "")
            if name.lower() == target:
                self._req(
                    "POST",
                    f"/rest/api/3/issue/{urllib.parse.quote(key)}/transitions",
                    {"transition": {"id": t["id"]}},
                )
                return {"ok": True, "transition": name, "id": t["id"]}
        available = [str((t.get("to") or {}).get("name") or t.get("name")) for t in self.transitions(key)]
        raise JiraError(f"No transition to '{target_status_name}'. Available: {available}")


def issue_plain_text(issue: dict[str, Any]) -> dict[str, Any]:
    fields = issue.get("fields") or {}
    desc = fields.get("description")
    if isinstance(desc, dict):
        # flatten ADF lightly
        parts: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "text" and node.get("text"):
                    parts.append(str(node["text"]))
                for c in node.get("content") or []:
                    walk(c)
            elif isinstance(node, list):
                for c in node:
                    walk(c)

        walk(desc)
        description = "\n".join(parts)
    else:
        description = str(desc or "")
    labels = fields.get("labels") or []
    status = (fields.get("status") or {}).get("name")
    assignee = fields.get("assignee") or {}
    return {
        "key": issue.get("key"),
        "summary": fields.get("summary"),
        "description": description,
        "labels": labels,
        "status": status,
        "assignee": assignee.get("displayName") or assignee.get("emailAddress"),
        "issuetype": (fields.get("issuetype") or {}).get("name"),
    }
