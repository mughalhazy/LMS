from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

AttendanceState = Literal["present", "late", "absent", "excused"]
CheckpointKind = Literal["lesson", "attendance", "assignment", "assessment"]
AlertSeverity = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class StudentGuardianLink:
    student_id: str
    guardian_id: str
    relationship: str = "parent"


@dataclass(frozen=True)
class AttendanceCheckpoint:
    checkpoint_id: str
    student_id: str
    course_id: str
    occurred_at: datetime
    state: AttendanceState
    period_key: str


@dataclass(frozen=True)
class ProgressCheckpoint:
    checkpoint_id: str
    student_id: str
    course_id: str
    kind: CheckpointKind
    completion_ratio: float
    occurred_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PerformanceAlert:
    alert_id: str
    student_id: str
    course_id: str
    reason: str
    severity: AlertSeverity
    created_at: datetime
    recommended_action: str


@dataclass(frozen=True)
class GuardianNotification:
    notification_id: str
    guardian_id: str
    student_id: str
    course_id: str
    category: Literal["attendance", "performance", "progress"]
    message: str
    created_at: datetime
