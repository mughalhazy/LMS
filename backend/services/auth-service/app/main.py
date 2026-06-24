from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple

from .schemas import (
    AdminResetPasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenRequest,
    TokenValidationRequest,
)
from .secrets import SecretConfigurationError, get_required_secret
from .security import get_jwks
from .service import AuthService
from .store_db import SQLiteAuthStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()



STORE = SQLiteAuthStore()
SERVICE = AuthService(STORE, signing_secret=get_required_secret("JWT_SHARED_SECRET"))


class AuthRequestHandler(BaseHTTPRequestHandler):
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

        # AUD-001: spec §4.1 — /sessions/login is canonical; /login kept as compat alias
        if self.path in ("/api/v2/auth/sessions/login", "/api/v2/auth/login"):
            return SERVICE.login(LoginRequest(**body))

        # AUD-052/002: spec §4.2 — proper refresh token flow at /tokens/refresh
        if self.path in ("/api/v2/auth/tokens/refresh", "/api/v2/auth/token/refresh"):
            return SERVICE.refresh_token(RefreshTokenRequest(**body))

        # Legacy session-based token issuance (kept for backward compat)
        if self.path == "/api/v2/auth/token":
            return SERVICE.issue_tokens(TokenRequest(**body))

        if self.path == "/api/v2/auth/sessions/validate":
            return SERVICE.validate_session(TokenValidationRequest(**body))

        if self.path in ("/api/v2/auth/password/forgot", "/api/v2/auth/password/reset/request"):
            return SERVICE.forgot_password(ForgotPasswordRequest(**body))

        if self.path in ("/api/v2/auth/password/reset", "/api/v2/auth/password/reset/confirm"):
            return SERVICE.reset_password(ResetPasswordRequest(**body))

        # Spec: auth-service-spec.md §2.1 — admin-initiated password reset
        if (
            self.path.startswith("/api/v2/admin/users/")
            and self.path.endswith("/reset-password")
        ):
            parts = self.path.split("/")
            # path: /api/v2/admin/users/{user_id}/reset-password → parts[5]
            if len(parts) >= 7:
                user_id = parts[5]
                return SERVICE.admin_reset_password(user_id, AdminResetPasswordRequest(**body))

        # CAT-005: POST /sessions/{session_id}/revoke — targeted session revocation
        if self.path.startswith("/api/v2/auth/sessions/") and self.path.endswith("/revoke"):
            parts = self.path.split("/")
            session_id = parts[-2] if len(parts) >= 7 else ""
            import types as _t
            _req = _t.SimpleNamespace(session_id=session_id, tenant_id=body.get("tenant_id", ""), user_id="")
            return SERVICE.logout(_req)

        # CAT-005: POST /sessions/revoke-all — alias for logout_all
        if self.path == "/api/v2/auth/sessions/revoke-all":
            import types as _t
            _req = _t.SimpleNamespace(tenant_id=body.get("tenant_id", ""), user_id=body.get("user_id", ""))
            return SERVICE.logout_all(_req)

        # CAT-006: POST /password/policy/validate — validate password strength against policy
        if self.path == "/api/v2/auth/password/policy/validate":
            password = body.get("password", "")
            violations = []
            if len(password) < 8:
                violations.append("min_length_8")
            if not any(c.isupper() for c in password):
                violations.append("requires_uppercase")
            if not any(c.isdigit() for c in password):
                violations.append("requires_digit")
            if violations:
                return 422, {"valid": False, "violations": violations}
            return 200, {"valid": True, "violations": []}

        # Spec: auth-service-spec.md §4.3 — single session logout
        if self.path == "/api/v2/auth/sessions/logout":
            from .schemas import LoginRequest as _Req
            import types as _types
            _req = _types.SimpleNamespace(
                session_id=body.get("session_id", ""),
                tenant_id=body.get("tenant_id", ""),
                user_id=body.get("user_id", ""),
            )
            return SERVICE.logout(_req)

        # Spec: auth-service-spec.md §4.4 — logout all sessions (AUD-003: underscore alias)
        if self.path in ("/api/v2/auth/sessions/logout_all", "/api/v2/auth/sessions/logout-all"):
            import types as _types
            _req = _types.SimpleNamespace(
                tenant_id=body.get("tenant_id", ""),
                user_id=body.get("user_id", ""),
            )
            return SERVICE.logout_all(_req)

        # Spec: auth-service-spec.md §8 — SSO initiation (SAML/OIDC pre-auth flow)
        if self.path == "/api/v2/auth/sso/initiate":
            return SERVICE.sso_initiate(
                tenant_id=body.get("tenant_id", ""),
                provider_type=body.get("provider_type", ""),
                redirect_uri=body.get("redirect_uri", ""),
                correlation_id=body.get("correlation_id"),
            )

        # Spec: auth-service-spec.md §8 — SSO callback (exchange assertion for platform session)
        if self.path == "/api/v2/auth/sso/callback":
            return SERVICE.sso_callback(
                tenant_id=body.get("tenant_id", ""),
                provider_type=body.get("provider_type", ""),
                code_or_assertion=body.get("code_or_assertion", ""),
                correlation_id=body.get("correlation_id", ""),
            )

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

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "auth-service"})
            return
        if self.path == "/metrics":
            self._send(200, {"service": "auth-service", "service_up": 1})
            return
        # Spec: auth-service-spec.md §4.8 — JWKS public key endpoint (RS256, FA-004a)
        if self.path == "/.well-known/jwks.json":
            self._send(200, get_jwks())
            return
        # Spec: auth-service-spec.md §8 — tenant discovery by email domain for pre-login SSO flow
        if self.path.startswith("/api/v2/auth/tenant"):
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            domain = params.get("domain", [None])[0]
            if not domain:
                self._send(400, {"error": "domain_required"})
                return
            status, payload = SERVICE.discover_tenant(domain)
            self._send(status, payload)
            return
        # CAT-005: GET /sessions/{session_id} — fetch session metadata
        if self.path.startswith("/api/v2/auth/sessions/"):
            from urllib.parse import urlparse as _up
            path_part = _up(self.path).path
            parts = path_part.rstrip("/").split("/")
            # /api/v2/auth/sessions/{session_id}
            if len(parts) >= 6 and parts[5] not in ("login", "logout", "logout_all", "logout-all", "validate", "revoke-all"):
                session_id = parts[5]
                session = STORE.get_session(session_id)
                if session is None:
                    self._send(404, {"error": "session_not_found"})
                else:
                    self._send(200, {
                        "session_id": session.session_id,
                        "user_id": session.user_id,
                        "tenant_id": session.tenant_id,
                        "issued_at": session.issued_at.isoformat(),
                        "expires_at": session.expires_at.isoformat(),
                        "state": "revoked" if session.revoked else "active",
                    })
                return
        self._send(404, {"error": "not_found"})


def run(host: str = "0.0.0.0", port: int = 8081) -> None:
    server = HTTPServer((host, port), AuthRequestHandler)
    print(f"Auth service listening on http://{host}:{port}")
    server.serve_forever()


# GAP-004 / RISK-011: manifest entry is app.main:app (uvicorn ASGI).
# auth-service uses stdlib HTTPServer; this shim makes the module importable
# as app.main:app. Start with: python -m backend.services.auth-service.app.main
# or uvicorn backend.services.auth-service.app.main:app (routes via FastAPI below).
from fastapi import FastAPI as _FastAPI, Request as _Request
from fastapi.responses import JSONResponse as _JSONResponse
import asyncio as _asyncio

app = _FastAPI(title="Auth Service", version="2.0.0", docs_url=None, openapi_url=None)


@app.api_route("/api/v2/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.api_route("/.well-known/jwks.json", methods=["GET"])
@app.api_route("/health", methods=["GET"])
@app.api_route("/metrics", methods=["GET"])
async def _asgi_dispatch(request: _Request, path: str = "") -> _JSONResponse:
    """ASGI shim: delegates to stdlib AuthRequestHandler logic via SERVICE."""
    method = request.method.upper()
    full_path = str(request.url.path)
    try:
        body_bytes = await request.body()
        body: dict = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        body = {}

    from .schemas import (LoginRequest, RefreshTokenRequest, ResetPasswordRequest,
                          ForgotPasswordRequest, TokenValidationRequest)

    if full_path == "/health":
        return _JSONResponse({"status": "ok", "service": "auth-service"})
    if full_path == "/metrics":
        return _JSONResponse({"service": "auth-service", "service_up": 1})
    if full_path == "/.well-known/jwks.json":
        from .security import get_jwks
        return _JSONResponse(get_jwks())
    if full_path in ("/api/v2/auth/sessions/login", "/api/v2/auth/login") and method == "POST":
        status_code, result = SERVICE.login(LoginRequest(**body))
        return _JSONResponse(result, status_code=status_code)
    if full_path in ("/api/v2/auth/tokens/refresh", "/api/v2/auth/token/refresh") and method == "POST":
        status_code, result = SERVICE.refresh_token(RefreshTokenRequest(**body))
        return _JSONResponse(result, status_code=status_code)
    if full_path == "/api/v2/auth/sessions/validate" and method == "POST":
        status_code, result = SERVICE.validate_token(TokenValidationRequest(**body))
        return _JSONResponse(result, status_code=status_code)
    if full_path == "/api/v2/auth/password/forgot" and method == "POST":
        status_code, result = SERVICE.forgot_password(ForgotPasswordRequest(**body))
        return _JSONResponse(result, status_code=status_code)
    if full_path == "/api/v2/auth/password/reset" and method == "POST":
        status_code, result = SERVICE.reset_password(ResetPasswordRequest(**body))
        return _JSONResponse(result, status_code=status_code)
    return _JSONResponse({"error": "not_found"}, status_code=404)


if __name__ == "__main__":
    run()
