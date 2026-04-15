"""Request and response schemas for certificate_service API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CompletionRefSchema(BaseModel):
    source_event: str = Field(min_length=1)
    source_event_id: str = Field(min_length=1)
    completed_at: datetime


class IssueCertificateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    enrollment_id: str | None = None
    template_id: str = Field(min_length=1)
    completion_ref: CompletionRefSchema
    artifact_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime | None = None
    issued_by: str = Field(min_length=1)


class CertificateResponse(BaseModel):
    certificate_id: str
    verification_code: str
    tenant_id: str
    user_id: str
    course_id: str
    enrollment_id: str | None
    template_id: str
    status: Literal["active", "revoked", "expired"]
    issued_at: datetime
    expires_at: datetime | None
    artifact_uri: str | None
    metadata: dict[str, Any]
    revoked_at: datetime | None = None
    revocation_reason: str | None = None


class RevokeCertificateRequest(BaseModel):
    reason: str = Field(min_length=1)
    revoked_by: str = Field(min_length=1)


class CertificateTemplateRequest(BaseModel):
    template_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    body: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CertificateTemplatePatchRequest(BaseModel):
    name: str | None = None
    body: str | None = None
    metadata: dict[str, Any] | None = None


class VerificationResponse(BaseModel):
    verification_code: str
    is_valid: bool
    status: Literal["active", "revoked", "expired"]
    certificate_id: str
    issued_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    verification_url: str
    claims: dict[str, Any]


class BadgeExtensionRequest(BaseModel):
    provider: str = Field(min_length=1)
    badge_class_id: str = Field(min_length=1)
    evidence_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: dict[str, str]
