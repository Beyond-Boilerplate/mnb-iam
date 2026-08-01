#!/usr/bin/env python3
"""Meridian lesson verifier — pass/fail + gap report against a live IIQ lab.

Prefers IIQ HTTP APIs (SCIM Users, OOTB REST probes). Falls back to iiq console
for object.exists / identity checks when REST/SCIM cannot answer.

Identity checks are adaptive: persona logins in specs (``helen.ross``) also
resolve via HR ``userId`` (``MNB00001``), displayName, and email using
``lab-data/HRApplications.txt`` (or ``~/iiq-lab-data`` copies).

Usage:
  ./tools/iiq-verify/verify-lesson.sh 04
  python3 tools/iiq-verify/verify_lesson.py --lesson 04 --base-url http://localhost:8080/identityiq

Env:
  IIQ_BASE_URL   default http://localhost:8080/identityiq
  IIQ_USER       default spadmin
  IIQ_PASSWORD   default admin
  IIQ_HOME       for console fallback (Tomcat lab)
  IIQ_VERIFY_MODE  local | docker | k8s | auto
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPECS = Path(__file__).resolve().parent / "lesson-specs"
REPORT_DIR = Path.home() / "iiq-lab-evidence" / "verify"

# HR columns used to resolve persona login ↔ cube name (userId) ↔ displayName.
_HR_ID_KEYS = ("name", "userId", "displayName", "email", "firstname", "lastname")


def _hr_file_candidates() -> list[Path]:
    home_data = Path.home() / "iiq-lab-data"
    return [
        ROOT / "lab-data" / "HRApplications.txt",
        ROOT / "lab-data" / "hr" / "MNB-HR-Employees.csv",
        home_data / "HRApplications.txt",
        home_data / "hr" / "MNB-HR-Employees.csv",
        home_data / "hr" / "MNB-HR-Employees.txt",
    ]


class PersonaAliasIndex:
    """Map Meridian persona identifiers across naming schemes.

    Labs may name Identity cubes after HR ``userId`` (``MNB00001``), HR ``name``
    (``helen.ross``), or display name (``Helen Ross``). Specs keep the lesson
    persona; this index expands lookups so verify stays adaptive.
    """

    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []
        self.by_key: dict[str, list[dict[str, str]]] = {}
        self.source: str | None = None
        self._load()

    @staticmethod
    def _norm(value: str) -> str:
        return value.strip().lower()

    def _load(self) -> None:
        path = next((p for p in _hr_file_candidates() if p.is_file()), None)
        if path is None:
            return
        try:
            with path.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for raw in reader:
                    row = {k: (raw.get(k) or "").strip() for k in (reader.fieldnames or [])}
                    if not any(row.get(k) for k in ("name", "userId", "displayName")):
                        continue
                    self.rows.append(row)
                    for key in _HR_ID_KEYS:
                        val = row.get(key) or ""
                        if not val:
                            continue
                        self.by_key.setdefault(self._norm(val), []).append(row)
                    # "Helen" + "Ross" style composite (rare, but cheap)
                    first = row.get("firstname") or ""
                    last = row.get("lastname") or ""
                    if first and last:
                        self.by_key.setdefault(self._norm(f"{first} {last}"), []).append(row)
            self.source = str(path)
        except OSError:
            return

    def expand(self, name: str, alternate_names: list[str] | None = None) -> list[str]:
        """Ordered unique candidates for SCIM/REST/console identity lookup."""
        out: list[str] = []
        seen: set[str] = set()

        def add(value: str | None) -> None:
            if not value:
                return
            v = value.strip()
            if not v or v in seen:
                return
            seen.add(v)
            out.append(v)

        add(name)
        for alt in alternate_names or []:
            add(alt)

        matched_rows: list[dict[str, str]] = []
        seen_row_ids: set[int] = set()
        for cand in list(out):
            for row in self.by_key.get(self._norm(cand), []):
                rid = id(row)
                if rid in seen_row_ids:
                    continue
                seen_row_ids.add(rid)
                matched_rows.append(row)

        for row in matched_rows:
            # Prefer durable keys first for labs that used userId as native identity.
            add(row.get("userId"))
            add(row.get("name"))
            add(row.get("displayName"))
            add(row.get("email"))

        return out


_PERSONAS = PersonaAliasIndex()


class IIQClient:
    def __init__(self, base_url: str, user: str, password: str, mode: str) -> None:
        self.base = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.mode = mode
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self._auth = f"Basic {token}"
        self.transport_notes: list[str] = []
        self._console_cache: dict[str, str] = {}
        self.personas = _PERSONAS
        self._identity_resolve_cache: dict[str, tuple[str | None, dict[str, Any] | None, str]] = {}

    def http(self, method: str, path: str, accept: str = "application/json") -> tuple[int, str]:
        url = path if path.startswith("http") else f"{self.base}{path}"
        req = urllib.request.Request(
            url,
            method=method,
            headers={
                "Authorization": self._auth,
                "Accept": accept,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return e.code, body
        except Exception as e:  # noqa: BLE001
            return 0, str(e)

    def http_ok(self, path: str) -> tuple[bool, str]:
        # login.jsf often needs no auth
        url = f"{self.base}{path}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return 200 <= resp.status < 400, f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            return 200 <= e.code < 400, f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001
            return False, str(e)

    def scim_users(self, filter_expr: str | None = None, count: int = 1) -> tuple[bool, dict[str, Any]]:
        """Return (scim_ok, payload). scim_ok means HTTP 200 + JSON ListResponse."""
        path = f"/scim/v2/Users?count={count}"
        if filter_expr:
            path += f"&filter={urllib.parse.quote(filter_expr)}"
        code, body = self.http("GET", path)
        if code != 200:
            return False, {}
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False, {}
        if not isinstance(data, dict):
            return False, {}
        return True, data

    def scim_user(self, name: str) -> dict[str, Any] | None:
        matched, resource, _how = self.resolve_identity(name)
        if matched and resource:
            return resource
        return None

    def _scim_find_one(self, filter_expr: str) -> dict[str, Any] | None:
        ok, data = self.scim_users(filter_expr, count=1)
        if not ok:
            return None
        resources = data.get("Resources") or data.get("resources") or []
        if resources:
            self.transport_notes.append("scim")
            return resources[0]
        return None

    def resolve_identity(
        self,
        name: str,
        alternate_names: list[str] | None = None,
    ) -> tuple[str | None, dict[str, Any] | None, str]:
        """Resolve a persona to a live Identity via adaptive aliases.

        Returns (matched_userName_or_name, scim_or_rest_payload, how).
        """
        cache_key = "|".join([name] + list(alternate_names or []))
        if cache_key in self._identity_resolve_cache:
            return self._identity_resolve_cache[cache_key]

        candidates = self.personas.expand(name, alternate_names)
        scim_ok, _ = self.scim_users(count=1)

        for cand in candidates:
            if scim_ok:
                # 1) Exact IIQ identity name / userName (covers MNB00001 and helen.ross)
                resource = self._scim_find_one(f'userName eq "{cand}"')
                if resource is not None:
                    matched = str(resource.get("userName") or cand)
                    result = (matched, resource, f"scim userName={cand}")
                    self._identity_resolve_cache[cache_key] = result
                    return result

                # 2) Display name (lesson-04-style alternates like "Helen Ross")
                if " " in cand or (cand[:1].isupper() and "." not in cand):
                    resource = self._scim_find_one(f'displayName eq "{cand}"')
                    if resource is not None:
                        matched = str(resource.get("userName") or cand)
                        result = (matched, resource, f"scim displayName={cand}")
                        self._identity_resolve_cache[cache_key] = result
                        return result

                # 3) Email
                if "@" in cand:
                    resource = self._scim_find_one(f'emails.value eq "{cand}"')
                    if resource is not None:
                        matched = str(resource.get("userName") or cand)
                        result = (matched, resource, f"scim email={cand}")
                        self._identity_resolve_cache[cache_key] = result
                        return result

            # 4) REST probe by candidate name
            rest = self.rest_identity_probe(cand)
            if rest:
                matched = str(rest.get("name") or rest.get("userName") or cand)
                result = (matched, rest, f"rest name={cand}")
                self._identity_resolve_cache[cache_key] = result
                return result

        # 5) Console fallback only when SCIM is unavailable (avoid 40s miss storms)
        if not scim_ok:
            for cand in candidates:
                out = self.console(f'get Identity "{cand}"')
                low = out.lower()
                if "unknown object" in low or "no object" in low or "not found" in low:
                    continue
                if f'name="{cand}"' in out or "<Identity" in out:
                    result = (cand, {"_console_xml": out, "userName": cand}, f"console name={cand}")
                    self._identity_resolve_cache[cache_key] = result
                    return result

        detail = "not found via SCIM"
        if self.personas.source:
            detail += (
                f" (aliases from {Path(self.personas.source).name}: "
                f"{', '.join(candidates[:6])})"
            )
        result = (None, None, detail)
        self._identity_resolve_cache[cache_key] = result
        return result

    def rest_identity_probe(self, name: str) -> dict[str, Any] | None:
        # Probe a few common OOTB / plugin shapes; tolerate absence.
        for path in (
            f"/rest/identities/{urllib.parse.quote(name)}",
            f"/rest/identity/{urllib.parse.quote(name)}",
        ):
            code, body = self.http("GET", path)
            if code == 200 and body.strip().startswith(("{", "[")):
                try:
                    self.transport_notes.append("rest")
                    return json.loads(body)
                except json.JSONDecodeError:
                    continue
        return None

    def console(self, command: str) -> str:
        if command in self._console_cache:
            self.transport_notes.append("console-cache")
            return self._console_cache[command]
        if self.mode == "docker":
            out = self._console_docker(command)
        elif self.mode == "k8s":
            out = self._console_k8s(command)
        else:
            out = self._console_local(command)
        self._console_cache[command] = out
        return out

    def prefetch_console(self, commands: list[str]) -> None:
        """Run many iiq console commands in one JVM (big win in docker mode)."""
        pending = [c for c in dict.fromkeys(commands) if c not in self._console_cache]
        if not pending:
            return
        if len(pending) == 1 or self.mode not in ("docker", "k8s", "local"):
            for cmd in pending:
                self.console(cmd)
            return
        raw = self._console_session(pending)
        self.transport_notes.append("console-batch")
        chunks = self._split_console_session(raw, len(pending))
        for cmd, chunk in zip(pending, chunks):
            self._console_cache[cmd] = chunk

    @staticmethod
    def _split_console_session(raw: str, n: int) -> list[str]:
        # Interactive console prints a "> " prompt between commands.
        parts = re.split(r"(?m)^> ?", raw)
        # Drop banner-only first segment if it has no payload; keep aligned to n cmds.
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= n + 1 and re.search(r"iiq\.hostname", parts[0]):
            # banner + n results, or banner merged into first result
            if len(parts) == n + 1:
                return parts[1:]
        if len(parts) >= n:
            return parts[:n]
        # Fallback: give everyone the full transcript (object_exists still searches by name).
        return [raw] * n

    def _console_bin_cd(self) -> str:
        return (
            'cd "$IIQ_HOME/WEB-INF/bin" 2>/dev/null || '
            "cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin"
        )

    def _console_session(self, commands: list[str]) -> str:
        script = "\n".join(commands) + "\n"
        if self.mode == "docker":
            container = os.environ.get("IIQ_DOCKER_CONTAINER", "").strip()
            if container:
                proc = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "-i",
                        container,
                        "sh",
                        "-c",
                        f"{self._console_bin_cd()}; ./iiq console iiqBeans",
                    ],
                    input=script,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return (proc.stdout or "") + (proc.stderr or "")
            proc = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(ROOT / "docker-compose.iiq.yml"),
                    "exec",
                    "-T",
                    "identityiq",
                    "sh",
                    "-c",
                    f'{self._console_bin_cd()}; ./iiq console iiqBeans',
                ],
                input=script,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=300,
            )
            return (proc.stdout or "") + (proc.stderr or "")
        if self.mode == "k8s":
            ns = os.environ.get("NAMESPACE", "sailpoint")
            deploy = os.environ.get("IIQ_DEPLOYMENT", "identityiq")
            pod = subprocess.check_output(
                [
                    "kubectl",
                    "-n",
                    ns,
                    "get",
                    "pod",
                    "-l",
                    f"app.kubernetes.io/name={deploy}",
                    "-o",
                    "jsonpath={.items[0].metadata.name}",
                ],
                text=True,
            ).strip()
            proc = subprocess.run(
                [
                    "kubectl",
                    "-n",
                    ns,
                    "exec",
                    "-i",
                    pod,
                    "-c",
                    "identityiq",
                    "--",
                    "sh",
                    "-c",
                    "cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin && ./iiq console iiqBeans",
                ],
                input=script,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return (proc.stdout or "") + (proc.stderr or "")
        # local
        iiq_home = os.environ.get("IIQ_HOME", str(Path.home() / "iiq-lab/tomcat/webapps/identityiq"))
        bin_dir = Path(iiq_home) / "WEB-INF" / "bin"
        proc = subprocess.run(
            ["./iiq", "console", "iiqBeans"],
            cwd=str(bin_dir),
            input=script,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return (proc.stdout or "") + (proc.stderr or "")

    def _console_local(self, command: str) -> str:
        iiq_home = os.environ.get("IIQ_HOME", str(Path.home() / "iiq-lab/tomcat/webapps/identityiq"))
        bin_dir = Path(iiq_home) / "WEB-INF" / "bin"
        iiq = bin_dir / "iiq"
        if not iiq.exists():
            return f"ERROR: iiq console not found under {iiq_home}"
        self.transport_notes.append("console-local")
        proc = subprocess.run(
            ["./iiq", "console", "iiqBeans", "-c", command],
            cwd=str(bin_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return (proc.stdout or "") + (proc.stderr or "")

    def _console_docker(self, command: str) -> str:
        self.transport_notes.append("console-docker")
        safe = command.replace('"', '\\"')
        container = os.environ.get("IIQ_DOCKER_CONTAINER", "").strip()
        if container:
            # Preferred in Compose academy sidecar (docker.sock + named container)
            shell = (
                f"{self._console_bin_cd()}; "
                f'./iiq console iiqBeans -c "{safe}"'
            )
            # Plain `docker exec` (not `docker compose exec`): no -T flag.
            proc = subprocess.run(
                ["docker", "exec", container, "sh", "-c", shell],
                capture_output=True,
                text=True,
                timeout=180,
            )
            return (proc.stdout or "") + (proc.stderr or "")
        proc = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(ROOT / "docker-compose.iiq.yml"),
                "exec",
                "-T",
                "identityiq",
                "sh",
                "-c",
                f'{self._console_bin_cd()}; ./iiq console iiqBeans -c "{safe}"',
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        return (proc.stdout or "") + (proc.stderr or "")

    def _console_k8s(self, command: str) -> str:
        self.transport_notes.append("console-k8s")
        ns = os.environ.get("NAMESPACE", "sailpoint")
        deploy = os.environ.get("IIQ_DEPLOYMENT", "identityiq")
        safe = command.replace('"', '\\"')
        pod = subprocess.check_output(
            [
                "kubectl",
                "-n",
                ns,
                "get",
                "pod",
                "-l",
                f"app.kubernetes.io/name={deploy}",
                "-o",
                "jsonpath={.items[0].metadata.name}",
            ],
            text=True,
        ).strip()
        proc = subprocess.run(
            [
                "kubectl",
                "-n",
                ns,
                "exec",
                pod,
                "-c",
                "identityiq",
                "--",
                "sh",
                "-c",
                f'cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin && ./iiq console iiqBeans -c "{safe}"',
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        return (proc.stdout or "") + (proc.stderr or "")

    def object_exists(self, clazz: str, name: str) -> tuple[bool, str]:
        out = self.console(f'get {clazz} "{name}"')
        low = out.lower()
        if "unknown object" in low or "no object" in low or "not found" in low or out.strip().startswith("ERROR:"):
            return False, out.strip()[:400]
        if f'name="{name}"' in out or f"name='{name}'" in out or clazz in out:
            return True, "found via console"
        # empty-ish
        if len(out.strip()) < 20:
            return False, out.strip()[:400]
        return True, "console returned payload"

    def identity_xml(self, name: str, alternate_names: list[str] | None = None) -> str:
        matched, resource, how = self.resolve_identity(name, alternate_names)
        if resource:
            if isinstance(resource.get("_console_xml"), str):
                return str(resource["_console_xml"])
            return json.dumps(resource)
        if matched:
            return self.console(f'get Identity "{matched}"')
        return ""

    def identity_exists(
        self, name: str, alternate_names: list[str] | None = None
    ) -> tuple[bool, str]:
        matched, _resource, how = self.resolve_identity(name, alternate_names)
        if matched:
            return True, how
        return False, how

    def identity_count(self) -> tuple[int | None, str]:
        ok, data = self.scim_users(count=1)
        if ok and "totalResults" in data:
            try:
                self.transport_notes.append("scim-count")
                return int(data["totalResults"]), "scim totalResults"
            except (TypeError, ValueError):
                pass
        out = self.console("count Identity")
        m = re.search(r"(\d+)", out)
        if m:
            return int(m.group(1)), "console count Identity"
        return None, out.strip()[:200]

    def identity_attr(
        self, name: str, attr: str, alternate_names: list[str] | None = None
    ) -> tuple[str | None, str]:
        matched, resource, how = self.resolve_identity(name, alternate_names)
        if resource is None:
            return None, how or (
                "attribute not found on Identity (Link-only? run Lesson 05 maps + Refresh MNB Attributes)"
            )

        payload = (
            str(resource["_console_xml"])
            if isinstance(resource.get("_console_xml"), str)
            else json.dumps(resource)
        )

        # JSON SCIM / REST
        try:
            data = json.loads(payload)
            # SailPoint SCIM extension bag
            sp = data.get("urn:ietf:params:scim:schemas:sailpoint:1.0:User") or {}
            if attr == "email":
                emails = data.get("emails") or []
                if emails and isinstance(emails, list):
                    val = emails[0].get("value") if isinstance(emails[0], dict) else str(emails[0])
                    return val, how
            if attr in ("firstname", "firstName"):
                name_obj = data.get("name") or {}
                if isinstance(name_obj, dict) and name_obj.get("givenName"):
                    return str(name_obj["givenName"]), how
            if attr in ("lastname", "lastName"):
                name_obj = data.get("name") or {}
                if isinstance(name_obj, dict) and name_obj.get("familyName"):
                    return str(name_obj["familyName"]), how
            if attr in ("displayName",) and data.get("displayName"):
                return str(data["displayName"]), how
            if attr in data and data[attr] is not None:
                return str(data[attr]), how
            if isinstance(sp, dict) and attr in sp and sp[attr] is not None:
                return str(sp[attr]), how
            attrs = data.get("attributes") or data.get("Attributes") or {}
            if isinstance(attrs, dict) and attr in attrs and attrs[attr] is not None:
                return str(attrs[attr]), how
        except json.JSONDecodeError:
            pass

        # XML Identity attributes map (console)
        pat = rf'<entry key="{re.escape(attr)}" value="([^"]*)"'
        m = re.search(pat, payload)
        if m:
            return m.group(1), f"{how}+console-xml"

        # Last resort: fetch console XML for the matched cube name
        if matched:
            xml = self.console(f'get Identity "{matched}"')
            m = re.search(pat, xml)
            if m:
                return m.group(1), f"{how}+console-xml"

        return None, (
            "attribute not found on Identity (Link-only? run Lesson 05 maps + Refresh MNB Attributes)"
        )


def resolve_spec(lesson: str) -> Path:
    lesson = lesson.strip()
    # exact stem first (mid-16-apps-capstone, first-90-days, …)
    exact = SPECS / f"{lesson}.json"
    if exact.exists():
        return exact
    # numeric or stem prefix
    candidates = list(SPECS.glob(f"{lesson}-*.json"))
    if not candidates and lesson.isdigit():
        candidates = list(SPECS.glob(f"{int(lesson):02d}-*.json"))
    if not candidates:
        raise SystemExit(f"No lesson spec for '{lesson}' under {SPECS}")
    return sorted(candidates)[0]


def detect_mode() -> str:
    env = os.environ.get("IIQ_VERIFY_MODE", "auto").lower()
    if env != "auto":
        return env
    # Prefer docker if compose project running
    try:
        out = subprocess.run(
            ["docker", "compose", "-f", str(ROOT / "docker-compose.iiq.yml"), "ps", "-q", "identityiq"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        if out.returncode == 0 and out.stdout.strip():
            return "docker"
    except Exception:  # noqa: BLE001
        pass
    iiq_home = Path(os.environ.get("IIQ_HOME", str(Path.home() / "iiq-lab/tomcat/webapps/identityiq")))
    if (iiq_home / "WEB-INF/bin/iiq").exists():
        return "local"
    return "local"


def run_check(client: IIQClient, check: dict[str, Any]) -> dict[str, Any]:
    cid = check.get("id", "check")
    ctype = check["type"]
    msg = check.get("message", cid)
    result: dict[str, Any] = {
        "id": cid,
        "type": ctype,
        "message": msg,
        "status": "FAIL",
        "detail": "",
        "hint": check.get("softFailHint") or check.get("hint") or "",
    }

    try:
        if ctype == "http.ok":
            ok, detail = client.http_ok(check.get("path", "/login.jsf"))
            result["status"] = "PASS" if ok else "FAIL"
            result["detail"] = detail
        elif ctype == "host.file.exists":
            rel = check["path"]
            path = ROOT / rel if not Path(rel).is_absolute() else Path(rel)
            home = Path.home() / "iiq-lab-data" / Path(rel).name
            ok = path.exists() or home.exists()
            result["status"] = "PASS" if ok else "FAIL"
            result["detail"] = str(path if path.exists() else home)
        elif ctype == "object.exists":
            classes = [check["objectClass"]] + list(check.get("alternateClasses") or [])
            names = [check["name"]] + list(check.get("alternateNames") or [])
            ok = False
            detail = ""
            matched = ""
            for name in names:
                for clazz in classes:
                    ok, detail = client.object_exists(clazz, name)
                    if ok:
                        matched = name
                        break
                if ok:
                    break
            if ok:
                result["status"] = "PASS"
                if matched and matched != check["name"]:
                    result["detail"] = f"found as {matched!r} via console ({detail})"
                else:
                    result["detail"] = detail
            elif check.get("severity") or check.get("softFail"):
                result["status"] = "WARN"
                result["detail"] = detail
                result["hint"] = result["hint"] or "Soft check — document equivalent object name if yours differs."
            else:
                result["status"] = "FAIL"
                result["detail"] = detail
        elif ctype == "object.absent":
            ok, detail = client.object_exists(check["objectClass"], check["name"])
            # absent expected
            if not ok:
                result["status"] = "PASS"
                result["detail"] = "absent as expected"
            else:
                soft = check.get("severity")
                result["status"] = "WARN" if soft else "FAIL"
                result["detail"] = f"object unexpectedly present ({detail})"
                if soft:
                    result["hint"] = result["hint"] or "OK if leftover lab; wipe or delete before Lesson 04."
        elif ctype == "identity.exists":
            alts = list(check.get("alternateNames") or [])
            matched, _res, how = client.resolve_identity(check["name"], alts)
            if matched:
                result["status"] = "PASS"
                if matched != check["name"]:
                    result["detail"] = f"found as {matched!r} ({how})"
                else:
                    result["detail"] = how
            elif check.get("optional") or check.get("softFail"):
                result["status"] = "WARN"
                result["detail"] = how
                result["hint"] = result["hint"] or (
                    "Soft check — apply scenario runner + Aggregate MNB-HR if this persona is in scope."
                )
            else:
                result["status"] = "FAIL"
                result["detail"] = how
                result["hint"] = result["hint"] or (
                    "Run Aggregate MNB-HR (Lesson 04) then re-verify. "
                    "Cube name may be HR userId (MNB…) when identityAttribute=userId."
                )
        elif ctype == "identity.countMin":
            n, detail = client.identity_count()
            need = int(check["min"])
            if n is None:
                result["status"] = "FAIL"
                result["detail"] = detail
            else:
                result["status"] = "PASS" if n >= need else "FAIL"
                result["detail"] = f"count={n} (need >={need}); {detail}"
        elif ctype == "identity.attr":
            alts = list(check.get("alternateNames") or [])
            attr = check["attr"]
            matched, _res, how = client.resolve_identity(check["name"], alts)
            val, detail = client.identity_attr(check["name"], attr, alts)
            if val is None:
                if check.get("optional") or check.get("softFail"):
                    result["status"] = "WARN"
                    result["detail"] = detail
                    result["hint"] = (
                        result["hint"]
                        or "Promote Link→Identity maps (Lesson 05) and run Refresh MNB Attributes."
                    )
                else:
                    result["status"] = "FAIL"
                    result["detail"] = detail
                    result["hint"] = (
                        result["hint"]
                        or "Promote Link→Identity maps (Lesson 05) and run Refresh MNB Attributes."
                    )
            else:
                ok = True
                if "contains" in check:
                    ok = check["contains"] in val
                if "equals" in check:
                    ok = val == check["equals"]
                if "equalsIgnoreCase" in check:
                    ok = val.lower() == str(check["equalsIgnoreCase"]).lower()
                if ok:
                    result["status"] = "PASS"
                elif check.get("optional") or check.get("softFail"):
                    result["status"] = "WARN"
                else:
                    result["status"] = "FAIL"
                suffix = f" as {matched!r}" if matched and matched != check["name"] else ""
                result["detail"] = f"{attr}={val!r} via {detail or how}{suffix}"
        else:
            result["status"] = "FAIL"
            result["detail"] = f"unknown check type {ctype}"
    except Exception as e:  # noqa: BLE001
        result["status"] = "FAIL"
        result["detail"] = f"exception: {e}"

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify a Meridian academy lesson against live IIQ")
    ap.add_argument("--lesson", "-l", required=True, help="Lesson number or stem (e.g. 04 or 04-authoritative-hr-source)")
    ap.add_argument("--base-url", default=os.environ.get("IIQ_BASE_URL", "http://localhost:8080/identityiq"))
    ap.add_argument("--user", default=os.environ.get("IIQ_USER", "spadmin"))
    ap.add_argument("--password", default=os.environ.get("IIQ_PASSWORD", "admin"))
    ap.add_argument("--mode", default=None, help="local|docker|k8s|auto")
    ap.add_argument("--json-out", default=None, help="Write report JSON path")
    args = ap.parse_args()

    spec_path = resolve_spec(args.lesson)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    mode = args.mode or detect_mode()
    client = IIQClient(args.base_url, args.user, args.password, mode)

    checks = list(spec.get("checks", []))
    # One iiq console JVM for all object lookups (~40s once vs ~40s each).
    prefetch_cmds: list[str] = []
    for c in checks:
        ctype = c.get("type")
        if ctype == "object.exists":
            classes = [c["objectClass"]] + list(c.get("alternateClasses") or [])
            names = [c["name"]] + list(c.get("alternateNames") or [])
            for name in names:
                for clazz in classes:
                    prefetch_cmds.append(f'get {clazz} "{name}"')
        elif ctype == "object.absent":
            prefetch_cmds.append(f'get {c["objectClass"]} "{c["name"]}"')
    if prefetch_cmds:
        client.prefetch_console(prefetch_cmds)

    results = [run_check(client, c) for c in checks]
    fails = [r for r in results if r["status"] == "FAIL"]
    warns = [r for r in results if r["status"] == "WARN"]
    verdict = "PASS" if not fails else "FAIL"

    report = {
        "schema": "mnb-lesson-verify-report/v1",
        "lesson": spec.get("lesson"),
        "stem": spec.get("stem"),
        "title": spec.get("title"),
        "verdict": verdict,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "target": {"baseUrl": args.base_url, "mode": mode, "user": args.user},
        "transport": sorted(set(client.transport_notes)),
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "PASS"),
            "failed": len(fails),
            "warned": len(warns),
        },
        "gaps": [
            {
                "id": r["id"],
                "message": r["message"],
                "detail": r["detail"],
                "hint": r.get("hint") or "",
            }
            for r in fails
        ],
        "checks": results,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.json_out) if args.json_out else REPORT_DIR / f"lesson-{spec.get('lesson')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Human report
    print(f"Lesson {spec.get('lesson')} — {spec.get('title')}")
    print(f"Target: {args.base_url}  mode={mode}")
    print(f"Verdict: {verdict}")
    print("-" * 60)
    for r in results:
        mark = {"PASS": "✓", "FAIL": "✗", "WARN": "!"}.get(r["status"], "?")
        print(f"  [{mark}] {r['status']:4}  {r['message']}")
        if r["status"] != "PASS":
            print(f"         detail: {r['detail']}")
            if r.get("hint"):
                print(f"         hint:   {r['hint']}")
    print("-" * 60)
    if fails:
        print("Gaps to fix:")
        for g in report["gaps"]:
            print(f"  - {g['id']}: {g['message']} — {g['detail']}")
    print(f"Report: {out_path}")
    print("Track progress via Academy → Verify now (live IIQ only; JSON paste is disabled).")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
