from __future__ import annotations

import importlib.util
import statistics
import sys
from pathlib import Path
from typing import Any

from shared.models.network_analytics import InstitutionBenchmark, StudentBenchmark, TeacherBenchmark
from shared.models.teacher_performance import TeacherPerformanceSnapshot

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
_AnalyticsModelsModule = _load_module("analytics_models_contract", "services/analytics-service/models.py")
LearningOptimizationInsight = _AnalyticsModelsModule.LearningOptimizationInsight
LearningOptimizationInsightRequest = _AnalyticsModelsModule.LearningOptimizationInsightRequest
RecommendationHooks = _AnalyticsModelsModule.RecommendationHooks


class AnalyticsService:
    """Analytics facade for economics and network-effects benchmarks."""

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

    def student_performance_benchmark(
        self,
        *,
        tenant_id: str,
        cohort_key: str,
        learner_count: int,
        average_score: float,
        completion_rate: float,
        attendance_rate: float,
        network_student_scores: tuple[float, ...] = (),
        comparison_window: str,
    ) -> StudentBenchmark:
        scores = [float(s) for s in network_student_scores]
        base = float(average_score)
        if not scores:
            percentile = 1.0
        else:
            percentile = sum(1 for s in scores if s <= base) / len(scores)
        insight = self._student_outcome_insight(base, float(completion_rate), float(attendance_rate), percentile)
        return StudentBenchmark(
            tenant_id=tenant_id,
            cohort_key=cohort_key,
            learner_count=learner_count,
            average_score=self._to_decimal(base),
            completion_rate=self._to_decimal(completion_rate),
            attendance_rate=self._to_decimal(attendance_rate),
            percentile_rank=self._to_decimal(percentile),
            outcome_insight=insight,
            comparison_window=comparison_window,
            metadata={"network_sample_size": len(scores), "anonymized": True},
        ).normalized()

    def teacher_performance_scoring(
        self,
        *,
        teacher_snapshot: TeacherPerformanceSnapshot,
        network_snapshots: tuple[TeacherPerformanceSnapshot, ...],
        benchmark_window: str,
        min_anonymized_sample: int = 3,
    ) -> TeacherBenchmark:
        tenant_safe = tuple(s for s in network_snapshots if s.teacher_id != teacher_snapshot.teacher_id)
        if len(tenant_safe) < min_anonymized_sample:
            raise ValueError("insufficient anonymized cross-tenant teacher sample")
        own_score = float(teacher_snapshot.overall_score())
        peer_scores = [float(snapshot.overall_score()) for snapshot in tenant_safe]
        percentile = sum(1 for score in peer_scores if score <= own_score) / len(peer_scores)
        peer_retention_avg = statistics.fmean(float(s.student_retention_score) for s in tenant_safe)
        outcome_avg = statistics.fmean(
            (float(s.completion_score) + float(s.engagement_score)) / 2.0 for s in tenant_safe
        )
        own_outcome = (float(teacher_snapshot.completion_score) + float(teacher_snapshot.engagement_score)) / 2.0
        compared_tenants = tuple({snapshot.tenant_id for snapshot in tenant_safe if snapshot.tenant_id != teacher_snapshot.tenant_id})

        return TeacherBenchmark(
            teacher_id=teacher_snapshot.teacher_id,
            home_tenant_id=teacher_snapshot.tenant_id,
            compared_tenant_ids=compared_tenants,
            performance_score=self._to_decimal(own_score),
            effectiveness_percentile=self._to_decimal(percentile),
            learner_outcome_delta=self._to_decimal(own_outcome - outcome_avg),
            retention_delta=self._to_decimal(float(teacher_snapshot.student_retention_score) - peer_retention_avg),
            benchmark_window=benchmark_window,
            metadata={"network_sample_size": len(peer_scores), "anonymized": True},
        ).normalized()

    def institution_benchmark(
        self,
        *,
        institution_key: str,
        student_benchmarks: tuple[StudentBenchmark, ...],
        teacher_benchmarks: tuple[TeacherBenchmark, ...],
        comparison_window: str,
        min_anonymized_tenants: int = 2,
    ) -> InstitutionBenchmark:
        tenant_ids = {benchmark.tenant_id for benchmark in student_benchmarks}
        tenant_ids.update(benchmark.home_tenant_id for benchmark in teacher_benchmarks)
        if len(tenant_ids) < min_anonymized_tenants:
            raise ValueError("insufficient participating tenants for anonymized institution benchmark")

        student_scores = [float(benchmark.average_score) for benchmark in student_benchmarks] or [0.0]
        teacher_scores = [float(benchmark.performance_score) for benchmark in teacher_benchmarks] or [0.0]
        total_learners = sum(benchmark.learner_count for benchmark in student_benchmarks)
        cohort_ranked = sorted(student_benchmarks, key=lambda b: b.percentile_rank, reverse=True)
        learning_outcome_index = (
            statistics.fmean(float(benchmark.completion_rate) for benchmark in student_benchmarks) * 0.6
            + statistics.fmean(float(benchmark.attendance_rate) for benchmark in student_benchmarks) * 0.4
            if student_benchmarks
            else 0.0
        )

        return InstitutionBenchmark(
            institution_key=institution_key,
            participating_tenants=tuple(tenant_ids),
            cohort_count=len(student_benchmarks),
            total_learners=total_learners,
            median_student_score=self._to_decimal(statistics.median(student_scores)),
            median_teacher_score=self._to_decimal(statistics.median(teacher_scores)),
            learning_outcome_index=self._to_decimal(learning_outcome_index),
            top_cohort_keys=tuple(benchmark.cohort_key for benchmark in cohort_ranked[:3]),
            comparison_window=comparison_window,
            anonymized=True,
            metadata={
                "student_sample": len(student_benchmarks),
                "teacher_sample": len(teacher_benchmarks),
                "cohort_comparison_enabled": True,
            },
        ).normalized()

    @staticmethod
    def _to_decimal(value: float) -> Any:
        from decimal import Decimal

        return Decimal(str(round(float(value), 4)))

    @staticmethod
    def _student_outcome_insight(score: float, completion: float, attendance: float, percentile: float) -> str:
        if completion >= 0.85 and attendance >= 0.85 and percentile >= 0.75:
            return "high_outcome_momentum"
        if completion < 0.6 or attendance < 0.6:
            return "intervention_recommended"
        if score >= 0.7 and percentile >= 0.5:
            return "stable_progress"
        return "monitoring_required"

    def generate_learning_optimization_insight(self, request: LearningOptimizationInsightRequest) -> LearningOptimizationInsight:
        sor = request.system_of_record
        progress = request.progress
        exam = request.exam_engine

        dropout_risk = min(1.0, max(0.0, (1 - (progress.completion_rate / 100)) * 0.35 + (exam.failed_attempts * 0.15) + (exam.no_show_count * 0.1) + (1 - (sor.attendance_rate / 100)) * 0.4))
        engagement_risk = min(1.0, max(0.0, (1 - min(progress.weekly_active_minutes, 300) / 300) * 0.5 + (progress.missed_deadlines * 0.1) + (0.2 if progress.activity_streak_days <= 1 else 0.0)))
        risk_band = "high" if max(dropout_risk, engagement_risk) >= 0.7 else ("medium" if max(dropout_risk, engagement_risk) >= 0.4 else "low")

        hooks = RecommendationHooks(
            recommendation_service_input={
                "tenant_id": sor.tenant_id,
                "learner_id": sor.learner_id,
                "risk_band": risk_band,
                "exam_trend_delta": exam.trend_delta,
                "metadata": dict(request.metadata),
            }
        )

        return LearningOptimizationInsight(
            tenant_id=sor.tenant_id,
            learner_id=sor.learner_id,
            risk_band=risk_band,
            dropout_risk_score=round(dropout_risk, 4),
            engagement_risk_score=round(engagement_risk, 4),
            recommendation_hooks=hooks,
            teacher_actions=("assign_remedial_practice", "schedule_parent_checkin"),
            operations_actions=("trigger_attendance_followup", "queue_fee_risk_review"),
            owner_actions=("monitor_retention_cohort", "review_tutor_allocation"),
        )
