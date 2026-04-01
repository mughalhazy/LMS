from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AnalyticsModule = _load_module("analytics_network_validation_module", "services/analytics-service/service.py")
ModelModule = _load_module("teacher_performance_validation_module", "shared/models/teacher_performance.py")

AnalyticsService = AnalyticsModule.AnalyticsService
TeacherPerformanceSnapshot = ModelModule.TeacherPerformanceSnapshot


def _snapshot(teacher_id: str, tenant_id: str, completion: str, engagement: str, retention: str) -> TeacherPerformanceSnapshot:
    return TeacherPerformanceSnapshot(
        teacher_id=teacher_id,
        tenant_id=tenant_id,
        batch_ids=("batch_1",),
        attendance_quality_score=Decimal("0.80"),
        student_retention_score=Decimal(retention),
        completion_score=Decimal(completion),
        engagement_score=Decimal(engagement),
        performance_period="2026-Q1",
    )


def test_student_benchmark_is_anonymized_and_tenant_safe() -> None:
    analytics = AnalyticsService()
    benchmark = analytics.student_performance_benchmark(
        tenant_id="tenant_a",
        cohort_key="grade_9",
        learner_count=140,
        average_score=0.82,
        completion_rate=0.87,
        attendance_rate=0.86,
        network_student_scores=(0.5, 0.75, 0.80, 0.81, 0.9),
        comparison_window="2026-Q1",
    )

    assert benchmark.tenant_id == "tenant_a"
    assert benchmark.metadata["anonymized"] is True
    assert benchmark.percentile_rank >= Decimal("0.5")
    assert benchmark.outcome_insight in {"high_outcome_momentum", "stable_progress"}


def test_teacher_scoring_requires_anonymized_cross_tenant_sample() -> None:
    analytics = AnalyticsService()
    teacher = _snapshot("teacher_1", "tenant_home", "0.90", "0.88", "0.84")
    peers = (
        _snapshot("teacher_2", "tenant_x", "0.81", "0.79", "0.78"),
        _snapshot("teacher_3", "tenant_y", "0.76", "0.82", "0.74"),
        _snapshot("teacher_4", "tenant_z", "0.85", "0.77", "0.80"),
    )

    scored = analytics.teacher_performance_scoring(
        teacher_snapshot=teacher,
        network_snapshots=peers,
        benchmark_window="2026-Q1",
    )
    assert scored.home_tenant_id == "tenant_home"
    assert len(scored.compared_tenant_ids) == 3
    assert scored.metadata["anonymized"] is True


def test_institution_benchmark_compares_cohorts_without_tenant_leakage() -> None:
    analytics = AnalyticsService()
    cohorts = (
        analytics.student_performance_benchmark(
            tenant_id="tenant_a",
            cohort_key="cohort_a",
            learner_count=55,
            average_score=0.74,
            completion_rate=0.71,
            attendance_rate=0.76,
            network_student_scores=(0.61, 0.65, 0.77),
            comparison_window="2026-Q1",
        ),
        analytics.student_performance_benchmark(
            tenant_id="tenant_b",
            cohort_key="cohort_b",
            learner_count=62,
            average_score=0.83,
            completion_rate=0.88,
            attendance_rate=0.84,
            network_student_scores=(0.68, 0.81, 0.86),
            comparison_window="2026-Q1",
        ),
    )

    teachers = (
        analytics.teacher_performance_scoring(
            teacher_snapshot=_snapshot("teacher_a", "tenant_a", "0.87", "0.86", "0.82"),
            network_snapshots=(
                _snapshot("peer_1", "tenant_b", "0.76", "0.75", "0.74"),
                _snapshot("peer_2", "tenant_c", "0.71", "0.80", "0.72"),
                _snapshot("peer_3", "tenant_d", "0.79", "0.78", "0.77"),
            ),
            benchmark_window="2026-Q1",
        ),
    )

    institution = analytics.institution_benchmark(
        institution_key="network_north",
        student_benchmarks=cohorts,
        teacher_benchmarks=teachers,
        comparison_window="2026-Q1",
    )

    assert institution.anonymized is True
    assert institution.total_learners == 117
    assert institution.cohort_count == 2
    assert institution.top_cohort_keys
