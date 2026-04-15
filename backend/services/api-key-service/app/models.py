from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class ApiKeyRecord:
    key_id: str
    tenant_id: str
    name: str
    hashed_secret: str
    key_prefix: str
    scopes: List[str]
    created_by: str
    created_at: datetime
    rotated_from_key_id: str | None = None
    revoked: bool = False
    revoked_at: datetime | None = None


@dataclass
class UsageCounter:
    key_id: str
    tenant_id: str
    total_requests: int = 0
    per_scope: Dict[str, int] = field(default_factory=dict)
    last_used_at: datetime | None = None
