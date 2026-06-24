from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

_FF_EXEMPT = {"/health"}

def _jwt_valid(auth_header: str | None) -> bool:
    """B07-001: validate HS256 JWT."""
    secret = os.getenv("JWT_SHARED_SECRET")
    if not secret:
        return True
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:]
    try:
        h, p, s = token.split(".")
        _pad = lambda x: x + "=" * ((4 - len(x) % 4) % 4)
        expected = _hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        received = base64.urlsafe_b64decode(_pad(s))
        if not _hmac.compare_digest(expected, received):
            return False
        payload = json.loads(base64.urlsafe_b64decode(_pad(p)))
        exp = payload.get("exp")
        return exp is None or float(exp) >= time.time()
    except Exception:
        return False

from .service import FeatureFlagService
from .store import InMemoryFlagStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryFlagStore()
SERVICE = FeatureFlagService(STORE)


class FlagHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass

    def _send(self, status: int, body: Dict[str, Any]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-API-Version", "v1")  # CAT-004
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) if length else b"{}")

    def _base(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:  # noqa: N802
        p = self._base()
        if p not in _FF_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        if p == "/health":
            self._send(200, {"status": "ok", "service": "feature-flag-service"}); return
        if p.startswith("/api/v1/flags/"):
            key = p.split("/api/v1/flags/")[1]
            self._send(*SERVICE.get_flag(key)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            if p == "/api/v1/flags":
                self._send(*SERVICE.upsert_flag(body)); return
            if p == "/api/v1/flags/is-enabled":
                self._send(*SERVICE.is_enabled(body)); return
            if p == "/api/v1/flags/resolve-many":
                self._send(*SERVICE.resolve_many(body)); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})

    def do_PUT(self) -> None:  # noqa: N802
        self.do_POST()


def run(host: str = "0.0.0.0", port: int = 8099) -> None:
    server = HTTPServer((host, port), FlagHandler)
    print(f"Feature flag service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
