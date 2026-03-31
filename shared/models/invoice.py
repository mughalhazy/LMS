from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    tenant_id: str
    amount: Decimal
    status: str
    created_at: datetime

    @staticmethod
    def issued(invoice_id: str, tenant_id: str, amount: Decimal) -> "Invoice":
        normalized_amount = Decimal(amount)
        if not invoice_id:
            raise ValueError("invoice_id is required")
        if not tenant_id:
            raise ValueError("tenant_id is required")
        if normalized_amount <= 0:
            raise ValueError("amount must be greater than zero")

        return Invoice(
            invoice_id=invoice_id,
            tenant_id=tenant_id,
            amount=normalized_amount,
            status="issued",
            created_at=datetime.now(timezone.utc),
        )
