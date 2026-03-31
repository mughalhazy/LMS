from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from shared.models.school import PerformanceAlert


@dataclass
class SchoolAssessmentService:
    """Assessment extension that emits school-oriented performance alerts."""

    _scores: dict[str, list[float]] = field(default_factory=dict)
    _alerts: list[PerformanceAlert] = field(default_factory=list)

    def record_score(
        self,
        *,
        student_id: str,
        course_id: str,
        score_percent: float,
        low_score_threshold: float = 60.0,
    ) -> PerformanceAlert | None:
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
