from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Callable

from .catalog import CatalogService, Product


class CheckoutStatus(str, Enum):
    OPEN = "open"
    SUBMITTED = "submitted"
    FAILED_VALIDATION = "failed_validation"


class OrderStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    RECONCILED = "reconciled"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RECONCILED = "reconciled"


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
class Order:
    order_id: str
    user_id: str
    product_ids: tuple[str, ...]
    total_amount: Decimal
    status: OrderStatus
    session_id: str
    tenant_id: str
    learner_id: str
    product: Product
    capability_id: str
    amount: Decimal
    currency: str
    payment_id: str | None
    transaction_id: str | None = None
    idempotency_key: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    order_id: str
    tenant_id: str
    amount: Decimal
    currency: str
    payment_id: str | None
    status: TransactionStatus
    retryable: bool
    attempt: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


PaymentExecutor = Callable[[str, str, Decimal, str, int, str], tuple[bool, str | None, bool]]
PriceResolver = Callable[[Product], Decimal]


class CheckoutService:
    """Checkout owns order/payment-intent initiation with retry-safe idempotency."""

    _valid_transitions: dict[OrderStatus, set[OrderStatus]] = {
        OrderStatus.CREATED: {OrderStatus.PENDING},
        OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.FAILED},
        OrderStatus.PAID: {OrderStatus.RECONCILED},
        OrderStatus.FAILED: {OrderStatus.RECONCILED},
        OrderStatus.RECONCILED: set(),
    }

    def __init__(
        self,
        catalog_service: CatalogService,
        payment_executor: PaymentExecutor,
        pricing_resolver: PriceResolver,
        *,
        max_retries: int = 2,
    ) -> None:
        self._catalog_service = catalog_service
        self._payment_executor = payment_executor
        self._pricing_resolver = pricing_resolver
        self._max_retries = max_retries
        self._sessions: dict[str, CheckoutSession] = {}
        self._orders: dict[str, Order] = {}
        self._transactions: dict[str, Transaction] = {}
        self._idempotency_index: dict[tuple[str, str], str] = {}
        self._transaction_log_store: dict[str, list[TransactionLogEntry]] = {}

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

    def create_order(self, *, session: CheckoutSession, product: Product) -> Order:
        base_amount = self.calculate_total((product,))
        return Order(
            order_id=f"order_{len(self._orders) + 1}",
            user_id=session.learner_id,
            product_ids=(product.product_id,),
            total_amount=base_amount,
            status=OrderStatus.CREATED,
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            learner_id=session.learner_id,
            product=product,
            capability_id=product.capability_id,
            amount=base_amount,
            currency=product.currency,
            payment_id=None,
            idempotency_key=session.idempotency_key,
        )

    def attach_products(self, *, order: Order, products: tuple[Product, ...]) -> Order:
        return Order(
            **{
                **order.__dict__,
                "product_ids": tuple(p.product_id for p in products),
                "total_amount": self.calculate_total(products),
            }
        )

    def calculate_total(self, products: tuple[Product, ...]) -> Decimal:
        return sum((Decimal(self._pricing_resolver(product)) for product in products), Decimal("0"))

    async def submit_session(self, *, session_id: str, max_retries: int = 2) -> Order:
        session = self._sessions[session_id.strip()]
        idem_key = (session.tenant_id, session.idempotency_key)
        existing_order_id = self._idempotency_index.get(idem_key)
        if existing_order_id:
            return self._orders[existing_order_id]
        configured_retries = self._max_retries if max_retries is None else max_retries

        product = self._catalog_service.resolve_sellable_product(
            tenant_id=session.tenant_id,
            product_id=session.product_id,
        )

        order = self.create_order(session=session, product=product)
        order = self.attach_products(order=order, products=(product,))

        payment_id: str | None = None
        success = False
        last_attempt = 0
        retryable = False
        txn_logs: list[TransactionLogEntry] = []
        for attempt in range(configured_retries + 1):
            last_attempt = attempt
            success, payment_id, retryable = self._payment_executor(
                session.tenant_id,
                session.learner_id,
                order.total_amount,
                order.currency,
                attempt,
                session.idempotency_key,
            )
            txn_logs.append(
                TransactionLogEntry(
                    log_id=f"txlog_{len(txn_logs) + 1}",
                    idempotency_key=session.idempotency_key,
                    tenant_id=session.tenant_id,
                    learner_id=session.learner_id,
                    attempt=attempt,
                    amount=Decimal(amount),
                    currency=product.currency,
                    success=success,
                    retryable=retryable,
                    payment_id=payment_id,
                )
            )
            if success:
                break
            if not retryable:
                break
            await asyncio.sleep(0)

        order = Order(
            order_id=f"order_{len(self._orders) + 1}",
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            learner_id=session.learner_id,
            product=product,
            capability_id=product.primary_capability_id,
            amount=Decimal(amount),
            currency=product.currency,
            payment_id=payment_id,
            status=OrderStatus.CREATED,
        )
        order = self._transition_order(order, OrderStatus.PENDING)
        order = self._transition_order(order, OrderStatus.PAID if success else OrderStatus.FAILED)

        transaction = Transaction(
            transaction_id=f"txn_{len(self._transactions) + 1}",
            order_id=order.order_id,
            tenant_id=order.tenant_id,
            amount=order.total_amount,
            currency=order.currency,
            payment_id=payment_id,
            status=TransactionStatus.SUCCEEDED if success else TransactionStatus.FAILED,
            retryable=retryable,
            attempt=last_attempt,
        )
        self._transactions[transaction.transaction_id] = transaction
        order = Order(**{**order.__dict__, "transaction_id": transaction.transaction_id})
        self._orders[order.order_id] = order
        self._idempotency_index[idem_key] = order.order_id
        self._transaction_log_store[order.order_id] = txn_logs
        self._sessions[session.session_id] = CheckoutSession(
            **{**session.__dict__, "status": CheckoutStatus.SUBMITTED, "attempt_count": last_attempt + 1}
        )
        return order

    def reconcile_order(self, *, order_id: str) -> Order:
        order = self._orders[order_id.strip()]
        if order.status == OrderStatus.RECONCILED:
            return order
        reconciled = self._transition_order(order, OrderStatus.RECONCILED)
        self._orders[reconciled.order_id] = reconciled
        if reconciled.transaction_id:
            txn = self._transactions[reconciled.transaction_id]
            txn_state = TransactionStatus.RECONCILED
            self._transactions[txn.transaction_id] = Transaction(**{**txn.__dict__, "status": txn_state})
        return reconciled

    def _transition_order(self, order: Order, target: OrderStatus) -> Order:
        allowed = self._valid_transitions[order.status]
        if target not in allowed:
            raise ValueError(f"invalid order transition: {order.status.value} -> {target.value}")
        return Order(**{**order.__dict__, "status": target})

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id.strip())

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        return self._transactions.get(transaction_id.strip())

    def get_transaction_logs(self, *, order_id: str) -> list[TransactionLogEntry]:
        return list(self._transaction_log_store.get(order_id.strip(), []))


# Backward-compatible alias while promoting Order as first-class domain entity.
OrderRecord = Order
