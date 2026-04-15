from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import Response

ALLOWED_ROLES = {"platform_admin", "tenant_admin", "instructor", "learner"}
_AUTH_SCHEME = HTTPBearer(auto_error=False)
_EXEMPT_PATHS = {"/health", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


@dataclass(frozen=True)
class AuthorizationContext:
    principal_id: str
    role: str
    permissions: set[str]
    tenant_id: str


def _parse_permissions(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {perm.strip() for perm in raw.split(",") if perm.strip()}


def _decode_base64url(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))


def _validate_hs256_jwt(token: str, secret: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed_jwt") from exc

    signed_part = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), signed_part, hashlib.sha256).digest()
    received_sig = _decode_base64url(signature_b64)
    if not hmac.compare_digest(expected_sig, received_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_signature")

    payload = json.loads(_decode_base64url(payload_b64).decode("utf-8"))
    exp = payload.get("exp")
    if exp is not None:
        import time

        if float(exp) < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired")
    return payload


def require_jwt(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_AUTH_SCHEME),
) -> None:
    if request.url.path in _EXEMPT_PATHS:
        return

    secret = os.getenv("JWT_SHARED_SECRET")
    if not secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="jwt_secret_not_configured")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")

    payload = _validate_hs256_jwt(credentials.credentials, secret)
    request.state.jwt_payload = payload


def apply_security_headers(app) -> None:
    @app.middleware("http")
    async def _security_headers(request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response


def get_authorization_context(
    x_principal_id: str = Header(..., alias="X-Principal-Id"),
    x_role: str = Header(..., alias="X-Role"),
    x_permissions: str | None = Header(None, alias="X-Permissions"),
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
) -> AuthorizationContext:
    if x_role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Unsupported role")
    return AuthorizationContext(
        principal_id=x_principal_id,
        role=x_role,
        permissions=_parse_permissions(x_permissions),
        tenant_id=x_tenant_id,
    )


def require_roles(*allowed_roles: str):
    def _dependency(ctx: AuthorizationContext = Depends(get_authorization_context)) -> AuthorizationContext:
        if ctx.role not in set(allowed_roles):
            raise HTTPException(status_code=403, detail="Role not allowed")
        return ctx

    return _dependency
