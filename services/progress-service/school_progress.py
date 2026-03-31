from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from shared.models.school import AttendanceCheckpoint, ProgressCheckpoint


@dataclass
class SegmentProgressService:
    """Config-driven progress service that enables segment behavior through flags."""

    behavior_config: dict[str, bool] = field(default_factory=dict)
    _attendance_checkpoints: list[AttendanceCheckpoint] = field(default_factory=list)
    _progress_checkpoints: list[ProgressCheckpoint] = field(default_factory=list)
    entitlement: Callable[[str], bool] = field(default=lambda _capability_id: True)

    def _is_behavior_enabled(self, key: str, *, default: bool = False) -> bool:
        return bool(self.behavior_config.get(key, default))

    def record_attendance_checkpoint(
        self,
        *,
        checkpoint_id: str,
        student_id: str,
        course_id: str,
        state: str,
        period_key: str,
        occurred_at: datetime | None = None,
    ) -> AttendanceCheckpoint:
        if not self._is_behavior_enabled("attendance_enabled"):
            raise RuntimeError("segment behavior disabled: attendance_enabled")
        is_enabled = self.entitlement("progress.attendance.record")
        if not is_enabled:
            raise PermissionError("capability denied: progress.attendance.record")
        checkpoint = AttendanceCheckpoint(
            checkpoint_id=checkpoint_id,
            student_id=student_id,
            course_id=course_id,
            occurred_at=occurred_at or datetime.utcnow(),
            state=state,
            period_key=period_key,
        )
        self._attendance_checkpoints.append(checkpoint)

        completion_ratio = 1.0 if state in {"present", "late"} else 0.0
        self._progress_checkpoints.append(
            ProgressCheckpoint(
                checkpoint_id=f"{checkpoint_id}:progress",
                student_id=student_id,
                course_id=course_id,
                kind="attendance",
                completion_ratio=completion_ratio,
                occurred_at=checkpoint.occurred_at,
                metadata={"attendance_state": state, "period_key": period_key},
            )
        )
        return checkpoint

    def attendance_ratio(self, *, student_id: str, course_id: str) -> float:
        if not self._is_behavior_enabled("attendance_enabled"):
            raise RuntimeError("segment behavior disabled: attendance_enabled")
        is_enabled = self.entitlement("progress.attendance.read")
        if not is_enabled:
            raise PermissionError("capability denied: progress.attendance.read")
        relevant = [
            c
            for c in self._attendance_checkpoints
            if c.student_id == student_id and c.course_id == course_id
        ]
        if not relevant:
            return 0.0

        present_like = sum(1 for c in relevant if c.state in {"present", "late"})
        return present_like / len(relevant)

    def checkpoints_for_student(self, *, student_id: str, course_id: str) -> list[ProgressCheckpoint]:
        return [
            c
            for c in self._progress_checkpoints
            if c.student_id == student_id and c.course_id == course_id
        ]


SchoolProgressService = SegmentProgressService
