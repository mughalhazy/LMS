"""Domain models for the progress service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4

ProgressStatus = Literal["not_started", "in_progress", "completed", "passed", "failed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ProgressRecord:
    """Authoritative progress entity aligned with Rails Progress semantics."""

    tenant_id: str
    enrollment_id: str
    learner_id: str
    course_id: str
    lesson_id: Optional[str]
    progress_percentage: float
    status: ProgressStatus
    last_activity_at: datetime
    completed_at: Optional[datetime] = None
    progress_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class CourseProgressSnapshot:
    tenant_id: str
    learner_id: str
    course_id: str
    enrollment_id: str
    completed_lessons: int
    total_lessons: int
    progress_percentage: float
    completion_status: ProgressStatus
    started_at: datetime
    completed_at: Optional[datetime]
    last_activity_at: datetime
    final_score: Optional[float] = None
    certificate_id: Optional[str] = None
    total_time_spent_seconds: int = 0


@dataclass
class LearningPathProgressSnapshot:
    tenant_id: str
    learner_id: str
    learning_path_id: str
    assigned_course_ids: list[str]
    completed_course_ids: list[str]
    progress_percentage: float
    current_course_id: Optional[str]
    status: Literal["not_started", "in_progress", "completed"]
    expected_completion_date: Optional[str]
    last_activity_at: datetime


@dataclass
class CompletionMetricDaily:
    tenant_id: str
    metric_date: str
    course_id: Optional[str]
    learning_path_id: Optional[str]
    started_count: int
    completed_count: int
    completion_rate: float
    avg_time_to_complete_seconds: float
    avg_progress_percentage: float


@dataclass
class MandatoryTrainingProgress:
    tenant_id: str
    learner_id: str
    manager_id: str
    course_id: str
    policy_id: str
    due_date: str
    completion_status: Literal["not_started", "in_progress", "completed"]
    completion_percentage: float
    reminder_required: bool
    last_activity_at: datetime


@dataclass
class ProgressAuditEntry:
    tenant_id: str
    actor_id: str
    action: str
    progress_id: Optional[str]
    idempotency_key: Optional[str]
    occurred_at: datetime
    details: dict[str, object]


@dataclass
class ProgressEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    correlation_id: str
    payload: dict[str, object]
    metadata: dict[str, object] = field(default_factory=dict)
