from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from .checkout import Order, OrderStatus
from .models import BillingCycle, ProductType, SubscriptionPlan


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class InvoiceState(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    OVERDUE = "overdue"
    VOIDED = "voided"


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

    def __init__(self, *, invoice_id: str, user_id: str | None = None, order_id: str, amount: Decimal, status: InvoiceStatus | None = None, currency: str, invoice_type: str, ledger_entry_id: str | None = None, created_at: datetime | None = None, tenant_id: str | None = None, state: InvoiceState | None = None) -> None:
        resolved_user_id = (user_id or tenant_id or "").strip()
        if not resolved_user_id:
            raise ValueError("user_id is required")
        resolved_status = status
        if resolved_status is None and state is not None:
            resolved_status = InvoiceStatus.PAID if state == InvoiceState.PAID else InvoiceStatus.OVERDUE if state == InvoiceState.OVERDUE else InvoiceStatus.PENDING
        resolved_status = resolved_status or InvoiceStatus.PENDING
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
        return self.user_id

    @property
    def state(self) -> InvoiceState:
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


@dataclass(frozen=True)
class SubscriptionBillingContract:
    subscription_id: str
    tenant_id: str
    plan_type: str
    amount: Decimal
    currency: str
    billing_cycle: BillingCycle
    status: str = "active"


class BillingService:
    def __init__(self) -> None:
        self._invoices: dict[str, InvoiceRecord] = {}
        self._order_to_invoice: dict[str, str] = {}
        self._ledger_by_invoice: dict[str, BillingLedgerEntry] = {}
        self._recurring_charges: dict[str, list[InvoiceRecord]] = {}

    def generate_invoice(self, order: Order) -> InvoiceRecord:
        if order.status not in {OrderStatus.PAID, OrderStatus.RECONCILED}:
            raise ValueError("cannot invoice order that is not paid")
        if order.order_id in self._order_to_invoice:
            return self._invoices[self._order_to_invoice[order.order_id]]

        invoice_id = f"inv_{len(self._invoices) + 1}"
        invoice = InvoiceRecord(
            invoice_id=invoice_id,
            user_id=order.tenant_id,
            order_id=order.order_id,
            amount=order.amount,
            status=InvoiceStatus.PENDING,
            currency=order.currency,
            state=InvoiceState.ISSUED,
            invoice_type="subscription" if order.product.type == ProductType.SUBSCRIPTION else "one_time",
        )
        ledger = BillingLedgerEntry(
            ledger_entry_id=invoice.ledger_entry_id,
            invoice_id=invoice.invoice_id,
            order_id=order.order_id,
            user_id=order.tenant_id,
            amount=order.amount,
        )
        self._invoices[invoice.invoice_id] = invoice
        self._order_to_invoice[order.order_id] = invoice.invoice_id
        self._ledger_by_invoice[invoice.invoice_id] = ledger
        return invoice

    def create_invoice_for_order(self, order: Order) -> InvoiceRecord:
        return self.generate_invoice(order)

    def get_invoice(self, invoice_id: str) -> InvoiceRecord | None:
        return self._invoices.get(invoice_id.strip())

    def create_recurring_charge(self, *, subscription_id: str, plan: SubscriptionPlan, tenant_id: str) -> InvoiceRecord:
        normalized = plan.normalized()
        invoice = InvoiceRecord(
            invoice_id=f"inv_{len(self._invoices) + 1}",
            order_id=f"recurring:{subscription_id}:{len(self._recurring_charges.get(subscription_id, [])) + 1}",
            tenant_id=tenant_id,
            amount=normalized.price,
            currency="USD",
            state=InvoiceState.ISSUED,
            invoice_type=f"subscription_recurring:{normalized.billing_cycle.value}",
        )
        self._invoices[invoice.invoice_id] = invoice
        self._recurring_charges.setdefault(subscription_id, []).append(invoice)
        return invoice

    def recurring_charges_for_subscription(self, subscription_id: str) -> list[InvoiceRecord]:
        return list(self._recurring_charges.get(subscription_id.strip(), []))
