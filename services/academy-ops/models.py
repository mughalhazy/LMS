from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from shared.models.branch import Branch, BranchStatus
from shared.models.timetable import TimetableSlot, TimetableSlotStatus
from shared.models.teacher_performance import TeacherPerformanceSnapshot


class BatchStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"


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
    teacher_ids: tuple[str, ...] = ()
    course_id: str = ""
    timetable_id: str = ""
    capacity: int = 1
    status: BatchStatus = BatchStatus.ACTIVE
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def student_ids(self) -> tuple[str, ...]:
        return self.learner_ids


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
class AttendanceRecord:
    """MS-SOR-01 (MS§6) boundary: academy-ops is the ORIGINATING service for attendance data.

    This record is the operational working copy created by the teacher/academy-ops flow.
    The authoritative cross-service record is written to system-of-record immediately
    after creation via AcademyOpsService.mark_attendance() → sor.record_attendance().
    academy-ops retains this copy for local attendance queries only.
    """

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

    @property
    def learner_id(self) -> str:
        return self.student_id


@dataclass(frozen=True)
class FeePayment:
    """MS-SOR-01 (MS§6) boundary: academy-ops is the ORIGINATING service for fee payment data.

    This record is the operational working copy created by the fee-management flow.
    The authoritative financial ledger entry is written to system-of-record immediately
    after creation via AcademyOpsService.record_fee_payment() → sor.post_payment_to_ledger().
    academy-ops retains this copy for local fee queries and teacher payout calculations only.
    """

    tenant_id: str
    learner_id: str
    payment_id: str
    amount: Decimal
    batch_id: str | None = None
    attribution_metadata: dict[str, str] = field(default_factory=dict)
    paid_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RevenueShareAgreement:
    tenant_id: str
    batch_id: str
    teacher_id: str
    share_ratio: Decimal


@dataclass(frozen=True)
class TeacherPayoutRecord:
    tenant_id: str
    batch_id: str
    teacher_id: str
    invoice_id: str
    revenue_amount: Decimal
    payout_amount: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)
