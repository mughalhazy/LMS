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

_EC_EXEMPT = {"/health"}

def _jwt_valid(auth_header: str | None) -> bool:
    """B07-002: validate HS256 JWT."""
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

from .service import EnterpriseControlService

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


SERVICE = EnterpriseControlService()


class EnterpriseHandler(BaseHTTPRequestHandler):
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
        if p not in _EC_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        tid = self.headers.get("X-Tenant-Id", "")
        if p == "/health":
            self._send(200, {"status": "ok", "service": "enterprise-control-service"}); return
        if p == "/api/v1/enterprise/compliance":
            self._send(*SERVICE.get_compliance(tid)); return
        if p == "/api/v1/enterprise/integrations":
            self._send(*SERVICE.list_integrations(tid)); return
        if p == "/api/v1/enterprise/rbac/policies":
            self._send(*SERVICE.get_rbac_policies(tid)); return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        p = self._base()
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            body = self._read_json()
            tid = body.get("tenant_id") or self.headers.get("X-Tenant-Id", "")
            if p == "/api/v1/enterprise/compliance":
                self._send(*SERVICE.update_compliance(tid, body)); return
            if p == "/api/v1/enterprise/integrations":
                self._send(*SERVICE.register_integration(body)); return
            if p == "/api/v1/enterprise/rbac/policies":
                self._send(*SERVICE.set_rbac_policy(body)); return
            self._send(404, {"error": "not_found"})
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8104) -> None:
    server = HTTPServer((host, port), EnterpriseHandler)
    print(f"Enterprise control service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
