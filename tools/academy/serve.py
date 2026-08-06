#!/usr/bin/env python3
"""Serve Meridian learn site locally and run lesson verification.

  python3 tools/academy/serve.py
  -> http://localhost:4173/

  POST /api/verify/<lesson>  -> runs verify_lesson.py, returns JSON
  GET  /api/health
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "learn" / "dist"
VERIFY_PY = ROOT / "tools" / "iiq-verify" / "verify_lesson.py"
SPECS = ROOT / "tools" / "iiq-verify" / "lesson-specs"
REPORT_DIR = Path.home() / "iiq-lab-evidence" / "verify"

# Enterprise Sandbox Path (lessons 201-255) — separate live verifier, no
# classic lesson-spec / REPORT_DIR involved. See tools/lab/enterprise/.
ENTERPRISE_VERIFY_PY = ROOT / "tools" / "lab" / "enterprise" / "verify_enterprise_lesson.py"
ENTERPRISE_SPECS = ROOT / "tools" / "lab" / "enterprise" / "lesson-asserts"
IIQ_MCP_URL = os.environ.get("IIQ_MCP_URL", "http://127.0.0.1:8766/mcp")
MCP_API_KEY = os.environ.get("MCP_API_KEY", os.environ.get("IIQ_MCP_API_KEY", "mnb-lab-mcp-key"))

HOST = os.environ.get("ACADEMY_HOST", "127.0.0.1")
PORT = int(os.environ.get("ACADEMY_PORT", "4173"))
IIQ_BASE_URL = os.environ.get("IIQ_BASE_URL", "http://localhost:8080/identityiq")
IIQ_USER = os.environ.get("IIQ_USER", "spadmin")
IIQ_PASSWORD = os.environ.get("IIQ_PASSWORD", "admin")
IIQ_HOME = os.environ.get("IIQ_HOME", str(Path.home() / "iiq-lab/tomcat/webapps/identityiq"))
IIQ_VERIFY_MODE = os.environ.get("IIQ_VERIFY_MODE", "auto")

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="7" fill="#0b5cab"/>
  <text x="16" y="21.5" text-anchor="middle" font-family="ui-sans-serif,system-ui,-apple-system,sans-serif" font-size="11" font-weight="700" fill="#ffffff">AC</text>
</svg>
""".encode("utf-8")


class AcademyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/api/health", "/healthz"):
            return self._json(200, {
                "ok": True,
                "iiqBaseUrl": IIQ_BASE_URL,
                "mode": IIQ_VERIFY_MODE,
            }) if parsed.path == "/api/health" else self._text(200, "ok")
        if parsed.path in ("/favicon.ico", "/favicon.svg"):
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(FAVICON_SVG)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(FAVICON_SVG)
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "verify":
            return self._verify(parts[2])
        self.send_error(404, "Not found")

    def _verify(self, lesson: str) -> None:
        if lesson.isdigit() and 201 <= int(lesson) <= 255:
            return self._verify_enterprise(lesson)
        env = os.environ.copy()
        env["IIQ_BASE_URL"] = IIQ_BASE_URL
        env["IIQ_USER"] = IIQ_USER
        env["IIQ_PASSWORD"] = IIQ_PASSWORD
        env["IIQ_HOME"] = IIQ_HOME
        env["IIQ_VERIFY_MODE"] = IIQ_VERIFY_MODE

        exact = SPECS / f"{lesson}.json"
        specs = [exact] if exact.exists() else []
        specs += list(SPECS.glob(f"{lesson}-*.json"))
        if lesson.isdigit():
            n = int(lesson)
            specs = list(SPECS.glob(f"{n:02d}-*.json")) + list(SPECS.glob(f"{n}-*.json")) + specs
        # de-dupe while preserving order
        seen = set()
        specs = [p for p in specs if not (p in seen or seen.add(p))]
        if not specs:
            return self._json(404, {
                "schema": "mnb-lesson-verify-report/v1",
                "verdict": "FAIL",
                "lesson": lesson,
                "error": f"No lesson spec for '{lesson}' under {SPECS}",
                "gaps": [{"id": "spec-missing", "message": "Lesson spec not found", "detail": lesson, "hint": ""}],
            })

        try:
            proc = subprocess.run(
                [sys.executable, str(VERIFY_PY), "--lesson", lesson, "--mode", IIQ_VERIFY_MODE],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )
            report = self._load_report(lesson)
            if report is None:
                report = {
                    "schema": "mnb-lesson-verify-report/v1",
                    "verdict": "PASS" if proc.returncode == 0 else "FAIL",
                    "lesson": lesson,
                    "rawStdout": proc.stdout,
                    "rawStderr": proc.stderr,
                    "gaps": [] if proc.returncode == 0 else [{
                        "id": "verify-cli",
                        "message": "Verifier failed without writing a report",
                        "detail": (proc.stderr or proc.stdout or "")[-800],
                        "hint": "Check IIQ is up and IIQ_HOME / IIQ_VERIFY_MODE",
                    }],
                }
            return self._json(200, report)
        except subprocess.TimeoutExpired:
            return self._json(504, {"schema": "mnb-lesson-verify-report/v1", "verdict": "FAIL", "error": "verify timed out"})
        except Exception as e:
            return self._json(500, {"schema": "mnb-lesson-verify-report/v1", "verdict": "FAIL", "error": str(e)})

    def _verify_enterprise(self, lesson: str) -> None:
        """Enterprise Sandbox Path (201-255): run verify_enterprise_lesson.py --json."""
        n = int(lesson)
        specs = list(ENTERPRISE_SPECS.glob(f"{n}-*.json")) or list(ENTERPRISE_SPECS.glob(f"{n:03d}-*.json"))
        if not specs:
            return self._json(404, {
                "schema": "mnb-lesson-verify-report/v1",
                "verdict": "FAIL",
                "lesson": lesson,
                "verifyMode": "paperwork",
                "error": f"No Enterprise Sandbox assert spec for lesson {lesson} under {ENTERPRISE_SPECS}",
                "gaps": [{
                    "id": "spec-missing",
                    "message": "Enterprise Sandbox assert spec not found",
                    "detail": f"lesson {lesson} has no JSON under tools/lab/enterprise/lesson-asserts/",
                    "hint": "Author a lesson-assert spec, or use Mark binder complete for now.",
                }],
            })

        env = os.environ.copy()
        env["IIQ_BASE_URL"] = IIQ_BASE_URL
        env["IIQ_USER"] = IIQ_USER
        env["IIQ_PASSWORD"] = IIQ_PASSWORD
        env.setdefault("IIQ_MCP_URL", IIQ_MCP_URL)
        env.setdefault("MCP_API_KEY", MCP_API_KEY)

        try:
            proc = subprocess.run(
                [sys.executable, str(ENTERPRISE_VERIFY_PY), lesson, "--json"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=180,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return self._json(504, {
                "schema": "mnb-lesson-verify-report/v1", "verdict": "FAIL",
                "lesson": lesson, "verifyMode": "enterprise", "error": "verify timed out",
            })
        except Exception as e:  # noqa: BLE001
            return self._json(500, {
                "schema": "mnb-lesson-verify-report/v1", "verdict": "FAIL",
                "lesson": lesson, "verifyMode": "enterprise", "error": str(e),
            })

        try:
            payload = json.loads(proc.stdout)
        except (json.JSONDecodeError, ValueError):
            return self._json(500, {
                "schema": "mnb-lesson-verify-report/v1",
                "verdict": "FAIL",
                "lesson": lesson,
                "verifyMode": "enterprise",
                "error": "verify_enterprise_lesson.py did not return JSON",
                "rawStdout": (proc.stdout or "")[-2000:],
                "rawStderr": (proc.stderr or "")[-2000:],
            })

        gaps = [
            {
                "id": c.get("id", ""),
                "message": c.get("message", ""),
                "detail": c.get("detail", ""),
                "hint": "Soft check — does not fail the lesson." if c.get("soft") else "",
            }
            for c in payload.get("checks", [])
            if c.get("status") == "FAIL"
        ]
        report = {
            "schema": "mnb-lesson-verify-report/v1",
            "lesson": lesson,
            "verifyMode": "enterprise",
            "verdict": payload.get("verdict", "FAIL"),
            "checkedAt": datetime.now(timezone.utc).isoformat(),
            "summary": payload.get("summary", {}),
            "gaps": gaps,
            "checks": payload.get("checks", []),
        }
        return self._json(200, report)

    def _load_report(self, lesson: str):
        exact = SPECS / f"{lesson}.json"
        specs = [exact] if exact.exists() else []
        specs += list(SPECS.glob(f"{lesson}-*.json"))
        if lesson.isdigit():
            specs = list(SPECS.glob(f"{int(lesson):02d}-*.json")) + specs
        if specs:
            spec_obj = json.loads(specs[0].read_text())
            report_path = REPORT_DIR / f"lesson-{spec_obj['lesson']}.json"
            if report_path.exists():
                return json.loads(report_path.read_text())
        guess = REPORT_DIR / f"lesson-{lesson}.json"
        if guess.exists():
            return json.loads(guess.read_text())
        return None

    def _text(self, status: int, body: str) -> None:
        raw = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)


def main() -> None:
    if not DIST.exists():
        print(f"Building learn site into {DIST} ...")
        subprocess.check_call([sys.executable, str(ROOT / "learn" / "build.py")], cwd=str(ROOT))
    if not DIST.exists():
        raise SystemExit(f"Missing learn dist at {DIST}. Run: python3 learn/build.py")

    print(f"Meridian academy: http://{HOST}:{PORT}/")
    print(f"IIQ target: {IIQ_BASE_URL} (mode={IIQ_VERIFY_MODE})")
    print(f"Verify API: POST http://{HOST}:{PORT}/api/verify/<lesson>")
    server = ThreadingHTTPServer((HOST, PORT), AcademyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down")


if __name__ == "__main__":
    main()
