from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LearnerRiskSignals:
    engagement_score: float
    recent_activity: float
    previous_activity: float
    activity_change_percent: float
    assessment_average_percent: float | None = None
    last_activity_at: str | None = None


@dataclass(frozen=True)
class LearnerRiskInsight:
    learner_id: str
    risk_score: float
    alerts: list[str] = field(default_factory=list)
    signals: LearnerRiskSignals | None = None


@dataclass(frozen=True)
class LearnerRiskInsightSummary:
    total_learners: int
    high_risk_learners: int
    medium_risk_learners: int
    alert_totals: dict[str, int] = field(default_factory=dict)
