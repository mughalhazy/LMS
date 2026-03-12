from __future__ import annotations

from typing import Dict, Tuple

from .schemas import (
    ALLOWED_SCOPES,
    ApiKeyAuthorizeRequest,
    ApiKeyCreateRequest,
    ApiKeyRotateRequest,
    ApiKeyUsageReportRequest,
)
from .security import generate_api_secret, hash_secret, scope_allowed
from .store import InMemoryApiKeyStore


class ApiKeyService:
    def __init__(self, store: InMemoryApiKeyStore) -> None:
        self.store = store

    def create_api_key(self, req: ApiKeyCreateRequest) -> Tuple[int, Dict[str, object]]:
        if not req.scopes:
            return 400, {"error": "scopes_required"}

        invalid_scopes = [scope for scope in req.scopes if scope not in ALLOWED_SCOPES]
        if invalid_scopes:
            return 400, {"error": "invalid_scopes", "invalid_scopes": invalid_scopes}

        plaintext_secret = generate_api_secret()
        record = self.store.create_key(
            tenant_id=req.tenant_id,
            name=req.name,
            hashed_secret=hash_secret(plaintext_secret),
            key_prefix=plaintext_secret[:12],
            scopes=req.scopes,
            created_by=req.created_by,
        )

        return 201, {
            "key_id": record.key_id,
            "tenant_id": record.tenant_id,
            "name": record.name,
            "api_key": plaintext_secret,
            "key_prefix": record.key_prefix,
            "scopes": record.scopes,
            "created_at": record.created_at.isoformat(),
            "warning": "Store this key securely. It cannot be retrieved again.",
        }

    def rotate_api_key(self, req: ApiKeyRotateRequest) -> Tuple[int, Dict[str, object]]:
        current_key = self.store.find_key(req.key_id)
        if current_key is None or current_key.tenant_id != req.tenant_id:
            return 404, {"error": "key_not_found"}

        if current_key.revoked:
            return 409, {"error": "key_already_revoked"}

        plaintext_secret = generate_api_secret()
        new_record = self.store.create_key(
            tenant_id=current_key.tenant_id,
            name=current_key.name,
            hashed_secret=hash_secret(plaintext_secret),
            key_prefix=plaintext_secret[:12],
            scopes=current_key.scopes,
            created_by=req.rotated_by,
            rotated_from_key_id=current_key.key_id,
        )
        self.store.revoke_key(current_key.key_id)

        return 200, {
            "rotated_key_id": current_key.key_id,
            "new_key_id": new_record.key_id,
            "api_key": plaintext_secret,
            "key_prefix": new_record.key_prefix,
            "scopes": new_record.scopes,
            "revoked_previous_key": True,
        }

    def authorize(self, req: ApiKeyAuthorizeRequest) -> Tuple[int, Dict[str, object]]:
        hashed = hash_secret(req.api_key)
        key = self.store.find_by_hashed_secret(req.tenant_id, hashed)
        if key is None:
            return 401, {"error": "invalid_api_key"}
        if key.revoked:
            return 401, {"error": "revoked_api_key"}
        if not scope_allowed(req.required_scope, key.scopes):
            return 403, {
                "error": "insufficient_scope",
                "required_scope": req.required_scope,
                "granted_scopes": key.scopes,
            }

        self.store.increment_usage(key.key_id, req.required_scope)

        return 200, {
            "authorized": True,
            "key_id": key.key_id,
            "tenant_id": key.tenant_id,
            "scope": req.required_scope,
        }

    def usage_report(self, req: ApiKeyUsageReportRequest) -> Tuple[int, Dict[str, object]]:
        key = self.store.find_key(req.key_id)
        if key is None or key.tenant_id != req.tenant_id:
            return 404, {"error": "key_not_found"}

        usage = self.store.get_usage(req.key_id)
        if usage is None:
            return 404, {"error": "usage_not_found"}

        return 200, {
            "key_id": key.key_id,
            "tenant_id": key.tenant_id,
            "total_requests": usage.total_requests,
            "per_scope": usage.per_scope,
            "last_used_at": usage.last_used_at.isoformat() if usage.last_used_at else None,
            "revoked": key.revoked,
        }
