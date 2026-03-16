"""Domain models for certificate_service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CertificateStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(slots=True)
class CompletionRef:
    source_event: str
    source_event_id: str
    completed_at: datetime


@dataclass(slots=True)
class Certificate:
    certificate_id: str
    verification_code: str
    tenant_id: str
    user_id: str
    course_id: str
    enrollment_id: str | None
    template_id: str
    status: CertificateStatus
    issued_at: datetime
    expires_at: datetime | None
    artifact_uri: str | None
    metadata: dict[str, Any] = field(default_factory=dict)
    completion_ref: CompletionRef | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None


@dataclass(slots=True)
class CertificateTemplate:
    template_id: str
    tenant_id: str
    name: str
    version: int
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class BadgeExtensionProfile:
    certificate_id: str
    provider: str
    badge_class_id: str
    evidence_url: str | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VerificationMetadata:
    verification_code: str
    certificate_id: str
    status: CertificateStatus
    is_valid: bool
    issued_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    verification_url: str
    claims: dict[str, Any] = field(default_factory=dict)
