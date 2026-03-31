from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from shared.models.school import PerformanceAlert


@dataclass
class SegmentAssessmentService:
    """Config-driven assessment extension that emits performance alerts."""

    behavior_config: dict[str, bool] = field(default_factory=dict)
    _scores: dict[str, list[float]] = field(default_factory=dict)
    _alerts: list[PerformanceAlert] = field(default_factory=list)
    entitlement: Callable[[str], bool] = field(default=lambda _capability_id: True)

    def record_score(
        self,
        *,
        student_id: str,
        course_id: str,
        score_percent: float,
        low_score_threshold: float = 60.0,
    ) -> PerformanceAlert | None:
        is_enabled = self.entitlement("assessment.score.record")
        if not is_enabled:
            raise PermissionError("capability denied: assessment.score.record")
        key = f"{course_id}:{student_id}"
        self._scores.setdefault(key, []).append(score_percent)

        if score_percent >= low_score_threshold:
            return None

        severity = "medium" if score_percent >= 50 else "high"
        if score_percent < 40:
            severity = "critical"

        alert = PerformanceAlert(
            alert_id=f"perf-{course_id}-{student_id}-{len(self._alerts)+1}",
            student_id=student_id,
            course_id=course_id,
            reason=f"Assessment score dropped below threshold ({score_percent:.1f}% < {low_score_threshold:.1f}%)",
            severity=severity,
            created_at=datetime.utcnow(),
            recommended_action="Schedule teacher-parent intervention and assign remediation plan.",
        )
        self._alerts.append(alert)
        return alert

    def alerts_for_student(self, *, student_id: str, course_id: str) -> list[PerformanceAlert]:
        return [a for a in self._alerts if a.student_id == student_id and a.course_id == course_id]


SchoolAssessmentService = SegmentAssessmentService
