from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Callable

from .catalog import CatalogProduct, CatalogService


class CheckoutStatus(str, Enum):
    OPEN = "open"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    PAYMENT_FAILED = "payment_failed"


@dataclass(frozen=True)
class CheckoutSession:
    session_id: str
    tenant_id: str
    learner_id: str
    product_id: str
    idempotency_key: str
    status: CheckoutStatus
    attempt_count: int = 0


@dataclass(frozen=True)
class OrderRecord:
    order_id: str
    session_id: str
    tenant_id: str
    learner_id: str
    product: CatalogProduct
    amount: Decimal
    currency: str
    payment_id: str | None
    status: CheckoutStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


PaymentExecutor = Callable[[str, str, Decimal, str, int], tuple[bool, str | None, bool]]


class CheckoutService:
    """Checkout owns order/payment-intent initiation with retry-safe idempotency."""

    def __init__(self, catalog_service: CatalogService, payment_executor: PaymentExecutor) -> None:
        self._catalog_service = catalog_service
        self._payment_executor = payment_executor
        self._sessions: dict[str, CheckoutSession] = {}
        self._orders: dict[str, OrderRecord] = {}
        self._idempotency_index: dict[tuple[str, str], str] = {}

    def start_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        learner_id: str,
        product_id: str,
        idempotency_key: str,
    ) -> CheckoutSession:
        session = CheckoutSession(
            session_id=session_id.strip(),
            tenant_id=tenant_id.strip(),
            learner_id=learner_id.strip(),
            product_id=product_id.strip(),
            idempotency_key=idempotency_key.strip(),
            status=CheckoutStatus.OPEN,
        )
        self._sessions[session.session_id] = session
        return session

    async def submit_session(self, *, session_id: str, max_retries: int = 2) -> OrderRecord:
        session = self._sessions[session_id.strip()]
        idem_key = (session.tenant_id, session.idempotency_key)
        existing_order_id = self._idempotency_index.get(idem_key)
        if existing_order_id:
            return self._orders[existing_order_id]

        product = self._catalog_service.resolve_sellable_product(
            tenant_id=session.tenant_id,
            product_id=session.product_id,
        )

        payment_id: str | None = None
        success = False
        for attempt in range(max_retries + 1):
            success, payment_id, retryable = self._payment_executor(
                session.tenant_id,
                session.learner_id,
                product.price,
                product.currency,
                attempt,
            )
            if success:
                break
            if not retryable:
                break
            await asyncio.sleep(0)

        status = CheckoutStatus.COMPLETED if success else CheckoutStatus.PAYMENT_FAILED
        order = OrderRecord(
            order_id=f"order_{len(self._orders) + 1}",
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            learner_id=session.learner_id,
            product=product,
            amount=Decimal(product.price),
            currency=product.currency,
            payment_id=payment_id,
            status=status,
        )
        self._orders[order.order_id] = order
        self._idempotency_index[idem_key] = order.order_id
        self._sessions[session.session_id] = CheckoutSession(
            **{**session.__dict__, "status": CheckoutStatus.SUBMITTED, "attempt_count": max_retries + 1}
        )
        return order

    def get_order(self, order_id: str) -> OrderRecord | None:
        return self._orders.get(order_id.strip())
