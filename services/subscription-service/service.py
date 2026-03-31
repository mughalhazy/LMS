from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from shared.models.invoice import Invoice


@dataclass(frozen=True)
class Subscription:
    subscription_id: str
    tenant_id: str
    amount: Decimal
    active: bool = False


class SubscriptionService:
    def __init__(self) -> None:
        self._invoices: list[Invoice] = []

    @property
    def invoices(self) -> list[Invoice]:
        return list(self._invoices)

    def activate_subscription(self, subscription: Subscription) -> tuple[Subscription, Invoice]:
        activated = Subscription(
            subscription_id=subscription.subscription_id,
            tenant_id=subscription.tenant_id,
            amount=Decimal(subscription.amount),
            active=True,
        )
        invoice = self._generate_invoice(
            tenant_id=subscription.tenant_id,
            amount=subscription.amount,
        )
        return activated, invoice

    def renew_subscription(self, subscription: Subscription) -> Invoice:
        if not subscription.active:
            raise ValueError("Cannot renew an inactive subscription")
        return self._generate_invoice(
            tenant_id=subscription.tenant_id,
            amount=subscription.amount,
        )

    def _generate_invoice(self, tenant_id: str, amount: Decimal) -> Invoice:
        invoice = Invoice.issued(
            invoice_id=f"inv_{uuid4().hex}",
            tenant_id=tenant_id,
            amount=Decimal(amount),
        )
        self._invoices.append(invoice)
        return invoice
