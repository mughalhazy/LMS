from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple

from .schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenRequest,
    TokenValidationRequest,
)
from .secrets import SecretConfigurationError, get_required_secret
from .service import AuthService
from .store import InMemoryAuthStore


STORE = InMemoryAuthStore()
SERVICE = AuthService(STORE, signing_secret=get_required_secret("JWT_SHARED_SECRET"))


class AuthRequestHandler(BaseHTTPRequestHandler):
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

        if self.path == "/api/v1/auth/login":
            return SERVICE.login(LoginRequest(**body))

        if self.path == "/api/v1/auth/token":
            return SERVICE.issue_tokens(TokenRequest(**body))

        if self.path == "/api/v1/auth/sessions/validate":
            return SERVICE.validate_session(TokenValidationRequest(**body))

        if self.path == "/api/v1/auth/password/forgot":
            return SERVICE.forgot_password(ForgotPasswordRequest(**body))

        if self.path == "/api/v1/auth/password/reset":
            return SERVICE.reset_password(ResetPasswordRequest(**body))

        return 404, {"error": "not_found"}

    def do_POST(self) -> None:  # noqa: N802
        try:
            status, payload = self._dispatch()
            self._send(status, payload)
        except TypeError as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})
        except SecretConfigurationError as exc:
            self._send(503, {"error": "secret_not_configured", "detail": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8081) -> None:
    server = HTTPServer((host, port), AuthRequestHandler)
    print(f"Auth service listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
