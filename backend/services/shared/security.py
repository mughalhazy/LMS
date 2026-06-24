"""Shared JWT validation utilities — supports both RS256 and HS256.

R-012 migration: consuming services must accept RS256 tokens issued by auth-service
when JWT_PRIVATE_KEY is configured there. Algorithm is determined from the JWT header
`alg` claim so the same validation function works during HS256→RS256 rollout.

Usage in each service's security.py:
    from backend.services.shared.security import (
        require_jwt,
        require_tenant_scope,
        apply_security_headers,
    )
    # Replace the local implementations with the shared ones, or delegate:
    #   _validate_rs256_jwt, _validate_hs256_jwt, require_jwt already imported.

Architecture references:
    ARCH_04 §Security Isolation
    R-012 / GAP-008: RS256/HS256 mismatch fix
    AUTH_AND_TENANCY_CONTRACT.md §JWT Signing
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import Response

_AUTH_SCHEME = HTTPBearer(auto_error=False)


# ------------------------------------------------------------------ #
# Base64-url helpers                                                   #
# ------------------------------------------------------------------ #

def _b64url_decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))


# ------------------------------------------------------------------ #
# HS256 validation (existing path — unchanged)                         #
# ------------------------------------------------------------------ #

def _validate_hs256_jwt(token: str, secret: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed_jwt") from exc

    signed_part = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), signed_part, hashlib.sha256).digest()
    received_sig = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected_sig, received_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_signature")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    exp = payload.get("exp")
    if exp is not None and float(exp) < time.time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired")
    return payload


# ------------------------------------------------------------------ #
# RS256 validation (R-012 — new path)                                  #
# ------------------------------------------------------------------ #

def _validate_rs256_jwt(token: str, public_key_pem: str) -> dict[str, Any]:
    """Validate an RS256-signed JWT using the RSA public key in PEM format.

    JWT_PUBLIC_KEY env var must contain the PEM-encoded public key matching
    the private key used by auth-service (JWT_PRIVATE_KEY or ephemeral key).

    Requires the `cryptography` package (already a dependency of auth-service).
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding as _padding
        from cryptography.exceptions import InvalidSignature
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="rs256_dependency_missing",
        ) from exc

    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed_jwt") from exc

    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = _b64url_decode(signature_b64)

    try:
        pub_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        pub_key.verify(sig, msg, _padding.PKCS1v15(), hashes.SHA256())  # type: ignore[arg-type]
    except InvalidSignature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_signature")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="jwt_validation_error") from exc

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    exp = payload.get("exp")
    if exp is not None and float(exp) < time.time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired")
    return payload


# ------------------------------------------------------------------ #
# Algorithm-aware JWT dispatch                                         #
# ------------------------------------------------------------------ #

def _peek_jwt_alg(token: str) -> str:
    """Decode the JWT header to read the `alg` claim without validating."""
    try:
        header_b64 = token.split(".")[0]
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        return str(header.get("alg", "HS256"))
    except Exception:
        return "HS256"


def validate_jwt(token: str) -> dict[str, Any]:
    """Validate a JWT using the algorithm declared in its header.

    Algorithm routing (R-012):
      RS256 → validate with JWT_PUBLIC_KEY env var (PEM)
      HS256 → validate with JWT_SHARED_SECRET env var

    During rollout both env vars may be set; the alg claim in the JWT
    determines which path is taken so HS256 and RS256 tokens coexist.
    """
    alg = _peek_jwt_alg(token)
    if alg == "RS256":
        public_key_pem = os.getenv("JWT_PUBLIC_KEY")
        if not public_key_pem:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="jwt_public_key_not_configured",
            )
        return _validate_rs256_jwt(token, public_key_pem)
    else:
        secret = os.getenv("JWT_SHARED_SECRET")
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="jwt_secret_not_configured",
            )
        return _validate_hs256_jwt(token, secret)


# ------------------------------------------------------------------ #
# FastAPI dependencies (drop-in replacement for per-service security.py)
# ------------------------------------------------------------------ #

def require_jwt(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_AUTH_SCHEME),
    exempt_paths: frozenset[str] = frozenset({
        "/health", "/metrics", "/openapi.json", "/docs",
        "/docs/oauth2-redirect", "/redoc", "/.well-known/jwks.json",
    }),
) -> None:
    """FastAPI dependency — validates JWT on every non-exempt request.

    Supports RS256 (when JWT_PUBLIC_KEY is set) and HS256 (JWT_SHARED_SECRET).
    Algorithm is determined from the JWT header `alg` claim (R-012).
    """
    if request.url.path in exempt_paths:
        return
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")
    request.state.jwt_payload = validate_jwt(credentials.credentials)


def require_tenant_scope(
    request: Request,
    x_tenant_id: str | None = Header(None, alias="X-Tenant-Id"),
) -> None:
    """FastAPI dependency — enforces JWT tenant_id matches X-Tenant-Id header."""
    exempt_paths = {"/health", "/metrics", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    if request.url.path in exempt_paths:
        return
    payload = getattr(request.state, "jwt_payload", {})
    claim_tenant = payload.get("tenant_id")
    if not x_tenant_id or not claim_tenant or claim_tenant != x_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="tenant_mismatch")


def apply_security_headers(app: Any) -> None:
    """Add defensive security headers to every FastAPI response (ARCH_04)."""
    @app.middleware("http")
    async def _security_headers(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response
