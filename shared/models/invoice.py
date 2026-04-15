from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

InvoiceStatus = Literal["pending", "paid", "overdue"]


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    user_id: str
    order_id: str
    amount: Decimal
    status: InvoiceStatus
    created_at: datetime

    @staticmethod
    def create(
        *,
        invoice_id: str,
        user_id: str,
        order_id: str,
        amount: Decimal,
        status: InvoiceStatus = "pending",
    ) -> "Invoice":
        normalized_amount = Decimal(amount)
        if not invoice_id:
            raise ValueError("invoice_id is required")
        if not user_id:
            raise ValueError("user_id is required")
        if not order_id:
            raise ValueError("order_id is required")
        if normalized_amount <= 0:
            raise ValueError("amount must be greater than zero")

        return Invoice(
            invoice_id=invoice_id,
            user_id=user_id,
            order_id=order_id,
            amount=normalized_amount,
            status=status,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def issued(invoice_id: str, tenant_id: str, amount: Decimal) -> "Invoice":
        """Backward-compatible constructor for existing callers.

        Legacy callers use tenant_id and no order context; map those values into
        the richer Invoice shape expected by billing lifecycle flows.
        """
        return Invoice.create(
            invoice_id=invoice_id,
            user_id=tenant_id,
            order_id=f"legacy:{invoice_id}",
            amount=amount,
            status="pending",
        )

    @property
    def tenant_id(self) -> str:
        """Backward-compatible alias for older service boundaries."""
        return self.user_id
