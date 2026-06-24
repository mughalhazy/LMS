"""Request and response schemas for enrollment service API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .models import EnrollmentStatus


class EnrollmentCreateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    source_channel: str = Field(default="admin_assignment", min_length=1)
    cohort_id: str | None = None
    session_id: str | None = None
    course_title: str | None = None
    assigned_by: str | None = None
    tenant_id: str | None = None  # AUD-018: spec §4.1 includes tenant_id in body


class StatusTransitionRequest(BaseModel):
    # AUD-020: spec §4.5 uses target_status and status_reason; old names kept as aliases
    target_status: EnrollmentStatus | None = None
    status_reason: str | None = None
    effective_at: str | None = None  # AUD-021: spec §4.5 effective_at field
    expected_version: int | None = None
    # Backward-compat aliases
    to_status: EnrollmentStatus | None = None
    reason: str | None = None

    @property
    def resolved_status(self) -> EnrollmentStatus:
        return self.target_status or self.to_status  # type: ignore[return-value]

    @property
    def resolved_reason(self) -> str:
        return self.status_reason or self.reason or ""


class BulkAssignRequest(BaseModel):
    user_ids: list[str] = Field(min_length=1)
    course_id: str = Field(min_length=1)
    source_channel: str = Field(default="bulk_import", min_length=1)
    cohort_id: str | None = None
    session_id: str | None = None
    idempotency_key: str | None = None
    tenant_id: str | None = None   # AUD-019: spec §4.6 requires tenant_id
    assigned_by: str | None = None  # AUD-019: spec §4.6 requires assigned_by


class BulkAssignResult(BaseModel):
    user_id: str
    status: str
    enrollment_id: str | None = None
    error: str | None = None


class BulkAssignResponse(BaseModel):
    # AUD-023: spec §4.6 response shape: job_id + accepted_count + rejected_count + submitted_at
    job_id: str
    accepted_count: int
    rejected_count: int
    submitted_at: str
    # Extended: per-item results kept for observability (not in spec)
    results: list[BulkAssignResult] = Field(default_factory=list)


class EnrollmentLinksRequest(BaseModel):
    cohort_id: str | None = None
    session_id: str | None = None


class EnrollmentResponse(BaseModel):
    enrollment_id: str
    tenant_id: str
    user_id: str
    course_id: str
    course_title: str | None = None
    source_channel: str
    cohort_id: str | None
    session_id: str | None
    enrollment_status: EnrollmentStatus
    version: int = 1
    created_at: datetime
    updated_at: datetime
    enrolled_at: datetime | None = None
    completed_at: datetime | None = None
    dropped_at: datetime | None = None
    deferred_at: datetime | None = None
    expired_at: datetime | None = None


class EnrollmentListResponse(BaseModel):
    # AUD-022: spec §4.3 response includes pagination fields
    items: list[EnrollmentResponse]
    page: int = 1
    page_size: int = 50
    total: int = 0


class AuditLogResponse(BaseModel):
    actor_id: str
    action: str
    enrollment_id: str
    metadata: dict
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
