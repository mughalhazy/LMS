from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def _q4(value: float | Decimal) -> Decimal:
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    return decimal_value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class TeacherSignal:
    teacher_id: str
    tenant_id: str
    assessment_quality: float
    learner_outcome: float
    retention_rate: float
    engagement_index: float


@dataclass(frozen=True)
class TeacherScore:
    teacher_id: str
    tenant_id: str
    weighted_score: Decimal
    percentile_rank: Decimal
    benchmark_window: str
    aggregation_safe: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchmarkSummary:
    benchmark_window: str
    participating_tenant_count: int
    teacher_sample_size: int
    network_average_score: Decimal
    network_median_score: Decimal
    p10_score: Decimal
    p50_score: Decimal
    p90_score: Decimal
    aggregation_safe: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "TeacherSignal",
    "TeacherScore",
    "BenchmarkSummary",
    "_q4",
]
