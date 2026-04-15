from __future__ import annotations

import importlib.util
import statistics
import sys
from dataclasses import dataclass
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


@dataclass
class InsightEnvelope:
    """BC-ANALYTICS-01: required output envelope for all operator-facing analytics.

    Every metric surfaced to operators must carry: trend vs prior period, context
    sentence, and at least one suggested action. Raw values alone are not permitted
    on operator-facing surfaces (per BC-ANALYTICS-01 §1).
    """
    metric: str
    current_value: float | str
    trend: str           # e.g. "down_14.0pct_vs_prior", "up_8.3pct_vs_prior", "no_prior_data"
    context: str
    suggested_action: str
    action_link: str = ""


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
        # BC-ANALYTICS-02: retain per-(tenant, cohort, period) metric snapshots for
        # prior-period trend comparison. Keys: (tenant_id, cohort_key, period_key).
        self._period_history: dict[tuple[str, str, str], dict[str, float]] = {}
        # CAP-LEARNING-ANALYTICS: raw learner events for analytics computation.
        # Keys: (tenant_id, learner_id) → list of event dicts.
        self._learner_events: dict[tuple[str, str], list[dict[str, Any]]] = {}
        # MO-036 / Phase E: BC-BRANCH-01 — per-branch metric snapshots.
        # Keys: (tenant_id, branch_id, period_key) → {metric: value}.
        self._branch_snapshots: dict[tuple[str, str, str], dict[str, float]] = {}
        # MO-040 / Phase E: exam performance history.
        # Keys: (tenant_id, exam_id) → list of {score, passed, session_id, at}.
        self._exam_results: dict[tuple[str, str], list[dict[str, Any]]] = {}

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

    # ------------------------------------------------------------------ #
    # BC-ANALYTICS-02 — Prior-period snapshot storage + trend labels     #
    # ------------------------------------------------------------------ #

    def record_period_snapshot(
        self,
        *,
        tenant_id: str,
        cohort_key: str,
        period_key: str,
        metrics: dict[str, float],
    ) -> None:
        """Store metric snapshot for this period so the next call can produce a trend.

        Call after computing a benchmark, passing the same period key used in
        comparison_window. The next call with a new period key can then reference
        this snapshot to produce a prior-period trend label per BC-ANALYTICS-02.
        """
        self._period_history[(tenant_id, cohort_key, period_key)] = dict(metrics)

    def _prior_snapshot(self, tenant_id: str, cohort_key: str, period_key: str) -> dict[str, float] | None:
        return self._period_history.get((tenant_id, cohort_key, period_key))

    @staticmethod
    def _compute_trend_label(current: float, prior: float | None) -> str:
        """BC-ANALYTICS-02: produce human-readable trend label vs prior period value.

        Returns 'no_prior_data' when no snapshot exists — spec requires this to be
        surfaced explicitly rather than silently omitted.
        """
        if prior is None:
            return "no_prior_data"
        if prior == 0:
            return "new_data_no_baseline"
        delta_pct = round((current - prior) / abs(prior) * 100, 1)
        direction = "up" if delta_pct >= 0 else "down"
        return f"{direction}_{abs(delta_pct):.1f}pct_vs_prior"

    # ------------------------------------------------------------------ #
    # BC-ANALYTICS-01 — Insight envelope builder                          #
    # ------------------------------------------------------------------ #

    def build_insight_envelope(
        self,
        *,
        metric: str,
        current_value: float | str,
        prior_value: float | None = None,
        context: str = "",
        suggested_action: str = "",
        action_link: str = "",
    ) -> InsightEnvelope:
        """BC-ANALYTICS-01: wrap any metric value in the required insight envelope.

        Every operator-facing metric MUST be wrapped before surfacing. Raw values
        without trend/context/suggested_action are not compliant.
        """
        trend = self._compute_trend_label(
            float(current_value) if prior_value is not None else 0.0,
            prior_value,
        )
        return InsightEnvelope(
            metric=metric,
            current_value=current_value,
            trend=trend,
            context=context or "No additional context available for this metric.",
            suggested_action=suggested_action or "Review metric and determine if action is required.",
            action_link=action_link,
        )

    def student_performance_insight(
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
        prior_period_key: str | None = None,
    ) -> InsightEnvelope:
        """BC-ANALYTICS-01 + BC-ANALYTICS-02 compliant student performance output.

        Computes benchmark, retrieves prior-period snapshot for trend, wraps in
        InsightEnvelope. Also stores current snapshot for future trend computation.

        Use this instead of student_performance_benchmark() for operator-facing surfaces.
        student_performance_benchmark() is preserved for internal/raw-data consumers.
        """
        benchmark = self.student_performance_benchmark(
            tenant_id=tenant_id,
            cohort_key=cohort_key,
            learner_count=learner_count,
            average_score=average_score,
            completion_rate=completion_rate,
            attendance_rate=attendance_rate,
            network_student_scores=network_student_scores,
            comparison_window=comparison_window,
        )

        prior = self._prior_snapshot(tenant_id, cohort_key, prior_period_key or "")
        prior_completion = prior.get("completion_rate") if prior else None
        prior_score = prior.get("average_score") if prior else None

        # Choose the primary metric for trend — completion_rate is most operator-relevant
        trend = self._compute_trend_label(float(benchmark.completion_rate), prior_completion)

        # Build context sentence from outcome insight + score comparison
        score_context = ""
        if prior_score is not None:
            score_delta = round((float(benchmark.average_score) - prior_score) * 100, 1)
            score_context = f" Score moved {'+' if score_delta >= 0 else ''}{score_delta}% vs prior period."

        context_map = {
            "high_outcome_momentum": f"Cohort {cohort_key} is performing strongly — completion and attendance both above 85%.{score_context}",
            "intervention_recommended": f"Cohort {cohort_key} needs intervention — completion or attendance below 60%.{score_context}",
            "stable_progress": f"Cohort {cohort_key} is on track with stable progress.{score_context}",
            "monitoring_required": f"Cohort {cohort_key} requires monitoring — mixed signals detected.{score_context}",
        }
        context = context_map.get(benchmark.outcome_insight, f"Cohort {cohort_key} performance data available.{score_context}")

        action_map = {
            "high_outcome_momentum": "Continue current approach — consider sharing as a best-practice cohort.",
            "intervention_recommended": "Schedule instructor review for this cohort and identify struggling learners.",
            "stable_progress": "No immediate action required — monitor for changes next period.",
            "monitoring_required": "Review individual learner data to identify who needs support.",
        }
        suggested_action = action_map.get(benchmark.outcome_insight, "Review cohort data and take appropriate action.")

        # Store snapshot for future prior-period comparison (BC-ANALYTICS-02)
        self.record_period_snapshot(
            tenant_id=tenant_id,
            cohort_key=cohort_key,
            period_key=comparison_window,
            metrics={
                "completion_rate": float(benchmark.completion_rate),
                "average_score": float(benchmark.average_score),
                "attendance_rate": float(benchmark.attendance_rate),
            },
        )

        return InsightEnvelope(
            metric="completion_rate",
            current_value=float(benchmark.completion_rate),
            trend=trend,
            context=context,
            suggested_action=suggested_action,
            action_link=f"/cohorts/{cohort_key}?tenant={tenant_id}&filter=performance",
        )

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

    # ------------------------------------------------------------------ #
    # CAP-LEARNING-ANALYTICS — Learner event ingestion + analytics       #
    # CGAP-031                                                            #
    # ------------------------------------------------------------------ #

    def ingest_learner_event(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """CAP-LEARNING-ANALYTICS: store a learner event for analytics computation.

        Supported event_type values: progress.updated, assessment.completed,
        assessment.failed, enrollment.completed, session.attended, session.missed.
        """
        key = (tenant_id.strip(), learner_id.strip())
        self._learner_events.setdefault(key, []).append(
            {"event_type": event_type, "payload": dict(payload)}
        )

    def learner_analytics(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        prior_period_key: str | None = None,
    ) -> InsightEnvelope:
        """CAP-LEARNING-ANALYTICS + BC-ANALYTICS-01/02: per-learner insight envelope.

        Computes completion_rate, engagement, and assessment performance from
        ingested events. Returns InsightEnvelope with trend vs prior period.
        """
        events = self._learner_events.get((tenant_id.strip(), learner_id.strip()), [])

        total = len(events)
        completed = sum(1 for e in events if e["event_type"] in {"enrollment.completed", "progress.updated"} and e["payload"].get("completion_pct", 0) >= 100)
        attended = sum(1 for e in events if e["event_type"] == "session.attended")
        missed = sum(1 for e in events if e["event_type"] == "session.missed")
        assessments = [e["payload"].get("score", 0) for e in events if e["event_type"] in {"assessment.completed"}]

        completion_rate = round(completed / max(total, 1), 4) if total else 0.0
        attendance_rate = round(attended / max(attended + missed, 1), 4) if (attended + missed) else 0.0
        avg_assessment = round(sum(assessments) / len(assessments), 4) if assessments else 0.0

        prior = self._prior_snapshot(tenant_id, learner_id, prior_period_key or "")
        prior_completion = prior.get("completion_rate") if prior else None
        trend = self._compute_trend_label(completion_rate, prior_completion)

        at_risk = completion_rate < 0.4 or attendance_rate < 0.5
        context = (
            f"Learner {learner_id} is at risk — completion {round(completion_rate*100,1)}%, attendance {round(attendance_rate*100,1)}%."
            if at_risk else
            f"Learner {learner_id} is on track — completion {round(completion_rate*100,1)}%, assessment avg {round(avg_assessment*100,1)}%."
        )
        suggested_action = (
            "Send re-engagement message and assign catch-up content."
            if at_risk else
            "No immediate action required — monitor next period."
        )

        self.record_period_snapshot(
            tenant_id=tenant_id,
            cohort_key=learner_id,
            period_key=prior_period_key or "current",
            metrics={"completion_rate": completion_rate, "attendance_rate": attendance_rate, "avg_assessment": avg_assessment},
        )

        return InsightEnvelope(
            metric="completion_rate",
            current_value=completion_rate,
            trend=trend,
            context=context,
            suggested_action=suggested_action,
            action_link=f"/learners/{learner_id}?tenant={tenant_id}",
        )

    def cohort_analytics(
        self,
        *,
        tenant_id: str,
        cohort_key: str,
        learner_ids: tuple[str, ...] | list[str],
        prior_period_key: str | None = None,
    ) -> InsightEnvelope:
        """CAP-LEARNING-ANALYTICS: cohort-level aggregated insight envelope."""
        envelopes = [
            self.learner_analytics(tenant_id=tenant_id, learner_id=lid, prior_period_key=prior_period_key)
            for lid in learner_ids
        ]
        if not envelopes:
            return self.build_insight_envelope(
                metric="cohort_completion_rate",
                current_value=0.0,
                context=f"No learner data available for cohort {cohort_key}.",
                suggested_action="Enroll learners and collect progress data.",
            )

        avg_completion = round(sum(float(e.current_value) for e in envelopes) / len(envelopes), 4)
        prior = self._prior_snapshot(tenant_id, cohort_key, prior_period_key or "")
        prior_completion = prior.get("completion_rate") if prior else None
        trend = self._compute_trend_label(avg_completion, prior_completion)

        at_risk_count = sum(1 for e in envelopes if float(e.current_value) < 0.4)
        context = (
            f"Cohort {cohort_key}: avg completion {round(avg_completion*100,1)}%. "
            f"{at_risk_count} of {len(envelopes)} learners at risk."
        )
        suggested_action = (
            f"Immediate intervention needed for {at_risk_count} at-risk learner(s)."
            if at_risk_count > 0 else
            "Cohort on track — no immediate action required."
        )

        self.record_period_snapshot(
            tenant_id=tenant_id,
            cohort_key=cohort_key,
            period_key=prior_period_key or "current",
            metrics={"completion_rate": avg_completion},
        )

        return InsightEnvelope(
            metric="cohort_completion_rate",
            current_value=avg_completion,
            trend=trend,
            context=context,
            suggested_action=suggested_action,
            action_link=f"/cohorts/{cohort_key}?tenant={tenant_id}",
        )

    def at_risk_learner_signals(
        self,
        *,
        tenant_id: str,
        learner_ids: tuple[str, ...] | list[str],
    ) -> tuple[dict[str, Any], ...]:
        """CAP-LEARNING-ANALYTICS: identify at-risk learners from ingested events.

        Returns a tuple of dicts per at-risk learner: learner_id, risk_level, signals.
        """
        signals: list[dict[str, Any]] = []
        for lid in learner_ids:
            envelope = self.learner_analytics(tenant_id=tenant_id, learner_id=lid)
            completion = float(envelope.current_value)
            if completion < 0.4:
                risk_level = "critical"
            elif completion < 0.6:
                risk_level = "elevated"
            else:
                continue
            signals.append({
                "learner_id": lid,
                "risk_level": risk_level,
                "completion_rate": completion,
                "trend": envelope.trend,
                "suggested_action": envelope.suggested_action,
            })
        return tuple(signals)

    # ------------------------------------------------------------------ #
    # CAP-EXECUTIVE-REPORTING — Tenant/academy-level rollup reports       #
    # CGAP-032                                                            #
    # ------------------------------------------------------------------ #

    def executive_summary_report(
        self,
        *,
        tenant_id: str,
        report_period: str,
        cohort_keys: tuple[str, ...] | list[str] | None = None,
    ) -> InsightEnvelope:
        """CAP-EXECUTIVE-REPORTING + BC-ANALYTICS-01/02: tenant-level executive summary.

        Aggregates stored period snapshots for the tenant across all or specified cohorts.
        Returns InsightEnvelope with trend, context, and suggested action.
        """
        # Collect all stored snapshots for this tenant
        tenant_snapshots = {
            cohort_key: metrics
            for (tid, cohort_key), metrics in self._period_history.items()
            if tid == tenant_id
        }

        if cohort_keys:
            relevant = {k: v for k, v in tenant_snapshots.items() if k in cohort_keys}
        else:
            relevant = tenant_snapshots

        if not relevant:
            return self.build_insight_envelope(
                metric="tenant_completion_rate",
                current_value=0.0,
                context=f"No analytics data available for tenant {tenant_id} — {report_period}.",
                suggested_action="Ensure learner progress events are being captured.",
            )

        all_completions = [v.get("completion_rate", 0.0) for v in relevant.values()]
        avg_completion = round(sum(all_completions) / len(all_completions), 4)
        at_risk_cohorts = [k for k, v in relevant.items() if v.get("completion_rate", 1.0) < 0.6]

        # Retrieve prior period for trend
        prior = self._prior_snapshot(tenant_id, "__executive__", report_period)
        trend = self._compute_trend_label(avg_completion, prior.get("avg_completion") if prior else None)

        context = (
            f"Tenant {tenant_id} — {report_period}: avg completion {round(avg_completion*100,1)}% "
            f"across {len(relevant)} cohort(s). "
            + (f"{len(at_risk_cohorts)} cohort(s) below 60% threshold." if at_risk_cohorts else "All cohorts above 60%.")
        )
        suggested_action = (
            f"Review and intervene in {len(at_risk_cohorts)} underperforming cohort(s): {', '.join(at_risk_cohorts[:3])}."
            if at_risk_cohorts else
            "Academy performance is healthy — no immediate action required."
        )

        self.record_period_snapshot(
            tenant_id=tenant_id,
            cohort_key="__executive__",
            period_key=report_period,
            metrics={"avg_completion": avg_completion, "cohort_count": float(len(relevant))},
        )

        return InsightEnvelope(
            metric="tenant_completion_rate",
            current_value=avg_completion,
            trend=trend,
            context=context,
            suggested_action=suggested_action,
            action_link=f"/executive?tenant={tenant_id}&period={report_period}",
        )

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

    # ------------------------------------------------------------------
    # BC-LEARN-01: At-risk → automatic intervention trigger — MO-030 / Phase C
    # at_risk_learner_signals() detects risk but previously emitted nothing.
    # trigger_at_risk_interventions() wraps it, then emits
    # "workflow.trigger.learner_intervention" per detected risk so that the
    # workflow engine can automatically assign the next best action without
    # any teacher or admin query.
    # ------------------------------------------------------------------

    def trigger_at_risk_interventions(
        self,
        *,
        tenant_id: str,
        learner_ids: tuple[str, ...] | list[str],
        event_publisher: Any | None = None,
    ) -> list[dict[str, Any]]:
        """Detect at-risk learners and emit workflow trigger events (BC-LEARN-01).

        For each at-risk learner identified by at_risk_learner_signals():
        - Emits "workflow.trigger.learner_intervention" event with risk details
        - Returns list of trigger records for audit / caller confirmation

        Args:
            tenant_id: Tenant context.
            learner_ids: All active learner IDs to evaluate.
            event_publisher: Optional callable(event_dict) for platform event bus.
                             If None, falls back to the shared envelope.

        Returns:
            List of trigger dicts emitted — one per at-risk learner.
        """
        signals = self.at_risk_learner_signals(tenant_id=tenant_id, learner_ids=learner_ids)
        if not signals:
            return []

        triggers: list[dict[str, Any]] = []
        for signal in signals:
            trigger_event: dict[str, Any] = {
                "event_type": "workflow.trigger.learner_intervention",
                "tenant_id": tenant_id,
                "learner_id": signal["learner_id"],
                "risk_level": signal["risk_level"],
                "completion_rate": signal["completion_rate"],
                "trend": signal["trend"],
                "suggested_action": signal["suggested_action"],
                "source": "analytics.at_risk_detection",
            }
            triggers.append(trigger_event)

            # Emit to event bus — best-effort
            _publish = event_publisher
            if _publish is None:
                try:
                    from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
                    _publish = publish_event
                except Exception:
                    _publish = None
            if _publish is not None:
                try:
                    _publish(trigger_event)
                except Exception:
                    pass

        return triggers

    # ------------------------------------------------------------------
    # MO-036 / Phase E — BC-BRANCH-01: Multi-branch analytics aggregation
    # HQ users need cross-branch visibility by default. This extends the
    # analytics service with branch-level snapshot storage and a
    # cross_branch_analytics() aggregator that produces an InsightEnvelope
    # for HQ-level reporting without requiring separate queries per branch.
    # ------------------------------------------------------------------

    def record_branch_snapshot(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        period_key: str,
        metrics: dict[str, float],
    ) -> None:
        """Store branch-level metric snapshot for cross-branch trend comparison (BC-BRANCH-01 / MO-036)."""
        self._branch_snapshots[(tenant_id, branch_id, period_key)] = dict(metrics)

    def cross_branch_analytics(
        self,
        *,
        tenant_id: str,
        branch_ids: list[str] | None = None,
        period_key: str,
    ) -> InsightEnvelope:
        """Aggregate analytics across all (or specified) branches for HQ view (BC-BRANCH-01 / MO-036).

        HQ users (scope=TENANT) see a unified view: average completion, revenue,
        attendance across all branches with inter-branch comparison.

        Args:
            tenant_id: Tenant context.
            branch_ids: Restrict to these branches. None = all branches for tenant.
            period_key: Reporting period key (e.g. "2026-04", "2026-W15").

        Returns:
            InsightEnvelope with aggregated metric, worst/best branch callout,
            trend vs prior period, and a suggested action.
        """
        # Collect all stored branch snapshots for this tenant + period
        relevant: dict[str, dict[str, float]] = {
            bid: metrics
            for (tid, bid, pk), metrics in self._branch_snapshots.items()
            if tid == tenant_id and pk == period_key
            and (branch_ids is None or bid in branch_ids)
        }

        if not relevant:
            return self.build_insight_envelope(
                metric="cross_branch_completion_rate",
                current_value=0.0,
                context=(
                    f"No branch analytics data for tenant {tenant_id} — {period_key}. "
                    "Ensure branch-level learning events are being captured."
                ),
                suggested_action="Review branch data collection and re-run after period end.",
            )

        completions = {bid: m.get("completion_rate", 0.0) for bid, m in relevant.items()}
        avg_completion = round(sum(completions.values()) / len(completions), 4)
        best_branch = max(completions, key=completions.__getitem__)
        worst_branch = min(completions, key=completions.__getitem__)

        # Prior period trend
        prior_key = f"__cross_branch_{period_key}__"
        prior = self._period_history.get((tenant_id, "__hq__", prior_key))
        trend = self._compute_trend_label(avg_completion, prior.get("avg_completion") if prior else None)
        # Store for next period comparison
        self._period_history[(tenant_id, "__hq__", prior_key)] = {"avg_completion": avg_completion}

        below_avg = [bid for bid, c in completions.items() if c < avg_completion]
        context = (
            f"Cross-branch — {period_key}: avg completion {round(avg_completion*100,1)}% "
            f"across {len(relevant)} branch(es). "
            f"Best: {best_branch} ({round(completions[best_branch]*100,1)}%). "
            f"Worst: {worst_branch} ({round(completions[worst_branch]*100,1)}%). "
            + (f"{len(below_avg)} branch(es) below average." if below_avg else "All branches at or above average.")
        )
        suggested_action = (
            f"Review {worst_branch} — completion rate "
            f"{round(completions[worst_branch]*100,1)}% is the lowest across all branches. "
            "Consider reallocating teaching resources or running a targeted intervention."
            if len(relevant) > 1 else
            f"Single branch {best_branch} — expand to more branches to unlock cross-branch benchmarking."
        )

        return InsightEnvelope(
            metric="cross_branch_completion_rate",
            current_value=round(avg_completion, 4),
            trend=trend,
            context=context,
            suggested_action=suggested_action,
            action_link=f"/analytics/cross-branch?tenant={tenant_id}&period={period_key}",
        )

    # ------------------------------------------------------------------
    # MO-040 / Phase E — Exam performance trend analytics
    # The exam engine has full session data but no analytics surface.
    # ingest_exam_result() stores outcomes; exam_performance_insight()
    # produces BC-ANALYTICS-01/02 compliant InsightEnvelope so operators
    # see pass rates, trends, and suggested actions — not raw scores.
    # ------------------------------------------------------------------

    def ingest_exam_result(
        self,
        *,
        tenant_id: str,
        exam_id: str,
        session_id: str,
        score: float,
        passed: bool,
        at: str | None = None,
    ) -> None:
        """Store a single exam session result for trend computation (MO-040 / Phase E)."""
        key = (tenant_id, exam_id)
        self._exam_results.setdefault(key, []).append({
            "session_id": session_id,
            "score": score,
            "passed": passed,
            "at": at or "",
        })

    def exam_performance_insight(
        self,
        *,
        tenant_id: str,
        exam_id: str,
        period_key: str,
    ) -> InsightEnvelope:
        """BC-ANALYTICS-01/02 exam performance insight — pass rate, trend, suggested action (MO-040).

        Returns an InsightEnvelope with pass_rate, trend vs prior period, context
        sentence, and at least one suggested action. Raw scores alone are never surfaced.
        """
        results = self._exam_results.get((tenant_id, exam_id), [])
        if not results:
            return self.build_insight_envelope(
                metric="exam_pass_rate",
                current_value=0.0,
                context=f"No exam results recorded for exam {exam_id} in tenant {tenant_id} — {period_key}.",
                suggested_action="Ensure exam sessions are submitting results to the analytics service.",
            )

        total = len(results)
        passed_count = sum(1 for r in results if r["passed"])
        pass_rate = round(passed_count / total, 4)
        avg_score = round(sum(r["score"] for r in results) / total, 2)

        prior = self._period_history.get((tenant_id, exam_id, period_key))
        trend = self._compute_trend_label(pass_rate, prior.get("pass_rate") if prior else None)
        # Store for next period
        self._period_history[(tenant_id, exam_id, period_key)] = {"pass_rate": pass_rate, "avg_score": avg_score}

        fail_count = total - passed_count
        context = (
            f"Exam {exam_id} — {period_key}: {passed_count}/{total} passed "
            f"({round(pass_rate*100,1)}%). Avg score: {avg_score}. "
            + (f"{fail_count} learner(s) did not pass." if fail_count > 0 else "All learners passed.")
        )

        if pass_rate < 0.5:
            suggested_action = (
                f"{fail_count} learner(s) failed — pass rate {round(pass_rate*100,1)}% is critically low. "
                "Review exam difficulty, identify weak topic clusters, and schedule remediation sessions."
            )
        elif pass_rate < 0.75:
            suggested_action = (
                f"Pass rate {round(pass_rate*100,1)}% is below target. "
                "Consider targeted review sessions for learners who scored below 60%."
            )
        else:
            suggested_action = (
                f"Pass rate {round(pass_rate*100,1)}% is healthy. "
                "Monitor the {fail_count} non-passing learner(s) for re-attempt support."
                if fail_count > 0 else
                "Exam performance is strong — no immediate action required."
            )

        return InsightEnvelope(
            metric="exam_pass_rate",
            current_value=pass_rate,
            trend=trend,
            context=context,
            suggested_action=suggested_action,
            action_link=f"/analytics/exams/{exam_id}?tenant={tenant_id}&period={period_key}",
        )
