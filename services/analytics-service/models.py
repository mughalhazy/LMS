from __future__ import annotations

from dataclasses import dataclass, field

from shared.models.network_analytics import InstitutionBenchmark, StudentBenchmark, TeacherBenchmark
from shared.models.teacher_performance import TeacherPerformanceSnapshot


@dataclass(frozen=True)
class SystemOfRecordSnapshot:
    learner_id: str
    tenant_id: str
    lifecycle_state: str
    attendance_rate: float
    overdue_balance: float


@dataclass(frozen=True)
class ProgressSnapshot:
    completion_rate: float
    weekly_active_minutes: int
    missed_deadlines: int
    activity_streak_days: int


@dataclass(frozen=True)
class ExamEngineSnapshot:
    average_score: float
    failed_attempts: int
    no_show_count: int
    trend_delta: float


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
