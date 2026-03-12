from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .models import (
    AssessmentAttempt,
    CourseCompletion,
    CourseEnrollment,
    LearningActivityEvent,
    PathProgressSnapshot,
)


@dataclass
class AnalyticsRepository:
    enrollments: list[CourseEnrollment] = field(default_factory=list)
    completions: list[CourseCompletion] = field(default_factory=list)
    activities: list[LearningActivityEvent] = field(default_factory=list)
    assessment_attempts: list[AssessmentAttempt] = field(default_factory=list)
    path_snapshots: list[PathProgressSnapshot] = field(default_factory=list)

    @staticmethod
    def _in_window(timestamp: datetime, start_at: datetime | None, end_at: datetime | None) -> bool:
        if start_at and timestamp < start_at:
            return False
        if end_at and timestamp > end_at:
            return False
        return True

    def list_enrollments(self, course_id: str, cohort_id: str | None = None) -> list[CourseEnrollment]:
        return [
            item
            for item in self.enrollments
            if item.course_id == course_id and (cohort_id is None or item.cohort_id == cohort_id)
        ]

    def list_completions(
        self,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> list[CourseCompletion]:
        cohort_learners = {
            row.learner_id for row in self.enrollments if row.course_id == course_id and (cohort_id is None or row.cohort_id == cohort_id)
        }
        return [
            row
            for row in self.completions
            if row.course_id == course_id
            and row.learner_id in cohort_learners
            and self._in_window(row.completion_timestamp, start_at, end_at)
        ]

    def list_activities(
        self,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> list[LearningActivityEvent]:
        return [
            row
            for row in self.activities
            if row.course_id == course_id
            and (cohort_id is None or row.cohort_id == cohort_id)
            and self._in_window(row.event_timestamp, start_at, end_at)
        ]

    def list_assessment_attempts(
        self,
        cohort_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[AssessmentAttempt]:
        return [
            row
            for row in self.assessment_attempts
            if row.cohort_id == cohort_id and self._in_window(row.submitted_at, start_at, end_at)
        ]

    def list_path_snapshots(
        self,
        learning_path_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> list[PathProgressSnapshot]:
        return [
            row
            for row in self.path_snapshots
            if row.learning_path_id == learning_path_id
            and (cohort_id is None or row.cohort_id == cohort_id)
            and self._in_window(row.snapshot_timestamp, start_at, end_at)
        ]
