from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from shared.models.network_analytics import InstitutionBenchmark, StudentBenchmark, TeacherBenchmark
from shared.models.teacher_performance import TeacherPerformanceSnapshot


@dataclass(frozen=True)
class SystemOfRecordSnapshot:
    learner_id: str
    tenant_id: str
    lifecycle_state: str
    attendance_rate: float
    overdue_balance: float

    @classmethod
    def from_profile(cls, profile: Any) -> "SystemOfRecordSnapshot":
        attendance = getattr(profile, "attendance_summary", None)
        attendance_rate_raw = getattr(attendance, "attendance_rate", 0)
        financial = getattr(profile, "financial_state", None)
        overdue_balance_raw = getattr(financial, "dues_outstanding", 0)
        return cls(
            learner_id=str(getattr(profile, "student_id", "")),
            tenant_id=str(getattr(profile, "tenant_id", "")),
            lifecycle_state=str(getattr(profile, "lifecycle_state", "unknown")),
            attendance_rate=float(attendance_rate_raw or 0),
            overdue_balance=float(overdue_balance_raw or 0),
        )


@dataclass(frozen=True)
class ProgressSnapshot:
    completion_rate: float
    weekly_active_minutes: int
    missed_deadlines: int
    activity_streak_days: int

    @classmethod
    def from_progress_payload(cls, payload: dict[str, Any]) -> "ProgressSnapshot":
        courses = payload.get("courses", {}) if isinstance(payload, dict) else {}
        statuses = [
            str(course.get("completion_status", ""))
            for course in courses.values()
            if isinstance(course, dict)
        ]
        completion_rate = 0.0
        if statuses:
            completed = sum(1 for status in statuses if status == "completed")
            completion_rate = (completed / len(statuses)) * 100
        metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        return cls(
            completion_rate=round(completion_rate, 2),
            weekly_active_minutes=int(metadata.get("weekly_active_minutes", 0) or 0),
            missed_deadlines=int(metadata.get("missed_deadlines", 0) or 0),
            activity_streak_days=int(metadata.get("activity_streak_days", 0) or 0),
        )


@dataclass(frozen=True)
class ExamEngineSnapshot:
    average_score: float
    failed_attempts: int
    no_show_count: int
    trend_delta: float

    @classmethod
    def from_exam_events(cls, events: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> "ExamEngineSnapshot":
        submitted_scores: list[float] = []
        failed_attempts = 0
        no_show_count = 0
        for event in events:
            event_type = str(event.get("event_type", ""))
            if event_type == "exam.session.submitted":
                score = event.get("score")
                if isinstance(score, (int, float, Decimal)):
                    submitted_scores.append(float(score))
                if isinstance(score, (int, float, Decimal)) and float(score) < 50:
                    failed_attempts += 1
            elif event_type == "exam.session.expired":
                no_show_count += 1

        average_score = round(sum(submitted_scores) / len(submitted_scores), 2) if submitted_scores else 0.0
        if len(submitted_scores) >= 2:
            trend_delta = round(submitted_scores[-1] - submitted_scores[0], 2)
        else:
            trend_delta = 0.0

        return cls(
            average_score=average_score,
            failed_attempts=failed_attempts,
            no_show_count=no_show_count,
            trend_delta=trend_delta,
        )


@dataclass(frozen=True)
class LearningOptimizationInsightRequest:
    system_of_record: SystemOfRecordSnapshot
    progress: ProgressSnapshot
    exam_engine: ExamEngineSnapshot
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendationHooks:
    recommendation_service_input: dict[str, object]


@dataclass(frozen=True)
class LearningOptimizationInsight:
    tenant_id: str
    learner_id: str
    risk_band: str
    dropout_risk_score: float
    engagement_risk_score: float
    recommendation_hooks: RecommendationHooks
    teacher_actions: tuple[str, ...]
    operations_actions: tuple[str, ...]
    owner_actions: tuple[str, ...]


__all__ = [
    "TeacherPerformanceSnapshot",
    "StudentBenchmark",
    "TeacherBenchmark",
    "InstitutionBenchmark",
    "SystemOfRecordSnapshot",
    "ProgressSnapshot",
    "ExamEngineSnapshot",
    "LearningOptimizationInsightRequest",
    "LearningOptimizationInsight",
    "RecommendationHooks",
]
