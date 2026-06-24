from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class LedgerEntry:
    entry_id: str
    student_id: str
    tenant_id: str
    entry_type: str     # fee_charged | payment_received | credit_note | refund | adjustment
    amount: float
    currency: str
    reference: str
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StudentBalance:
    student_id: str
    tenant_id: str
    currency: str
    total_owed: float = 0.0
    total_paid: float = 0.0
    balance: float = 0.0        # positive = owes money, negative = credit
    overdue: bool = False
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FeeObligation:
    obligation_id: str
    student_id: str
    tenant_id: str
    enrollment_id: str
    amount: float
    currency: str
    due_date: datetime
    status: str = "pending"     # pending | paid | overdue | waived
    paid_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
