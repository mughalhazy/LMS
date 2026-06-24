from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import AssessmentFormat, AssessmentStatus, AssessmentType, AttemptStatus


class AssessmentCreateRequest(BaseModel):
    course_id: str
    lesson_id: str | None = None
    title: str
    description: str | None = None
    assessment_type: AssessmentType
    assessment_format: AssessmentFormat | None = None  # B03-006: assessment-data-schema.md §2
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
    assessment_format: AssessmentFormat | None = None  # B03-006: assessment-data-schema.md §2
    status: AssessmentStatus
    max_score: float
    passing_score: float
    time_limit_minutes: int | None
    question_count: int
    metadata: dict[str, str | int | float | bool | None]
    created_by: str
    created_at: datetime
    updated_at: datetime
    attempts_count: int = 0
    avg_score: float | None = None


class AssessmentListResponse(BaseModel):
    items: list[AssessmentResponse]


class AttemptStartRequest(BaseModel):
    learner_id: str
    exam_session_id: str | None = None
    isolation_key: str | None = None


class AttemptResponse(BaseModel):
    attempt_id: str
    tenant_id: str
    assessment_id: str
    learner_id: str
    status: AttemptStatus
    started_at: datetime
    submitted_at: datetime | None
    grading_result_id: str | None
    exam_session_id: str | None
    isolation_key: str | None


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


class VersionCreateRequest(BaseModel):
    actor_id: str
    source_version_number: int | None = None


class VersionPublishRequest(BaseModel):
    actor_id: str
    availability_start: datetime | None = None
    availability_end: datetime | None = None


class VersionResponse(BaseModel):
    version_id: str
    assessment_id: str
    tenant_id: str
    version_number: int
    status: str
    created_by: str
    created_at: datetime
    published_at: datetime | None
    availability_start: datetime | None
    availability_end: datetime | None
    item_ids: list[str]


class ItemCreateRequest(BaseModel):
    actor_id: str
    question_text: str
    item_type: str
    options: list[dict[str, Any]] = Field(default_factory=list)
    correct_answer: str | None = None
    points: float = Field(gt=0, default=1.0)
    order: int = Field(ge=0, default=0)


class ItemUpdateRequest(BaseModel):
    actor_id: str
    question_text: str | None = None
    item_type: str | None = None
    options: list[dict[str, Any]] | None = None
    correct_answer: str | None = None
    points: float | None = Field(default=None, gt=0)
    order: int | None = Field(default=None, ge=0)


class ItemResponse(BaseModel):
    item_id: str
    assessment_id: str
    version_id: str
    tenant_id: str
    question_text: str
    item_type: str
    options: list[dict[str, Any]]
    correct_answer: str | None
    points: float
    order: int
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    service: str


class MetricsResponse(BaseModel):
    service: str
    counters: dict[str, int]
