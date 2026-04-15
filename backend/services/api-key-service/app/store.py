from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Dict, Optional, Tuple

from .models import ApiKeyRecord, UsageCounter


class InMemoryApiKeyStore:
    def __init__(self) -> None:
        self.keys_by_id: Dict[str, ApiKeyRecord] = {}
        self.keys_by_hash: Dict[Tuple[str, str], ApiKeyRecord] = {}
        self.usage_by_key_id: Dict[str, UsageCounter] = {}

    def create_key(
        self,
        tenant_id: str,
        name: str,
        hashed_secret: str,
        key_prefix: str,
        scopes: list[str],
        created_by: str,
        rotated_from_key_id: str | None = None,
    ) -> ApiKeyRecord:
        key_id = f"key_{secrets.token_urlsafe(10)}"
        record = ApiKeyRecord(
            key_id=key_id,
            tenant_id=tenant_id,
            name=name,
            hashed_secret=hashed_secret,
            key_prefix=key_prefix,
            scopes=scopes,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            rotated_from_key_id=rotated_from_key_id,
        )
        self.keys_by_id[key_id] = record
        self.keys_by_hash[(tenant_id, hashed_secret)] = record
        self.usage_by_key_id[key_id] = UsageCounter(key_id=key_id, tenant_id=tenant_id)
        return record

    def find_key(self, key_id: str) -> Optional[ApiKeyRecord]:
        return self.keys_by_id.get(key_id)

    def find_by_hashed_secret(self, tenant_id: str, hashed_secret: str) -> Optional[ApiKeyRecord]:
        return self.keys_by_hash.get((tenant_id, hashed_secret))

    def revoke_key(self, key_id: str) -> None:
        record = self.keys_by_id.get(key_id)
        if record is None:
            return
        record.revoked = True
        record.revoked_at = datetime.now(timezone.utc)

    def increment_usage(self, key_id: str, scope: str) -> None:
        usage = self.usage_by_key_id[key_id]
        usage.total_requests += 1
        usage.per_scope[scope] = usage.per_scope.get(scope, 0) + 1
        usage.last_used_at = datetime.now(timezone.utc)

    def get_usage(self, key_id: str) -> Optional[UsageCounter]:
        return self.usage_by_key_id.get(key_id)
