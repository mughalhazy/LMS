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
    """Argon2id (spec §9, FA-004b). Falls back to PBKDF2 only if argon2-cffi unavailable."""
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
        # argon2-cffi encodes salt internally; prefix with 'argon2:' to distinguish from legacy hashes
        return "argon2:" + ph.hash(password)
    except ImportError:
        resolved_salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), resolved_salt.encode("utf-8"), 200_000)
        return f"{resolved_salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify Argon2id hash (new) or PBKDF2 hash (legacy migration path)."""
    if password_hash.startswith("argon2:"):
        try:
            from argon2 import PasswordHasher
            from argon2.exceptions import VerifyMismatchError
            ph = PasswordHasher()
            try:
                return ph.verify(password_hash[len("argon2:"):], password)
            except VerifyMismatchError:
                return False
        except ImportError:
            return False
    # Legacy PBKDF2 path — accepts existing hashes during migration
    salt, _ = password_hash.split("$", 1)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    expected_hash = salt + "$" + candidate.hex()
    return hmac.compare_digest(expected_hash, password_hash)


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")


def _b64url_decode(payload: str) -> bytes:
    pad = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + pad)


# ── RSA key management (FA-004a) ─────────────────────────────────────────────

def _load_or_generate_rsa_key():
    """Load RSA private key from JWT_PRIVATE_KEY env var, or generate an ephemeral key."""
    import os
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    pem = os.environ.get("JWT_PRIVATE_KEY", "").strip()
    if pem:
        return serialization.load_pem_private_key(pem.replace("\\n", "\n").encode(), password=None)
    # Ephemeral key for development — tokens invalidated on restart
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _get_rsa_key_pair():
    """Return (private_key, public_key, kid) — cached at module level."""
    import hashlib as _hl
    from cryptography.hazmat.primitives import serialization as _ser
    private_key = _load_or_generate_rsa_key()
    public_key = private_key.public_key()
    der = public_key.public_bytes(_ser.Encoding.DER, _ser.PublicFormat.SubjectPublicKeyInfo)
    kid = _hl.sha256(der).hexdigest()[:16]
    return private_key, public_key, kid


_RSA_KEY_CACHE: tuple | None = None


def get_rsa_key_pair():
    global _RSA_KEY_CACHE
    if _RSA_KEY_CACHE is None:
        _RSA_KEY_CACHE = _get_rsa_key_pair()
    return _RSA_KEY_CACHE


def get_jwks() -> Dict[str, object]:
    """Build JWKS document from current RSA public key (spec §4.8)."""
    import base64 as _b64
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
    _, public_key, kid = get_rsa_key_pair()
    pub_numbers = public_key.public_key().public_numbers() if not isinstance(public_key, RSAPublicKey) else public_key.public_numbers()
    n_bytes = pub_numbers.n.to_bytes((pub_numbers.n.bit_length() + 7) // 8, "big")
    e_bytes = pub_numbers.e.to_bytes((pub_numbers.e.bit_length() + 7) // 8, "big")
    n_b64 = _b64.urlsafe_b64encode(n_bytes).decode().rstrip("=")
    e_b64 = _b64.urlsafe_b64encode(e_bytes).decode().rstrip("=")
    return {"keys": [{"kty": "RSA", "kid": kid, "alg": "RS256", "use": "sig", "n": n_b64, "e": e_b64}]}


def issue_token(secret: str, claims: Dict[str, object], ttl_seconds: int) -> str:
    """Issue JWT. Uses RS256 when RSA key available; falls back to HS256 (legacy/dev)."""
    import uuid as _uuid
    now = int(time.time())
    envelope = dict(claims)
    envelope["iat"] = now
    envelope["exp"] = now + ttl_seconds
    envelope.setdefault("jti", str(_uuid.uuid4()))
    envelope.setdefault("iss", "lms-platform")
    envelope.setdefault("aud", ["lms.api"])
    envelope.setdefault("sid", claims.get("session_id", ""))

    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        private_key, _, kid = get_rsa_key_pair()
        header = {"alg": "RS256", "typ": "JWT", "kid": kid}
        encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        encoded_payload = _b64url_encode(json.dumps(envelope, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"
    except Exception:
        # AUD-047: HS256 fallback when cryptography package unavailable. Log warning —
        # symmetric signing lacks RS256 non-repudiation properties.
        import logging as _logging
        _logging.getLogger("auth-service.security").warning(
            "auth-service: RS256 signing unavailable — falling back to HS256. "
            "Install cryptography package for production use."
        )
        header = {"alg": "HS256", "typ": "JWT"}
        encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        encoded_payload = _b64url_encode(json.dumps(envelope, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"


def validate_token(secret: str, token: str, is_jti_revoked=None) -> Tuple[bool, Dict[str, object] | None, str | None]:
    """Validate JWT. Handles RS256 (new) and HS256 (legacy) transparently."""
    try:
        encoded_header, encoded_payload, encoded_sig = token.split(".")
    except ValueError:
        return False, None, "invalid_format"

    try:
        header = json.loads(_b64url_decode(encoded_header).decode("utf-8"))
    except Exception:
        return False, None, "invalid_header"

    alg = header.get("alg", "HS256")

    if alg == "RS256":
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            _, public_key, _ = get_rsa_key_pair()
            signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
            sig_bytes = _b64url_decode(encoded_sig)
            public_key.verify(sig_bytes, signing_input, padding.PKCS1v15(), hashes.SHA256())
        except Exception:
            return False, None, "invalid_signature"
    else:
        # HS256 path — legacy tokens during migration window
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

    jti = payload.get("jti")
    if jti and is_jti_revoked and is_jti_revoked(str(jti)):
        return False, None, "token_revoked"

    return True, payload, None
