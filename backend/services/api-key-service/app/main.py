from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple

from .schemas import (
    ApiKeyAuthorizeRequest,
    ApiKeyCreateRequest,
    ApiKeyRotateRequest,
    ApiKeyUsageReportRequest,
)
from .service import ApiKeyService
from .store import InMemoryApiKeyStore


STORE = InMemoryApiKeyStore()
SERVICE = ApiKeyService(STORE)


class ApiKeyRequestHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: Dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
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
