#!/usr/bin/env python3
"""Serve docs/api with a same-origin reverse proxy to local IdentityIQ.

Swagger UI cannot call http://localhost:8080 from another origin (CORS).
This server exposes:

  http://127.0.0.1:8765/swagger/     → static API docs
  http://127.0.0.1:8765/identityiq/* → proxied to IIQ_BASE (default :8080)

Usage:
  ./docs/api/serve.py
  # or: IIQ_BASE=http://localhost:8080 python3 docs/api/serve.py --port 8765
"""

from __future__ import annotations

import argparse
import http.client
import http.server
import os
import socketserver
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_IIQ = os.environ.get("IIQ_BASE", "http://localhost:8080").rstrip("/")


class ApiDocsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, iiq_base: str = DEFAULT_IIQ, **kwargs):
        self.iiq_base = iiq_base.rstrip("/")
        super().__init__(*args, directory=directory or str(ROOT), **kwargs)

    def end_headers(self) -> None:
        # Allow Swagger (same origin) + opportunistic CORS for tooling
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Authorization, Content-Type, Accept, X-Requested-With",
        )
        self.send_header("Access-Control-Expose-Headers", "*")
        # Avoid stale swagger dropdown / OpenAPI after regenerations
        path = urllib.parse.urlparse(self.path).path
        if path.endswith((".html", ".yaml", ".yml", ".json", ".md")):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/identityiq/") or self.path == "/identityiq":
            self._proxy()
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        self._proxy_or_405()

    def do_PUT(self) -> None:  # noqa: N802
        self._proxy_or_405()

    def do_PATCH(self) -> None:  # noqa: N802
        self._proxy_or_405()

    def do_DELETE(self) -> None:  # noqa: N802
        self._proxy_or_405()

    def do_HEAD(self) -> None:  # noqa: N802
        if self.path.startswith("/identityiq/"):
            self._proxy()
            return
        super().do_HEAD()

    def _proxy_or_405(self) -> None:
        if self.path.startswith("/identityiq/") or self.path == "/identityiq":
            self._proxy()
            return
        self.send_error(405, "Method not allowed for static docs")

    def _proxy(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        target = f"{self.iiq_base}{parsed.path}"
        if parsed.query:
            target = f"{target}?{parsed.query}"

        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length > 0 else None

        headers = {}
        for key in ("Authorization", "Accept", "Content-Type", "X-Requested-With"):
            val = self.headers.get(key)
            if val:
                headers[key] = val
        if "Accept" not in headers:
            headers["Accept"] = "application/json, application/scim+json, */*"

        req = urllib.request.Request(target, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                self.send_response(resp.status)
                ctype = resp.headers.get("Content-Type")
                if ctype:
                    self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            ctype = e.headers.get("Content-Type") if e.headers else None
            if ctype:
                self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        except Exception as e:  # noqa: BLE001
            msg = f"Proxy error contacting {target}: {e}\n".encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def log_message(self, fmt: str, *args) -> None:
        sys_stderr = __import__("sys").stderr
        print("[%s] %s" % (self.log_date_time_string(), fmt % args), file=sys_stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=int(os.environ.get("API_DOCS_PORT", "8765")))
    ap.add_argument(
        "--bind",
        default=os.environ.get("API_DOCS_BIND", "127.0.0.1"),
        help="Bind address (use 0.0.0.0 in Docker)",
    )
    ap.add_argument("--iiq-base", default=DEFAULT_IIQ, help="IIQ origin, e.g. http://localhost:8080")
    args = ap.parse_args()

    iiq_base = args.iiq_base.rstrip("/")

    class Handler(ApiDocsHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), iiq_base=iiq_base, **kw)

    # Allow Ctrl+C to stop cleanly on macOS
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((args.bind, args.port), Handler) as httpd:
        print(f"API docs + IIQ proxy")
        print(f"  Swagger:  http://{args.bind}:{args.port}/swagger/")
        print(f"  Custom:   http://{args.bind}:{args.port}/swagger/  → Spec: Meridian Custom APIs (default)")
        print(f"  Proxy:    http://{args.bind}:{args.port}/identityiq/*  →  {iiq_base}/identityiq/*")
        print(f"  Tip: Authorize in Swagger with Basic auth (e.g. spadmin / lab password)")
        print(f"  Tip: Hard-refresh the page if Spec dropdown looks stale (Cmd+Shift+R)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
