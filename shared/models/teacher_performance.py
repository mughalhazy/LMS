from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class TeacherPerformanceSnapshot:
    """Reusable teacher-performance view for tenant and cross-institution analytics."""

    teacher_id: str
    tenant_id: str
    batch_ids: tuple[str, ...]
    attendance_quality_score: Decimal
    student_retention_score: Decimal
    completion_score: Decimal
    engagement_score: Decimal
    performance_period: str
    metadata: dict[str, Any] = field(default_factory=dict)
    captured_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def batch_id(self) -> str:
        """Backward-compatible accessor for single-batch consumers."""
        return self.batch_ids[0] if self.batch_ids else ""

    def overall_score(self) -> Decimal:
        weighted = (
            self.attendance_quality_score * Decimal("0.30")
            + self.student_retention_score * Decimal("0.25")
            + self.completion_score * Decimal("0.25")
            + self.engagement_score * Decimal("0.20")
        )
        return weighted.quantize(Decimal("0.0001"))
