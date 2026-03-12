from __future__ import annotations

import hashlib
import secrets


def generate_api_secret() -> str:
    return f"lms_{secrets.token_urlsafe(32)}"


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def verify_secret(secret: str, hashed_secret: str) -> bool:
    return hash_secret(secret) == hashed_secret


def scope_allowed(required_scope: str, granted_scopes: list[str]) -> bool:
    if "integrations:*" in granted_scopes:
        return True
    return required_scope in granted_scopes
