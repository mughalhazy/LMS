from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from .catalog import ProductType
from .checkout import Order, OrderStatus
from .models import SubscriptionPlan


class InvoiceState(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    VOIDED = "voided"


@dataclass(frozen=True)
class InvoiceRecord:
    invoice_id: str
    order_id: str
    tenant_id: str
    amount: Decimal
    currency: str
    state: InvoiceState
    invoice_type: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BillingService:
    """Billing owns invoice lifecycle; no payment execution internals."""

    def __init__(self) -> None:
        self._invoices: dict[str, InvoiceRecord] = {}
        self._order_to_invoice: dict[str, str] = {}
        self._recurring_charges: dict[str, list[InvoiceRecord]] = {}

    def create_invoice_for_order(self, order: Order) -> InvoiceRecord:
        if order.status not in {OrderStatus.PAID, OrderStatus.RECONCILED}:
            raise ValueError("cannot invoice order that is not paid")
        if order.order_id in self._order_to_invoice:
            return self._invoices[self._order_to_invoice[order.order_id]]

        invoice = InvoiceRecord(
            invoice_id=f"inv_{len(self._invoices) + 1}",
            order_id=order.order_id,
            tenant_id=order.tenant_id,
            amount=Decimal(order.amount),
            currency=order.currency,
            state=InvoiceState.ISSUED,
            invoice_type="subscription" if order.product.type == ProductType.SUBSCRIPTION else "one_time",
        )
        self._invoices[invoice.invoice_id] = invoice
        self._order_to_invoice[order.order_id] = invoice.invoice_id
        return invoice

    def mark_paid(self, invoice_id: str) -> InvoiceRecord:
        current = self._invoices[invoice_id.strip()]
        paid = InvoiceRecord(**{**current.__dict__, "state": InvoiceState.PAID})
        self._invoices[paid.invoice_id] = paid
        return paid

    def get_invoice(self, invoice_id: str) -> InvoiceRecord | None:
        return self._invoices.get(invoice_id.strip())

    def create_recurring_charge(self, *, subscription_id: str, plan: SubscriptionPlan, tenant_id: str) -> InvoiceRecord:
        normalized_plan = plan.normalized()
        invoice = InvoiceRecord(
            invoice_id=f"inv_{len(self._invoices) + 1}",
            order_id=f"recurring:{subscription_id.strip()}:{len(self._recurring_charges.get(subscription_id.strip(), [])) + 1}",
            tenant_id=tenant_id.strip(),
            amount=normalized_plan.price,
            currency="USD",
            state=InvoiceState.ISSUED,
            invoice_type=f"subscription_recurring:{normalized_plan.billing_cycle.value}",
        )
        self._invoices[invoice.invoice_id] = invoice
        self._recurring_charges.setdefault(subscription_id.strip(), []).append(invoice)
        return invoice

    def recurring_charges_for_subscription(self, subscription_id: str) -> list[InvoiceRecord]:
        return list(self._recurring_charges.get(subscription_id.strip(), []))
