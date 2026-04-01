from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

AttendanceStatus = Literal["present", "absent", "late", "excused"]


@dataclass(frozen=True)
class AttendanceRecord:
    attendance_id: str
    tenant_id: str
    branch_id: str
    batch_id: str
    class_session_id: str
    student_id: str
    teacher_id: str
    status: AttendanceStatus
    marked_at: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""
