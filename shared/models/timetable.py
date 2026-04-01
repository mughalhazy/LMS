from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum


class TimetableSlotStatus(str, Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TimetableSlot:
    tenant_id: str
    branch_id: str
    slot_id: str
    batch_id: str
    teacher_id: str
    day_of_week: str
    start_time: time
    end_time: time
    room_or_virtual_link: str
    recurrence_rule: str
    status: TimetableSlotStatus = TimetableSlotStatus.SCHEDULED


@dataclass(frozen=True)
class AttendanceSessionEvent:
    event_id: str
    tenant_id: str
    branch_id: str
    batch_id: str
    slot_id: str
    learner_id: str
    scheduled_for: datetime
    status: str = "pending"
