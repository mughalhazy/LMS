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

_UM_EXEMPT = {"/health"}

def _jwt_valid(auth_header: str | None) -> bool:
    """B08-004: HS256 JWT validation."""
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

from .service import UsageMeteringService
from .store import InMemoryMeteringStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryMeteringStore()
SERVICE = UsageMeteringService(STORE)


class MeteringHandler(BaseHTTPRequestHandler):
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

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) if length else b"{}")

    def _qs(self, key: str, default: str = "") -> str:
        return (parse_qs(urlparse(self.path).query).get(key) or [default])[0]

    def _base(self) -> str:
        return urlparse(self.path).path

    def do_GET(self) -> None:  # noqa: N802
        p = self._base()
        if p not in _UM_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        if p == "/health":
            self._send(200, {"status": "ok", "service": "usage-metering-service"}); return
        if "/tenants/" in p and "/capabilities/" in p:
            parts = p.split("/tenants/")[1].split("/capabilities/")
            tid, ck = parts[0], parts[1]
            self._send(*SERVICE.query_usage(
                tid, ck,
                from_date=self._qs("from"),
                to_date=self._qs("to"),
                granularity=self._qs("granularity", "daily"),
                metric_key=self._qs("metric_key", "request_count"),
            )); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            if p == "/api/v1/usage/events":
                events = body if isinstance(body, list) else [body]
                self._send(*SERVICE.ingest_events(events)); return
            if p == "/api/v1/usage/exports/daily":
                self._send(*SERVICE.export_daily(body.get("date", ""))); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8100) -> None:
    server = HTTPServer((host, port), MeteringHandler)
    print(f"Usage metering service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
