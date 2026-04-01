from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum

from .catalog import ProductType
from .checkout import Order, OrderStatus


class InvoiceState(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    OVERDUE = "overdue"
    VOIDED = "voided"


class BillingCycle(str, Enum):
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    ANNUAL = "annual"


@dataclass(frozen=True)
class InvoiceRecord:
    invoice_id: str
    order_id: str
    tenant_id: str
    amount: Decimal
    currency: str
    state: InvoiceState
    invoice_type: str
    billing_cycle: BillingCycle = BillingCycle.ONE_TIME
    subscription_id: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    due_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class SubscriptionBillingContract:
    subscription_id: str
    tenant_id: str
    plan_type: str
    amount: Decimal
    currency: str
    billing_cycle: BillingCycle
    status: str = "active"
    next_billing_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payment_terms_days: int = 15
    last_billed_at: datetime | None = None


class BillingService:
    """Billing owns invoice lifecycle; no payment execution internals."""

    def __init__(self) -> None:
        self._invoices: dict[str, InvoiceRecord] = {}
        self._order_to_invoice: dict[str, str] = {}
        self._subscription_contracts: dict[str, SubscriptionBillingContract] = {}
        self._subscription_period_index: dict[tuple[str, datetime], str] = {}

    def create_invoice_for_order(self, order: Order) -> InvoiceRecord:
        if order.status not in {OrderStatus.PAID, OrderStatus.RECONCILED}:
            raise ValueError("cannot invoice order that is not paid")
        if order.order_id in self._order_to_invoice:
            return self._invoices[self._order_to_invoice[order.order_id]]

        now = datetime.now(timezone.utc)
        is_subscription = order.product.product_type == ProductType.SUBSCRIPTION
        billing_cycle = BillingCycle.MONTHLY if is_subscription else BillingCycle.ONE_TIME
        due_at = self._derive_due_at(now=now, billing_cycle=billing_cycle)
        subscription_id = f"sub_{order.tenant_id}_{order.product.product_id}" if is_subscription else None
        invoice = InvoiceRecord(
            invoice_id=f"inv_{len(self._invoices) + 1}",
            order_id=order.order_id,
            tenant_id=order.tenant_id,
            amount=Decimal(order.amount),
            currency=order.currency,
            state=InvoiceState.ISSUED,
            invoice_type="subscription" if is_subscription else "one_time",
            billing_cycle=billing_cycle,
            subscription_id=subscription_id,
            period_start=now if is_subscription else None,
            period_end=self._period_end_for_cycle(now, billing_cycle) if is_subscription else None,
            due_at=due_at,
        )
        self._invoices[invoice.invoice_id] = invoice
        self._order_to_invoice[order.order_id] = invoice.invoice_id
        if is_subscription and subscription_id:
            self._subscription_contracts[subscription_id] = SubscriptionBillingContract(
                subscription_id=subscription_id,
                tenant_id=order.tenant_id,
                plan_type=order.product.metadata.get("plan_type", "pro"),
                amount=Decimal(order.amount),
                currency=order.currency,
                billing_cycle=billing_cycle,
                next_billing_at=invoice.period_end or now,
                last_billed_at=now,
            )
        return invoice

    def mark_paid(self, invoice_id: str) -> InvoiceRecord:
        current = self._invoices[invoice_id.strip()]
        paid = InvoiceRecord(**{**current.__dict__, "state": InvoiceState.PAID})
        self._invoices[paid.invoice_id] = paid
        return paid

    def get_invoice(self, invoice_id: str) -> InvoiceRecord | None:
        return self._invoices.get(invoice_id.strip())

    def sync_subscription_contract(
        self,
        *,
        subscription_id: str,
        tenant_id: str,
        plan_type: str,
        amount: Decimal,
        currency: str,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        next_billing_at: datetime | None = None,
        status: str = "active",
    ) -> SubscriptionBillingContract:
        normalized_subscription = SubscriptionBillingContract(
            subscription_id=subscription_id.strip(),
            tenant_id=tenant_id.strip(),
            plan_type=plan_type.strip().lower(),
            amount=Decimal(amount),
            currency=currency.strip().upper(),
            billing_cycle=billing_cycle,
            status=status.strip().lower(),
            next_billing_at=next_billing_at or datetime.now(timezone.utc),
        )
        self._subscription_contracts[normalized_subscription.subscription_id] = normalized_subscription
        return normalized_subscription

    def execute_scheduled_billing(self, *, now: datetime | None = None) -> list[InvoiceRecord]:
        run_at = now or datetime.now(timezone.utc)
        issued: list[InvoiceRecord] = []
        for subscription in list(self._subscription_contracts.values()):
            if subscription.status != "active":
                continue
            if subscription.next_billing_at > run_at:
                continue
            period_start = subscription.next_billing_at
            dedupe_key = (subscription.subscription_id, period_start)
            existing_id = self._subscription_period_index.get(dedupe_key)
            if existing_id:
                issued.append(self._invoices[existing_id])
                continue
            period_end = self._period_end_for_cycle(period_start, subscription.billing_cycle)
            invoice = InvoiceRecord(
                invoice_id=f"inv_{len(self._invoices) + 1}",
                order_id=f"sub_cycle:{subscription.subscription_id}:{period_start.date().isoformat()}",
                tenant_id=subscription.tenant_id,
                amount=subscription.amount,
                currency=subscription.currency,
                state=InvoiceState.ISSUED,
                invoice_type="subscription",
                billing_cycle=subscription.billing_cycle,
                subscription_id=subscription.subscription_id,
                period_start=period_start,
                period_end=period_end,
                due_at=self._derive_due_at(now=run_at, billing_cycle=subscription.billing_cycle),
            )
            self._invoices[invoice.invoice_id] = invoice
            self._subscription_period_index[dedupe_key] = invoice.invoice_id
            issued.append(invoice)
            self._subscription_contracts[subscription.subscription_id] = SubscriptionBillingContract(
                **{
                    **subscription.__dict__,
                    "last_billed_at": run_at,
                    "next_billing_at": period_end,
                }
            )
        return issued

    def detect_overdue_invoices(self, *, now: datetime | None = None) -> list[InvoiceRecord]:
        run_at = now or datetime.now(timezone.utc)
        overdue: list[InvoiceRecord] = []
        for invoice_id, invoice in list(self._invoices.items()):
            if invoice.state != InvoiceState.ISSUED or invoice.due_at is None or invoice.due_at > run_at:
                continue
            overdue_invoice = InvoiceRecord(**{**invoice.__dict__, "state": InvoiceState.OVERDUE})
            self._invoices[invoice_id] = overdue_invoice
            overdue.append(overdue_invoice)
        return overdue

    def _derive_due_at(self, *, now: datetime, billing_cycle: BillingCycle) -> datetime:
        terms_days = 1 if billing_cycle == BillingCycle.ONE_TIME else 15
        return now + timedelta(days=terms_days)

    def _period_end_for_cycle(self, start_at: datetime, cycle: BillingCycle) -> datetime:
        if cycle == BillingCycle.ANNUAL:
            return start_at + timedelta(days=365)
        if cycle == BillingCycle.MONTHLY:
            return start_at + timedelta(days=30)
        return start_at
