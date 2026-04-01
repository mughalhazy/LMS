from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AcademicStatus(str, Enum):
    ENROLLED = "enrolled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DROPPED = "dropped"


@dataclass(frozen=True)
class ContactInfo:
    email: str = ""
    phone: str = ""
    address: str = ""


@dataclass(frozen=True)
class GuardianContact:
    name: str
    relation: str
    phone: str = ""
    email: str = ""


@dataclass(frozen=True)
class AcademicState:
    status: AcademicStatus = AcademicStatus.ENROLLED
    updated_at: datetime | None = None
    notes: str = ""


@dataclass(frozen=True)
class FinancialState:
    current_balance: Decimal = Decimal("0")
    dues_outstanding: Decimal = Decimal("0")
    payment_status: str = "due"
    installment_status: str = "not_started"


@dataclass(frozen=True)
class AttendanceSummary:
    attended_sessions: int = 0
    missed_sessions: int = 0
    attendance_rate: Decimal = Decimal("0")


@dataclass(frozen=True)
class LedgerSummary:
    total_invoiced: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    current_balance: Decimal = Decimal("0")
    last_invoice_id: str | None = None
    last_payment_id: str | None = None


@dataclass(frozen=True)
class UnifiedStudentProfile:
    student_id: str
    tenant_id: str
    full_name: str
    contact_info: ContactInfo = field(default_factory=ContactInfo)
    guardian_contacts: tuple[GuardianContact, ...] = ()
    academic_state: AcademicState = field(default_factory=AcademicState)
    financial_state: FinancialState = field(default_factory=FinancialState)
    lifecycle_state: str = "prospect"
    active_batches: tuple[str, ...] = ()
    assigned_teacher_ids: tuple[str, ...] = ()
    attendance_summary: AttendanceSummary = field(default_factory=AttendanceSummary)
    ledger_summary: LedgerSummary = field(default_factory=LedgerSummary)
    metadata: dict[str, str] = field(default_factory=dict)

    def with_balance(self, *, invoiced: Decimal, paid: Decimal, last_invoice_id: str | None, last_payment_id: str | None) -> "UnifiedStudentProfile":
        balance = invoiced - paid
        return replace(
            self,
            financial_state=replace(
                self.financial_state,
                current_balance=balance,
                dues_outstanding=max(balance, Decimal("0")),
                payment_status="paid" if balance <= 0 else "due",
            ),
            ledger_summary=LedgerSummary(
                total_invoiced=invoiced,
                total_paid=paid,
                current_balance=balance,
                last_invoice_id=last_invoice_id,
                last_payment_id=last_payment_id,
            ),
        )
