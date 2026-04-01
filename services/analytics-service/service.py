from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from .models import (
    LearningOptimizationInsight,
    LearningOptimizationInsightRequest,
    RecommendationHooks,
)

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_OwnerEconomicsModule = _load_module("owner_economics_module_for_analytics", "services/commerce/owner_economics.py")
OwnerEconomicsEngine = _OwnerEconomicsModule.OwnerEconomicsEngine


class AnalyticsService:
    """Analytics facade that delegates owner economics to canonical commerce engine."""

    def __init__(self) -> None:
        self._owner_economics_engine = OwnerEconomicsEngine()
        self._learning_optimization_store: dict[tuple[str, str], LearningOptimizationInsight] = {}

    def compute_owner_economics(
        self,
        *,
        tenant_id: str,
        reporting_period: str,
        ledger_entries: tuple[Any, ...],
        commerce_invoices: tuple[Any, ...],
        academy_batches: tuple[Any, ...],
        academy_branches: tuple[Any, ...],
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        return self._owner_economics_engine.compute_profitability_snapshot(
            tenant_id=tenant_id,
            reporting_period=reporting_period,
            ledger_entries=ledger_entries,
            commerce_invoices=commerce_invoices,
            batches=academy_batches,
            branches=academy_branches,
            metadata=metadata,
        )

    def generate_learning_optimization_insight(
        self,
        req: LearningOptimizationInsightRequest,
    ) -> LearningOptimizationInsight:
        system_of_record = req.system_of_record
        progress = req.progress
        exam = req.exam_engine

        dropout_score = 0.0
        engagement_score = 0.0
        risk_reasons: list[str] = []

        if system_of_record.lifecycle_state in {"paused", "dropped"}:
            dropout_score += 35
            risk_reasons.append(f"lifecycle:{system_of_record.lifecycle_state}")
        if system_of_record.attendance_rate < 80:
            dropout_score += min(25, (80 - system_of_record.attendance_rate) * 0.7)
            risk_reasons.append("attendance_decline")
        if progress.completion_rate < 55:
            dropout_score += min(20, (55 - progress.completion_rate) * 0.6)
            risk_reasons.append("low_completion")
        if progress.missed_deadlines > 0:
            dropout_score += min(15, progress.missed_deadlines * 3)
            risk_reasons.append("missed_deadlines")
        if exam.no_show_count > 0:
            dropout_score += min(10, exam.no_show_count * 2)
            risk_reasons.append("exam_no_show")

        if progress.weekly_active_minutes < 90:
            engagement_score += min(30, (90 - progress.weekly_active_minutes) * 0.25)
            risk_reasons.append("low_weekly_active_time")
        if progress.activity_streak_days < 3:
            engagement_score += (3 - progress.activity_streak_days) * 6
            risk_reasons.append("inconsistent_learning_habit")
        if exam.trend_delta < 0:
            engagement_score += min(18, abs(exam.trend_delta) * 2.5)
            risk_reasons.append("exam_trend_down")
        if exam.failed_attempts > 1:
            engagement_score += min(12, (exam.failed_attempts - 1) * 3)
            risk_reasons.append("repeated_exam_failures")

        dropout_score = round(min(100.0, dropout_score), 2)
        engagement_score = round(min(100.0, engagement_score), 2)

        predicted_performance = round(
            max(
                0.0,
                min(
                    100.0,
                    (exam.average_score * 0.55)
                    + (progress.completion_rate * 0.3)
                    + (min(progress.weekly_active_minutes, 300) / 3 * 0.1)
                    + (system_of_record.attendance_rate * 0.05)
                    - (dropout_score * 0.12)
                    - (engagement_score * 0.08),
                ),
            ),
            2,
        )

        risk_band = "high" if max(dropout_score, engagement_score) >= 70 else "medium" if max(dropout_score, engagement_score) >= 40 else "low"
        hooks = self._build_recommendation_hooks(
            tenant_id=system_of_record.tenant_id,
            learner_id=system_of_record.learner_id,
            dropout_score=dropout_score,
            engagement_score=engagement_score,
            predicted_performance=predicted_performance,
            risk_band=risk_band,
        )
        insight = LearningOptimizationInsight(
            tenant_id=system_of_record.tenant_id,
            learner_id=system_of_record.learner_id,
            dropout_risk_score=dropout_score,
            engagement_risk_score=engagement_score,
            predicted_performance_score=predicted_performance,
            risk_band=risk_band,
            risk_reasons=sorted(set(risk_reasons)),
            recommendation_hooks=hooks,
            teacher_actions=self._teacher_actions(risk_band, predicted_performance),
            operations_actions=self._operations_actions(risk_band, system_of_record.overdue_balance),
            owner_actions=self._owner_actions(risk_band, predicted_performance, req.metadata),
        )
        self._learning_optimization_store[(insight.tenant_id, insight.learner_id)] = insight
        return insight

    def get_learning_optimization_insight(self, *, tenant_id: str, learner_id: str) -> LearningOptimizationInsight | None:
        return self._learning_optimization_store.get((tenant_id, learner_id))

    @staticmethod
    def _build_recommendation_hooks(
        *,
        tenant_id: str,
        learner_id: str,
        dropout_score: float,
        engagement_score: float,
        predicted_performance: float,
        risk_band: str,
    ) -> RecommendationHooks:
        return RecommendationHooks(
            recommendation_service_input={
                "tenant_id": tenant_id,
                "learner_id": learner_id,
                "risk_band": risk_band,
                "dropoff_rate": round(dropout_score / 100, 2),
                "engagement_score": max(0.0, round(100 - engagement_score, 2)),
                "completion_rate": round(max(0.0, predicted_performance - 8), 2),
            },
            ai_tutor_input={
                "tenant_id": tenant_id,
                "learner_id": learner_id,
                "suggested_focus": "exam-readiness" if predicted_performance < 60 else "skill-transfer",
                "trend_direction": "down" if engagement_score >= 40 else "stable",
            },
            automation_tags=[f"risk:{risk_band}", "learning-optimization", "integrated-insight"],
        )

    @staticmethod
    def _teacher_actions(risk_band: str, predicted_performance: float) -> list[str]:
        actions = [
            "Assign a focused weekly intervention plan with 2 measurable checkpoints.",
            "Review learner misconceptions from latest exams and reinforce with guided practice.",
        ]
        if risk_band == "high":
            actions.append("Schedule 1:1 support session within 48 hours and notify guardian/sponsor where applicable.")
        if predicted_performance < 50:
            actions.append("Move learner to remediation path before next high-stakes assessment.")
        return actions

    @staticmethod
    def _operations_actions(risk_band: str, overdue_balance: float) -> list[str]:
        actions = [
            "Track this learner in weekly retention operations review.",
            "Verify nudges and reminders are active for this learner cohort.",
        ]
        if overdue_balance > 0:
            actions.append("Coordinate finance outreach to resolve overdue balance blocking engagement.")
        if risk_band in {"high", "medium"}:
            actions.append("Escalate to learner success specialist for proactive outreach.")
        return actions

    @staticmethod
    def _owner_actions(risk_band: str, predicted_performance: float, metadata: dict[str, Any]) -> list[str]:
        cohort_id = metadata.get("cohort_id", "unknown-cohort")
        actions = [
            f"Monitor cohort {cohort_id} risk concentration in owner dashboard.",
            "Review ROI impact of interventions in monthly performance business review.",
        ]
        if risk_band == "high" or predicted_performance < 55:
            actions.append("Approve additional coaching capacity for high-risk cohort segment.")
        return actions
