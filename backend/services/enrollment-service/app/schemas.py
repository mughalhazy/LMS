"""Request and response schemas for enrollment service API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .models import EnrollmentStatus


class EnrollmentCreateRequest(BaseModel):
    learner_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    assignment_source: str = Field(default="admin", min_length=1)
    cohort_id: str | None = None
    session_id: str | None = None


class StatusTransitionRequest(BaseModel):
    to_status: EnrollmentStatus
    reason: str = Field(min_length=1)


class EnrollmentResponse(BaseModel):
    id: str
    tenant_id: str
    learner_id: str
    course_id: str
    assignment_source: str
    cohort_id: str | None
    session_id: str | None
    status: EnrollmentStatus
    created_at: datetime
    updated_at: datetime


class EnrollmentListResponse(BaseModel):
    items: list[EnrollmentResponse]


class AuditLogResponse(BaseModel):
    actor_id: str
    action: str
    enrollment_id: str
    metadata: dict
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
