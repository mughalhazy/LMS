from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import AssessmentStatus, AssessmentType, AttemptStatus


class AssessmentCreateRequest(BaseModel):
    course_id: str
    lesson_id: str | None = None
    title: str
    description: str | None = None
    assessment_type: AssessmentType
    max_score: float = Field(gt=0)
    passing_score: float = Field(ge=0)
    time_limit_minutes: int | None = Field(default=None, gt=0)
    question_count: int = Field(gt=0)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    actor_id: str


class AssessmentUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    max_score: float | None = Field(default=None, gt=0)
    passing_score: float | None = Field(default=None, ge=0)
    time_limit_minutes: int | None = Field(default=None, gt=0)
    question_count: int | None = Field(default=None, gt=0)
    metadata: dict[str, str | int | float | bool | None] | None = None
    actor_id: str


class AssessmentResponse(BaseModel):
    assessment_id: str
    tenant_id: str
    course_id: str
    lesson_id: str | None
    title: str
    description: str | None
    assessment_type: AssessmentType
    status: AssessmentStatus
    max_score: float
    passing_score: float
    time_limit_minutes: int | None
    question_count: int
    metadata: dict[str, str | int | float | bool | None]
    created_by: str
    created_at: datetime
    updated_at: datetime


class AssessmentListResponse(BaseModel):
    items: list[AssessmentResponse]


class AttemptStartRequest(BaseModel):
    learner_id: str


class AttemptResponse(BaseModel):
    attempt_id: str
    tenant_id: str
    assessment_id: str
    learner_id: str
    status: AttemptStatus
    started_at: datetime
    submitted_at: datetime | None
    grading_result_id: str | None


class SubmissionCreateRequest(BaseModel):
    payload: dict[str, Any]
    submitted_by: str


class SubmissionResponse(BaseModel):
    submission_id: str
    attempt_id: str
    tenant_id: str
    payload: dict[str, Any]
    submitted_by: str
    submitted_at: datetime


class GradeAttemptRequest(BaseModel):
    grading_result_id: str
    actor_id: str


class HealthResponse(BaseModel):
    status: str
    service: str


class MetricsResponse(BaseModel):
    service: str
    counters: dict[str, int]
