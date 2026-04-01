from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from shared.models.teacher_performance import TeacherPerformanceSnapshot


class SystemOfRecordSnapshot(BaseModel):
    learner_id: str
    tenant_id: str
    lifecycle_state: str = "active"
    attendance_rate: float = Field(default=100.0, ge=0.0, le=100.0)
    overdue_balance: float = Field(default=0.0, ge=0.0)
    attendance_flags: list[str] = Field(default_factory=list)


class ProgressSnapshot(BaseModel):
    completion_rate: float = Field(ge=0.0, le=100.0)
    weekly_active_minutes: int = Field(default=0, ge=0)
    missed_deadlines: int = Field(default=0, ge=0)
    activity_streak_days: int = Field(default=0, ge=0)


class ExamEngineSnapshot(BaseModel):
    average_score: float = Field(default=0.0, ge=0.0, le=100.0)
    failed_attempts: int = Field(default=0, ge=0)
    no_show_count: int = Field(default=0, ge=0)
    trend_delta: float = Field(
        default=0.0,
        description="Positive if performance is improving, negative when degrading.",
    )


class RecommendationHooks(BaseModel):
    recommendation_service_input: dict[str, Any] = Field(default_factory=dict)
    ai_tutor_input: dict[str, Any] = Field(default_factory=dict)
    automation_tags: list[str] = Field(default_factory=list)


class LearningOptimizationInsight(BaseModel):
    tenant_id: str
    learner_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dropout_risk_score: float = Field(ge=0.0, le=100.0)
    engagement_risk_score: float = Field(ge=0.0, le=100.0)
    predicted_performance_score: float = Field(ge=0.0, le=100.0)
    risk_band: str
    risk_reasons: list[str] = Field(default_factory=list)
    recommendation_hooks: RecommendationHooks
    teacher_actions: list[str] = Field(default_factory=list)
    operations_actions: list[str] = Field(default_factory=list)
    owner_actions: list[str] = Field(default_factory=list)


class LearningOptimizationInsightRequest(BaseModel):
    system_of_record: SystemOfRecordSnapshot
    progress: ProgressSnapshot
    exam_engine: ExamEngineSnapshot
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "TeacherPerformanceSnapshot",
    "SystemOfRecordSnapshot",
    "ProgressSnapshot",
    "ExamEngineSnapshot",
    "RecommendationHooks",
    "LearningOptimizationInsight",
    "LearningOptimizationInsightRequest",
]
