from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from shared.models.student_profile import (
    AcademicState,
    AcademicStatus,
    AttendanceSummary,
    ContactInfo,
    FinancialState,
    GuardianContact,
    LedgerSummary,
    UnifiedStudentProfile,
)


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    tenant_id: str
    student_id: str
    amount: Decimal
    currency: str
    source_type: str
    source_ref: str
    posted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LifecycleTransitionError(ValueError):
    pass


__all__ = [
    "AcademicState",
    "AcademicStatus",
    "AttendanceSummary",
    "ContactInfo",
    "FinancialState",
    "GuardianContact",
    "LedgerEntry",
    "LedgerSummary",
    "LifecycleTransitionError",
    "UnifiedStudentProfile",
]
