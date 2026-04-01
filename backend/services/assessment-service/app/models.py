from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AssessmentType(str, Enum):
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    MOCK_TEST = "mock_test"


class AssessmentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    RETIRED = "retired"


class AttemptStatus(str, Enum):
    STARTED = "started"
    SUBMITTED = "submitted"
    GRADED = "graded"


@dataclass
class AssessmentDefinition:
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


@dataclass
class AttemptRecord:
    attempt_id: str
    tenant_id: str
    assessment_id: str
    learner_id: str
    started_at: datetime
    status: AttemptStatus
    submitted_at: datetime | None = None
    grading_result_id: str | None = None
    exam_session_id: str | None = None
    isolation_key: str | None = None


@dataclass
class SubmissionRecord:
    submission_id: str
    attempt_id: str
    tenant_id: str
    payload: dict[str, object]
    submitted_by: str
    submitted_at: datetime


@dataclass
class AuditRecord:
    event_id: str
    tenant_id: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    timestamp: datetime
    details: dict[str, object] = field(default_factory=dict)
