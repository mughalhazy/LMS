from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal

LedgerEntryType = Literal["invoice", "payment", "adjustment", "refund", "due"]


@dataclass(frozen=True)
class LedgerEntry:
    ledger_entry_id: str
    student_id: str
    tenant_id: str
    entry_type: LedgerEntryType
    amount: Decimal
    currency: str
    reference_type: str
    reference_id: str
    status: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        *,
        ledger_entry_id: str,
        student_id: str,
        tenant_id: str,
        entry_type: LedgerEntryType,
        amount: Decimal,
        currency: str,
        reference_type: str,
        reference_id: str,
        status: str = "posted",
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "LedgerEntry":
        normalized_amount = Decimal(amount)
        if not ledger_entry_id:
            raise ValueError("ledger_entry_id is required")
        if not student_id:
            raise ValueError("student_id is required")
        if not tenant_id:
            raise ValueError("tenant_id is required")
        if not currency:
            raise ValueError("currency is required")
        if not reference_type:
            raise ValueError("reference_type is required")
        if not reference_id:
            raise ValueError("reference_id is required")

        return LedgerEntry(
            ledger_entry_id=ledger_entry_id,
            student_id=student_id,
            tenant_id=tenant_id,
            entry_type=entry_type,
            amount=normalized_amount,
            currency=currency,
            reference_type=reference_type,
            reference_id=reference_id,
            status=status,
            timestamp=timestamp or datetime.now(timezone.utc),
            metadata=metadata or {},
        )
