from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from shared.models.branch import Branch, BranchStatus
from shared.models.timetable import TimetableSlotStatus


class TeacherRole(str, Enum):
    PRIMARY = "primary_teacher"
    ASSISTANT = "assistant_teacher"


@dataclass(frozen=True)
class Batch:
    tenant_id: str
    branch_id: str
    batch_id: str
    academy_id: str
    title: str
    start_date: date
    end_date: date
    learner_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TeacherAssignment:
    tenant_id: str
    branch_id: str
    batch_id: str
    teacher_id: str
    role: TeacherRole = TeacherRole.PRIMARY
    teacher_owned_batch: bool = False
    ownership_metadata: dict[str, str] = field(default_factory=dict)
    assigned_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class TimetableSlot:
    tenant_id: str
    branch_id: str
    batch_id: str
    slot_id: str
    teacher_id: str
    day_of_week: str
    start_time: time
    end_time: time
    room_or_virtual_link: str
    recurrence_rule: str
    status: TimetableSlotStatus = TimetableSlotStatus.SCHEDULED


@dataclass(frozen=True)
class AttendanceRecord:
    attendance_id: str
    tenant_id: str
    branch_id: str
    batch_id: str
    class_session_id: str
    student_id: str
    teacher_id: str
    status: str
    notes: str = ""
    marked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class FeePayment:
    tenant_id: str
    learner_id: str
    payment_id: str
    amount: Decimal
    paid_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RevenueShareAgreement:
    tenant_id: str
    batch_id: str
    teacher_id: str
    share_ratio: Decimal


@dataclass(frozen=True)
class TeacherPerformanceSnapshot:
    tenant_id: str
    batch_id: str
    teacher_id: str
    attendance_rate: Decimal
    completion_rate: Decimal
    learner_satisfaction: Decimal
    captured_at: datetime = field(default_factory=datetime.utcnow)

    def score(self) -> Decimal:
        return (
            (self.attendance_rate * Decimal("0.40"))
            + (self.completion_rate * Decimal("0.35"))
            + (self.learner_satisfaction * Decimal("0.25"))
        ).quantize(Decimal("0.0001"))


@dataclass(frozen=True)
class TeacherPayoutRecord:
    tenant_id: str
    batch_id: str
    teacher_id: str
    invoice_id: str
    revenue_amount: Decimal
    payout_amount: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)
