from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from shared.models.teacher_performance import TeacherPerformanceSnapshot


class AnalyticsService:
    """Read-model helpers for teacher performance analytics."""

    def list_teacher_performance(
        self,
        *,
        snapshots: tuple[TeacherPerformanceSnapshot, ...],
        tenant_id: str,
        teacher_id: str | None = None,
    ) -> tuple[TeacherPerformanceSnapshot, ...]:
        rows = [row for row in snapshots if row.tenant_id == tenant_id]
        if teacher_id is not None:
            rows = [row for row in rows if row.teacher_id == teacher_id]
        return tuple(sorted(rows, key=lambda row: row.captured_at))

    def get_teacher_performance_detail(
        self,
        *,
        snapshots: tuple[TeacherPerformanceSnapshot, ...],
        tenant_id: str,
        teacher_id: str,
    ) -> dict[str, object]:
        rows = self.list_teacher_performance(snapshots=snapshots, tenant_id=tenant_id, teacher_id=teacher_id)
        if not rows:
            raise KeyError("teacher performance not found")
        latest = rows[-1]
        return {
            "teacher_id": teacher_id,
            "tenant_id": tenant_id,
            "batch_ids": latest.batch_ids,
            "latest_performance_period": latest.performance_period,
            "latest_overall_score": latest.overall_score(),
            "snapshots": rows,
        }

    def summarize_cross_institution_performance(
        self,
        *,
        snapshots: tuple[TeacherPerformanceSnapshot, ...],
        teacher_id: str,
    ) -> dict[str, Decimal]:
        by_tenant: dict[str, list[Decimal]] = defaultdict(list)
        for snapshot in snapshots:
            if snapshot.teacher_id == teacher_id:
                by_tenant[snapshot.tenant_id].append(snapshot.overall_score())
        return {
            tenant_id: (sum(scores, Decimal("0")) / Decimal(len(scores))).quantize(Decimal("0.0001"))
            for tenant_id, scores in by_tenant.items()
        }
