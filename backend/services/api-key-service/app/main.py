from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple

# /authorize is the API key verification endpoint — exempt from JWT (it IS the auth mechanism)
_AK_JWT_EXEMPT = {"/health", "/metrics", "/api/v1/integrations/api-keys/authorize"}

def _jwt_valid(auth_header: str | None) -> bool:
    """B07-005: validate HS256 JWT."""
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

from .schemas import (
    ApiKeyAuthorizeRequest,
    ApiKeyCreateRequest,
    ApiKeyRotateRequest,
    ApiKeyUsageReportRequest,
)
from .service import ApiKeyService
from .store import InMemoryApiKeyStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()



STORE = InMemoryApiKeyStore()
SERVICE = ApiKeyService(STORE)


class ApiKeyRequestHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: Dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-API-Version", "v1")  # CAT-004
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _dispatch(self) -> Tuple[int, Dict[str, Any]]:
        body = self._read_json()

        if self.path == "/api/v1/integrations/api-keys":
            return SERVICE.create_api_key(ApiKeyCreateRequest(**body))

        if self.path == "/api/v1/integrations/api-keys/rotate":
            return SERVICE.rotate_api_key(ApiKeyRotateRequest(**body))

        if self.path == "/api/v1/integrations/api-keys/authorize":
            return SERVICE.authorize(ApiKeyAuthorizeRequest(**body))

        if self.path == "/api/v1/integrations/api-keys/usage":
            return SERVICE.usage_report(ApiKeyUsageReportRequest(**body))

        return 404, {"error": "not_found"}

    def do_POST(self) -> None:  # noqa: N802
        # B07-005: JWT required on create/rotate/usage; /authorize is exempt
        if self.path not in _AK_JWT_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            status, payload = self._dispatch()
            self._send(status, payload)
        except TypeError as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "api-key-service"})
            return
        if self.path == "/metrics":
            self._send(200, {"service": "api-key-service", "service_up": 1})
            return
        self._send(404, {"error": "not_found"})


def run(host: str = "0.0.0.0", port: int = 8086) -> None:
    server = HTTPServer((host, port), ApiKeyRequestHandler)
    print(f"API key service listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
