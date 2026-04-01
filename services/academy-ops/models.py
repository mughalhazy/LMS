from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from shared.models.timetable import AttendanceSessionEvent, TimetableSlot, TimetableSlotStatus


@dataclass(frozen=True)
class Branch:
    tenant_id: str
    branch_id: str
    academy_id: str
    name: str
    timezone: str
    active: bool = True


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
    assigned_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class AttendanceRecord:
    tenant_id: str
    branch_id: str
    batch_id: str
    learner_id: str
    slot_id: str
    present: bool


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


__all__ = [
    "AttendanceRecord",
    "AttendanceSessionEvent",
    "Batch",
    "Branch",
    "FeePayment",
    "RevenueShareAgreement",
    "TeacherAssignment",
    "TeacherPerformanceSnapshot",
    "TeacherPayoutRecord",
    "TimetableSlot",
    "TimetableSlotStatus",
]
