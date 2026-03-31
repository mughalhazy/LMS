from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CourseEnrollment:
    tenant_id: str
    learner_id: str
    course_id: str
    cohort_id: str
    enrollment_status: str
    enrolled_at: datetime


@dataclass(frozen=True)
class CourseCompletion:
    tenant_id: str
    learner_id: str
    course_id: str
    completion_status: str
    completion_timestamp: datetime
    total_time_spent_seconds: int


@dataclass(frozen=True)
class LearningActivityEvent:
    tenant_id: str
    learner_id: str
    course_id: str
    cohort_id: str
    active_minutes: float
    content_interactions: int
    assessment_attempts: int
    discussion_actions: int
    event_timestamp: datetime
    sentiment_score: float = 0.0


@dataclass(frozen=True)
class AssessmentAttempt:
    tenant_id: str
    learner_id: str
    course_id: str
    cohort_id: str
    score: float
    max_score: float
    submitted_at: datetime


@dataclass(frozen=True)
class PathProgressSnapshot:
    tenant_id: str
    learner_id: str
    learning_path_id: str
    cohort_id: str
    progress_percent: float
    completed_modules: int
    total_modules: int
    snapshot_timestamp: datetime


@dataclass(frozen=True)
class RevenueRecord:
    tenant_id: str
    plan_id: str
    amount: float
    billed_at: datetime
    currency: str = "USD"
    source_event_id: str | None = None
