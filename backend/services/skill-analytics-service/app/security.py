from __future__ import annotations
import base64, hashlib, hmac, json, os
from typing import Any
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import Response

_AUTH_SCHEME = HTTPBearer(auto_error=False)
_EXEMPT_PATHS = {"/health", "/metrics", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}

def _decode_b64url(v: str) -> bytes:
    return base64.urlsafe_b64decode(v + "=" * ((4 - len(v) % 4) % 4))

def _validate_hs256_jwt(token: str, secret: str) -> dict[str, Any]:
    try:
        h, p, s = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed_jwt") from exc
    signed = f"{h}.{p}".encode()
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _decode_b64url(s)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_signature")
    payload = json.loads(_decode_b64url(p))
    exp = payload.get("exp")
    if exp is not None:
        import time
        if float(exp) < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired")
    return payload


# R-012: RS256 validation path — used when auth-service issues RS256 tokens
def _validate_rs256_jwt(token: str, public_key_pem: str) -> dict[str, Any]:
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding as _padding
        from cryptography.exceptions import InvalidSignature
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="rs256_dependency_missing") from exc
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed_jwt") from exc
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = _decode_b64url(signature_b64)
    try:
        pub_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        pub_key.verify(sig, msg, _padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_signature")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="jwt_validation_error") from exc
    payload = json.loads(_decode_b64url(payload_b64).decode("utf-8"))
    exp = payload.get("exp")
    if exp is not None:
        import time
        if float(exp) < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired")
    return payload

def require_jwt(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(_AUTH_SCHEME)) -> None:
    if request.url.path in _EXEMPT_PATHS:
        return
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")

    token = credentials.credentials
    # R-012: peek at alg claim to route RS256 vs HS256
    try:
        alg = json.loads(_decode_b64url(token.split(".")[0]).decode()).get("alg", "HS256")
    except Exception:
        alg = "HS256"

    if alg == "RS256":
        public_key_pem = os.getenv("JWT_PUBLIC_KEY")
        if not public_key_pem:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="jwt_public_key_not_configured")
        request.state.jwt_payload = _validate_rs256_jwt(token, public_key_pem)
    else:
        secret = os.getenv("JWT_SHARED_SECRET")
        if not secret:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="jwt_secret_not_configured")
        request.state.jwt_payload = _validate_hs256_jwt(token, secret)

def apply_security_headers(app) -> None:
    @app.middleware("http")
    async def _sec_hdrs(request: Request, call_next):
        r: Response = await call_next(request)
        r.headers["X-Content-Type-Options"] = "nosniff"
        r.headers["X-Frame-Options"] = "DENY"
        r.headers["Cache-Control"] = "no-store"
        return r
