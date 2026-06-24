from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

_OB_EXEMPT = {"/health"}

def _jwt_valid(auth_header: str | None) -> bool:
    """B07-004: validate HS256 JWT."""
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

from .service import OnboardingService

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


SERVICE = OnboardingService()


class OnboardingHandler(BaseHTTPRequestHandler):
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

    def _qs(self, key: str) -> str:
        return (parse_qs(urlparse(self.path).query).get(key) or [""])[0]

    def _base(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:  # noqa: N802
        p = self._base()
        if p not in _OB_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        if p == "/health":
            self._send(200, {"status": "ok", "service": "onboarding-service"}); return
        if p.startswith("/api/v1/onboarding/sessions/"):
            sid = p.split("/sessions/")[1]
            self._send(*SERVICE.get_status(sid)); return
        if p == "/api/v1/onboarding/defaults":
            self._send(*SERVICE.get_defaults(
                self._qs("segment_type") or "corp",
                self._qs("plan_type") or "basic",
                self._qs("country_code") or "US",
            )); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            if p == "/api/v1/onboarding/sessions":
                self._send(*SERVICE.start_onboarding(body)); return
            if "/sessions/" in p and p.endswith("/complete-step"):
                sid = p.split("/sessions/")[1].replace("/complete-step", "")
                self._send(*SERVICE.complete_step(sid, body.get("step_name", ""), body.get("data"))); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8103) -> None:
    server = HTTPServer((host, port), OnboardingHandler)
    print(f"Onboarding service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
