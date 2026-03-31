"""API schemas for progress-service v1."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

ProgressStatus = Literal["not_started", "in_progress", "completed", "passed", "failed"]
PathStatus = Literal["not_started", "in_progress", "completed"]


class LessonProgressUpsertRequest(BaseModel):
    tenant_id: str
    learner_id: str
    course_id: str
    enrollment_id: str
    academy_cohort_id: Optional[str] = None
    academy_enrollment_id: Optional[str] = None
    progress_percentage: float = Field(ge=0, le=100)
    status: ProgressStatus
    time_spent_seconds_delta: int = Field(ge=0)
    attempt_count: int = Field(ge=0)
    timestamp: datetime
    idempotency_key: str
    workforce_policy_id: str | None = None
    workforce_manager_id: str | None = None
    workforce_due_date: str | None = None

    @model_validator(mode="after")
    def validate_academy_context(self) -> "LessonProgressUpsertRequest":
        if (self.academy_cohort_id is None) ^ (self.academy_enrollment_id is None):
            raise ValueError("academy_cohort_id and academy_enrollment_id must be provided together")
        return self


class LessonProgressCompleteRequest(BaseModel):
    tenant_id: str
    learner_id: str
    course_id: str
    enrollment_id: str
    academy_cohort_id: Optional[str] = None
    academy_enrollment_id: Optional[str] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    time_spent_seconds: int = Field(ge=0)
    attempt_count: int = Field(ge=0)
    completed_at: datetime
    idempotency_key: str
    workforce_policy_id: str | None = None
    workforce_manager_id: str | None = None
    workforce_due_date: str | None = None

    @model_validator(mode="after")
    def validate_academy_context(self) -> "LessonProgressCompleteRequest":
        if (self.academy_cohort_id is None) ^ (self.academy_enrollment_id is None):
            raise ValueError("academy_cohort_id and academy_enrollment_id must be provided together")
        return self


class LearningPathAssignmentRequest(BaseModel):
    tenant_id: str
    learner_id: str
    assigned_course_ids: list[str]
    expected_completion_date: Optional[str] = None
    idempotency_key: str


class ProgressRecordResponse(BaseModel):
    progress_id: str
    tenant_id: str
    learner_id: str
    user_id: str
    course_id: str
    lesson_id: Optional[str]
    enrollment_id: str
    progress_percentage: float
    percent_complete: float
    status: ProgressStatus
    last_activity_at: datetime
    completed_at: Optional[datetime]


class CourseProgressResponse(BaseModel):
    tenant_id: str
    learner_id: str
    course_id: str
    enrollment_id: str
    completion_status: ProgressStatus
    progress_percentage: float
    final_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    total_time_spent_seconds: int
    certificate_id: Optional[str]


class LearningPathProgressResponse(BaseModel):
    tenant_id: str
    learner_id: str
    learning_path_id: str
    assigned_course_ids: list[str]
    completed_course_ids: list[str]
    progress_percentage: float
    current_course_id: Optional[str]
    status: PathStatus
    expected_completion_date: Optional[str]
    last_activity_at: datetime


class LearnerProgressSummaryResponse(BaseModel):
    tenant_id: str
    learner_id: str
    courses: list[CourseProgressResponse]
    lessons: list[ProgressRecordResponse]
    learning_paths: list[LearningPathProgressResponse]
    mandatory_training: list[dict[str, str | float | bool]]


class LessonCompleteResponse(BaseModel):
    lesson_progress: ProgressRecordResponse
    course_progress: CourseProgressResponse


class LearningPathAssignmentResponse(BaseModel):
    learning_path_id: str
    status: PathStatus
    progress_percentage: float
    current_course_id: Optional[str]


class TenantScopedQuery(BaseModel):
    tenant_id: str


class TenantHeader(BaseModel):
    x_tenant_id: str

    @model_validator(mode="after")
    def has_tenant(self) -> "TenantHeader":
        if not self.x_tenant_id:
            raise ValueError("x_tenant_id required")
        return self
