from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from shared.models.school import GuardianNotification, PerformanceAlert


@dataclass
class SegmentNotificationService:
    """Config-driven guardian notification helper for segment behavior."""

    behavior_config: dict[str, bool] = field(default_factory=dict)
    _notification_log: list[GuardianNotification] = field(default_factory=list)
    entitlement: Callable[[str], bool] = field(default=lambda _capability_id: True)

    def _is_behavior_enabled(self, key: str, *, default: bool = False) -> bool:
        return bool(self.behavior_config.get(key, default))

    def notify_guardians_for_attendance(
        self,
        *,
        guardian_ids: list[str],
        student_id: str,
        course_id: str,
        attendance_state: str,
    ) -> list[GuardianNotification]:
        if not self._is_behavior_enabled("guardian_notifications_enabled"):
            raise RuntimeError("segment behavior disabled: guardian_notifications_enabled")
        is_enabled = self.entitlement("notification.guardian.attendance.send")
        if not is_enabled:
            raise PermissionError("capability denied: notification.guardian.attendance.send")
        message = f"Attendance update: student {student_id} is marked {attendance_state} in course {course_id}."
        return self._emit_batch(
            guardian_ids=guardian_ids,
            student_id=student_id,
            course_id=course_id,
            category="attendance",
            message=message,
        )

    def notify_guardians_for_performance_alert(
        self,
        *,
        guardian_ids: list[str],
        alert: PerformanceAlert,
    ) -> list[GuardianNotification]:
        if not self._is_behavior_enabled("guardian_notifications_enabled"):
            raise RuntimeError("segment behavior disabled: guardian_notifications_enabled")
        is_enabled = self.entitlement("notification.guardian.performance.send")
        if not is_enabled:
            raise PermissionError("capability denied: notification.guardian.performance.send")
        message = f"Performance alert ({alert.severity}): {alert.reason}"
        return self._emit_batch(
            guardian_ids=guardian_ids,
            student_id=alert.student_id,
            course_id=alert.course_id,
            category="performance",
            message=message,
        )

    def _emit_batch(
        self,
        *,
        guardian_ids: list[str],
        student_id: str,
        course_id: str,
        category: str,
        message: str,
    ) -> list[GuardianNotification]:
        created_at = datetime.utcnow()
        notifications: list[GuardianNotification] = []

        for idx, guardian_id in enumerate(sorted(set(guardian_ids)), start=1):
            notification = GuardianNotification(
                notification_id=f"{category}-{course_id}-{student_id}-{idx}",
                guardian_id=guardian_id,
                student_id=student_id,
                course_id=course_id,
                category=category,
                message=message,
                created_at=created_at,
            )
            self._notification_log.append(notification)
            notifications.append(notification)

        return notifications

    def notifications_for_guardian(self, guardian_id: str) -> list[GuardianNotification]:
        return [n for n in self._notification_log if n.guardian_id == guardian_id]


SchoolNotificationService = SegmentNotificationService
