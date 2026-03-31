from __future__ import annotations

from dataclasses import dataclass

from shared.models.event import PlatformEvent


@dataclass(frozen=True)
class StudentGuardianLink:
    student_id: str
    guardian_id: str
    relationship: str = "parent"


AttendanceCheckpoint = PlatformEvent
ProgressCheckpoint = PlatformEvent
PerformanceAlert = PlatformEvent
GuardianNotification = PlatformEvent
