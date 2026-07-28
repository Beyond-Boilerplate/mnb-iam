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
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "learn" / "dist"
VERIFY_PY = ROOT / "tools" / "iiq-verify" / "verify_lesson.py"
SPECS = ROOT / "tools" / "iiq-verify" / "lesson-specs"
REPORT_DIR = Path.home() / "iiq-lab-evidence" / "verify"

HOST = os.environ.get("ACADEMY_HOST", "127.0.0.1")
PORT = int(os.environ.get("ACADEMY_PORT", "4173"))
IIQ_BASE_URL = os.environ.get("IIQ_BASE_URL", "http://localhost:8080/identityiq")
IIQ_USER = os.environ.get("IIQ_USER", "spadmin")
IIQ_PASSWORD = os.environ.get("IIQ_PASSWORD", "admin")
IIQ_HOME = os.environ.get("IIQ_HOME", str(Path.home() / "iiq-lab/tomcat/webapps/identityiq"))
IIQ_VERIFY_MODE = os.environ.get("IIQ_VERIFY_MODE", "auto")


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
        if parsed.path == "/api/health":
            return self._json(200, {
                "ok": True,
                "iiqBaseUrl": IIQ_BASE_URL,
                "mode": IIQ_VERIFY_MODE,
            })
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "verify":
            return self._verify(parts[2])
        self.send_error(404, "Not found")

    def _verify(self, lesson: str) -> None:
        env = os.environ.copy()
        env["IIQ_BASE_URL"] = IIQ_BASE_URL
        env["IIQ_USER"] = IIQ_USER
        env["IIQ_PASSWORD"] = IIQ_PASSWORD
        env["IIQ_HOME"] = IIQ_HOME
        env["IIQ_VERIFY_MODE"] = IIQ_VERIFY_MODE
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
                    "verdict": "PASS" if proc.returncode == 0 else "FAIL",
                    "rawStdout": proc.stdout,
                    "rawStderr": proc.stderr,
                }
            return self._json(200, report)
        except subprocess.TimeoutExpired:
            return self._json(504, {"verdict": "FAIL", "error": "verify timed out"})
        except Exception as e:
            return self._json(500, {"verdict": "FAIL", "error": str(e)})

    def _load_report(self, lesson: str):
        specs = list(SPECS.glob(f"{lesson}-*.json"))
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
