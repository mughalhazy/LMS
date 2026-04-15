from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class BadgeStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class BadgeIssuanceStatus(str, Enum):
    ISSUED = "issued"
    REVOKED = "revoked"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BadgeDefinition:
    tenant_id: str
    code: str
    title: str
    description: str
    criteria: dict
    image_url: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    status: BadgeStatus = BadgeStatus.ACTIVE
    badge_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class BadgeIssuance:
    tenant_id: str
    badge_id: str
    learner_id: str
    issued_by: str
    evidence: dict
    issued_at: datetime = field(default_factory=utc_now)
    status: BadgeIssuanceStatus = BadgeIssuanceStatus.ISSUED
    revoked_at: datetime | None = None
    revoke_reason: str | None = None
    issuance_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
