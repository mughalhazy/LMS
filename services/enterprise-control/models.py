from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AuditQuery:
    actor_id: str | None = None
    action: str | None = None
    resource_prefix: str | None = None
    decision: str | None = None
    permission: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    offset: int = 0
    limit: int = 50
    descending: bool = False


@dataclass(frozen=True)
class ComplianceRecord:
    record_id: str
    tenant_id: str
    framework: str
    control_id: str
    status: str
    assessed_by_actor_id: str
    created_at: datetime
    evidence: dict[str, Any] = field(default_factory=dict)

