from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from shared.models.ledger import LedgerEntry


@dataclass(frozen=True)
class StudentLedgerSnapshot:
    tenant_id: str
    student_id: str
    balance: Decimal
    entries: tuple[LedgerEntry, ...]
