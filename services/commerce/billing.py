from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from .catalog import ProductType
from .checkout import Order, OrderStatus


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class InvoiceState(str, Enum):
    """Legacy state enum retained for compatibility with existing imports/tests."""

    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    VOIDED = "voided"
    OVERDUE = "overdue"


@dataclass(frozen=True, init=False)
class InvoiceRecord:
    invoice_id: str
    user_id: str
    order_id: str
    amount: Decimal
    status: InvoiceStatus
    currency: str
    invoice_type: str
    ledger_entry_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __init__(
        self,
        *,
        invoice_id: str,
        user_id: str | None = None,
        order_id: str,
        amount: Decimal,
        status: InvoiceStatus | None = None,
        currency: str,
        invoice_type: str,
        ledger_entry_id: str | None = None,
        created_at: datetime | None = None,
        tenant_id: str | None = None,
        state: InvoiceState | None = None,
    ) -> None:
        resolved_user_id = (user_id or tenant_id or "").strip()
        if not resolved_user_id:
            raise ValueError("user_id is required")
        resolved_status = status
        if resolved_status is None and state is not None:
            resolved_status = (
                InvoiceStatus.PAID
                if state == InvoiceState.PAID
                else InvoiceStatus.OVERDUE
                if state == InvoiceState.OVERDUE
                else InvoiceStatus.PENDING
            )
        if resolved_status is None:
            resolved_status = InvoiceStatus.PENDING

        object.__setattr__(self, "invoice_id", invoice_id)
        object.__setattr__(self, "user_id", resolved_user_id)
        object.__setattr__(self, "order_id", order_id)
        object.__setattr__(self, "amount", Decimal(amount))
        object.__setattr__(self, "status", resolved_status)
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "invoice_type", invoice_type)
        object.__setattr__(self, "ledger_entry_id", ledger_entry_id or f"led_{invoice_id}")
        object.__setattr__(self, "created_at", created_at or datetime.now(timezone.utc))

    @property
    def tenant_id(self) -> str:
        """Compatibility alias used by existing service boundaries."""
        return self.user_id

    @property
    def state(self) -> InvoiceState:
        """Compatibility alias used by older tests and integrations."""
        if self.status == InvoiceStatus.PAID:
            return InvoiceState.PAID
        if self.status == InvoiceStatus.OVERDUE:
            return InvoiceState.OVERDUE
        return InvoiceState.ISSUED


@dataclass(frozen=True)
class BillingLedgerEntry:
    ledger_entry_id: str
    invoice_id: str
    order_id: str
    user_id: str
    amount: Decimal
    source_system: str = "system-of-record"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BillingService:
    """Billing owns invoice lifecycle; no payment execution internals."""

    def __init__(self) -> None:
        self._invoices: dict[str, InvoiceRecord] = {}
        self._order_to_invoice: dict[str, str] = {}
        self._ledger_by_invoice: dict[str, BillingLedgerEntry] = {}

    def generate_invoice(self, order: Order) -> InvoiceRecord:
        if order.status not in {OrderStatus.PAID, OrderStatus.RECONCILED}:
            raise ValueError("cannot invoice order that is not paid")
        if order.order_id in self._order_to_invoice:
            return self._invoices[self._order_to_invoice[order.order_id]]

        next_index = len(self._invoices) + 1
        invoice_id = f"inv_{next_index}"
        ledger_entry = BillingLedgerEntry(
            ledger_entry_id=f"led_{invoice_id}",
            invoice_id=invoice_id,
            order_id=order.order_id,
            user_id=order.tenant_id,
            amount=Decimal(order.amount),
        )
        invoice = InvoiceRecord(
            invoice_id=invoice_id,
            user_id=order.tenant_id,
            order_id=order.order_id,
            amount=Decimal(order.amount),
            status=InvoiceStatus.PENDING,
            currency=order.currency,
            invoice_type="subscription" if order.product.product_type == ProductType.SUBSCRIPTION else "one_time",
            ledger_entry_id=ledger_entry.ledger_entry_id,
        )
        self._invoices[invoice.invoice_id] = invoice
        self._order_to_invoice[order.order_id] = invoice.invoice_id
        self._ledger_by_invoice[invoice.invoice_id] = ledger_entry
        return invoice

    def create_invoice_for_order(self, order: Order) -> InvoiceRecord:
        """Backward-compatible alias for previous method name."""
        return self.generate_invoice(order)

    def mark_paid(self, invoice_id: str) -> InvoiceRecord:
        current = self._invoices[invoice_id.strip()]
        paid = InvoiceRecord(**{**current.__dict__, "status": InvoiceStatus.PAID})
        self._invoices[paid.invoice_id] = paid
        return paid

    def mark_overdue(self, invoice_id: str) -> InvoiceRecord:
        current = self._invoices[invoice_id.strip()]
        overdue = InvoiceRecord(**{**current.__dict__, "status": InvoiceStatus.OVERDUE})
        self._invoices[overdue.invoice_id] = overdue
        return overdue

    def get_invoice(self, invoice_id: str) -> InvoiceRecord | None:
        return self._invoices.get(invoice_id.strip())

    def get_ledger_entry(self, invoice_id: str) -> BillingLedgerEntry | None:
        return self._ledger_by_invoice.get(invoice_id.strip())
