from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .models import BadgeIssuanceStatus, BadgeStatus


class BadgeDefinitionCreate(BaseModel):
    tenant_id: str
    code: str
    title: str
    description: str
    criteria: dict = Field(default_factory=dict)
    image_url: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class BadgeDefinitionPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    criteria: dict | None = None
    image_url: str | None = None
    metadata: dict[str, str] | None = None
    status: BadgeStatus | None = None


class BadgeDefinitionOut(BaseModel):
    badge_id: str
    tenant_id: str
    code: str
    title: str
    description: str
    criteria: dict
    image_url: str | None
    metadata: dict[str, str]
    status: BadgeStatus
    created_at: datetime
    updated_at: datetime


class BadgeIssuanceCreate(BaseModel):
    tenant_id: str
    badge_id: str
    learner_id: str
    issued_by: str
    evidence: dict = Field(default_factory=dict)


class BadgeIssuancePatch(BaseModel):
    status: BadgeIssuanceStatus
    revoke_reason: str | None = None


class BadgeIssuanceOut(BaseModel):
    issuance_id: str
    tenant_id: str
    badge_id: str
    learner_id: str
    issued_by: str
    evidence: dict
    issued_at: datetime
    status: BadgeIssuanceStatus
    revoked_at: datetime | None
    revoke_reason: str | None
    created_at: datetime
    updated_at: datetime
