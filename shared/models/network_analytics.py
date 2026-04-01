from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def _q4(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class StudentBenchmark:
    """Anonymized student benchmark inside cohort/institution aggregates."""

    tenant_id: str
    cohort_key: str
    learner_count: int
    average_score: Decimal
    completion_rate: Decimal
    attendance_rate: Decimal
    percentile_rank: Decimal
    outcome_insight: str
    comparison_window: str
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def normalized(self) -> "StudentBenchmark":
        return StudentBenchmark(
            tenant_id=self.tenant_id.strip(),
            cohort_key=self.cohort_key.strip(),
            learner_count=max(self.learner_count, 0),
            average_score=_q4(self.average_score),
            completion_rate=_q4(self.completion_rate),
            attendance_rate=_q4(self.attendance_rate),
            percentile_rank=_q4(self.percentile_rank),
            outcome_insight=self.outcome_insight.strip(),
            comparison_window=self.comparison_window.strip(),
            metadata=dict(self.metadata),
            generated_at=self.generated_at,
        )


@dataclass(frozen=True)
class TeacherBenchmark:
    """Cross-tenant teacher benchmark with de-identified comparative context."""

    teacher_id: str
    home_tenant_id: str
    compared_tenant_ids: tuple[str, ...]
    performance_score: Decimal
    effectiveness_percentile: Decimal
    learner_outcome_delta: Decimal
    retention_delta: Decimal
    benchmark_window: str
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def normalized(self) -> "TeacherBenchmark":
        return TeacherBenchmark(
            teacher_id=self.teacher_id.strip(),
            home_tenant_id=self.home_tenant_id.strip(),
            compared_tenant_ids=tuple(sorted({tid.strip() for tid in self.compared_tenant_ids if tid.strip()})),
            performance_score=_q4(self.performance_score),
            effectiveness_percentile=_q4(self.effectiveness_percentile),
            learner_outcome_delta=_q4(self.learner_outcome_delta),
            retention_delta=_q4(self.retention_delta),
            benchmark_window=self.benchmark_window.strip(),
            metadata=dict(self.metadata),
            generated_at=self.generated_at,
        )


@dataclass(frozen=True)
class InstitutionBenchmark:
    """Institution-level benchmark and cohort comparison rollup."""

    institution_key: str
    participating_tenants: tuple[str, ...]
    cohort_count: int
    total_learners: int
    median_student_score: Decimal
    median_teacher_score: Decimal
    learning_outcome_index: Decimal
    top_cohort_keys: tuple[str, ...] = ()
    comparison_window: str = ""
    anonymized: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def normalized(self) -> "InstitutionBenchmark":
        return InstitutionBenchmark(
            institution_key=self.institution_key.strip(),
            participating_tenants=tuple(sorted({tid.strip() for tid in self.participating_tenants if tid.strip()})),
            cohort_count=max(self.cohort_count, 0),
            total_learners=max(self.total_learners, 0),
            median_student_score=_q4(self.median_student_score),
            median_teacher_score=_q4(self.median_teacher_score),
            learning_outcome_index=_q4(self.learning_outcome_index),
            top_cohort_keys=tuple(key.strip() for key in self.top_cohort_keys if key.strip()),
            comparison_window=self.comparison_window.strip(),
            anonymized=self.anonymized,
            metadata=dict(self.metadata),
            generated_at=self.generated_at,
        )
