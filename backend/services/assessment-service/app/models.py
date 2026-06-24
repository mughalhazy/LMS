from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AssessmentType(str, Enum):
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    MOCK_TEST = "mock_test"


class AssessmentFormat(str, Enum):
    # B03-006: assessment-data-schema.md §2 extensibility field
    STANDARD_QUIZ = "standard_quiz"
    STANDARD_EXAM = "standard_exam"
    TAKE_HOME_ASSIGNMENT = "take_home_assignment"
    MOCK_TEST = "mock_test"
    BOARD_STYLE = "board_style"


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
    attempts_count: int = 0
    avg_score: float | None = None
    assessment_format: AssessmentFormat | None = None  # B03-006: assessment-data-schema.md §2


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
class AssessmentVersion:
    version_id: str
    assessment_id: str
    tenant_id: str
    version_number: int
    status: str  # draft | published
    created_by: str
    created_at: datetime
    published_at: datetime | None = None
    availability_start: datetime | None = None
    availability_end: datetime | None = None
    item_ids: list[str] = field(default_factory=list)


@dataclass
class AssessmentItem:
    item_id: str
    assessment_id: str
    version_id: str
    tenant_id: str
    question_text: str
    item_type: str  # mcq | short_answer | true_false | essay
    options: list[dict[str, object]]
    correct_answer: str | None
    points: float
    order: int
    created_at: datetime
    updated_at: datetime


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
