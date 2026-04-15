from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Dict, Tuple


class SecurityError(Exception):
    """Domain-specific exception."""


def hash_password(password: str, salt: str | None = None) -> str:
    resolved_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), resolved_salt.encode("utf-8"), 200_000)
    return f"{resolved_salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt, _ = password_hash.split("$", 1)
    return hmac.compare_digest(hash_password(password, salt), password_hash)


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")


def _b64url_decode(payload: str) -> bytes:
    pad = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + pad)


def issue_token(secret: str, claims: Dict[str, object], ttl_seconds: int) -> str:
    now = int(time.time())
    envelope = dict(claims)
    envelope["iat"] = now
    envelope["exp"] = now + ttl_seconds

    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(envelope, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_sig = _b64url_encode(signature)
    return f"{encoded_header}.{encoded_payload}.{encoded_sig}"


def validate_token(secret: str, token: str) -> Tuple[bool, Dict[str, object] | None, str | None]:
    try:
        encoded_header, encoded_payload, encoded_sig = token.split(".")
    except ValueError:
        return False, None, "invalid_format"

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()

    if not hmac.compare_digest(_b64url_encode(expected_sig), encoded_sig):
        return False, None, "invalid_signature"

    try:
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
    except Exception:
        return False, None, "invalid_payload"

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return False, None, "expired"

    return True, payload, None
