from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Callable

from .catalog import CatalogService
from .models import Product


class CheckoutStatus(str, Enum):
    OPEN = "open"
    SUBMITTED = "submitted"


class OrderStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    RECONCILED = "reconciled"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    RECONCILED = "reconciled"


@dataclass(frozen=True)
class TransactionLogEntry:
    log_id: str
    idempotency_key: str
    tenant_id: str
    learner_id: str
    attempt: int
    amount: Decimal
    currency: str
    success: bool
    retryable: bool
    payment_id: str | None


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


PaymentExecutor = Callable[[str, str, Decimal, str, int, str], tuple[bool, str | None, bool]]
PriceResolver = Callable[[Product], Decimal]
FailureNotifier = Callable[[str, str, str], None]


class CheckoutService:
    def __init__(
        self,
        catalog_service: CatalogService,
        payment_executor: PaymentExecutor,
        pricing_resolver: PriceResolver,
        *,
        max_retries: int = 2,
        backoff_base_seconds: float = 0.0,
        failure_notifier: FailureNotifier | None = None,
    ) -> None:
        self._catalog_service = catalog_service
        self._payment_executor = payment_executor
        self._pricing_resolver = pricing_resolver
        self._max_retries = max_retries
        self._backoff_base_seconds = max(backoff_base_seconds, 0.0)
        self._failure_notifier = failure_notifier
        self._sessions: dict[str, CheckoutSession] = {}
        self._orders: dict[str, Order] = {}
        self._transactions: dict[str, Transaction] = {}
        self._idempotency_index: dict[tuple[str, str], str] = {}
        self._transaction_log_store: dict[str, list[TransactionLogEntry]] = {}

    def start_session(self, *, session_id: str, tenant_id: str, learner_id: str, product_id: str, idempotency_key: str) -> CheckoutSession:
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

    def calculate_total(self, products: tuple[Product, ...]) -> Decimal:
        return sum((Decimal(self._pricing_resolver(p)) for p in products), Decimal("0"))

    async def submit_session(self, *, session_id: str, max_retries: int = 2) -> Order:
        session = self._sessions[session_id.strip()]
        idem_key = (session.tenant_id, session.idempotency_key)
        existing = self._idempotency_index.get(idem_key)
        if existing:
            return self._orders[existing]

        product = self._catalog_service.resolve_sellable_product(tenant_id=session.tenant_id, product_id=session.product_id)
        total = self.calculate_total((product,))

        success = False
        payment_id: str | None = None
        retryable = False
        last_attempt = 0
        logs: list[TransactionLogEntry] = []
        retries = self._max_retries if max_retries is None else max_retries
        for attempt in range(retries + 1):
            last_attempt = attempt
            success, payment_id, retryable = self._payment_executor(
                session.tenant_id,
                session.learner_id,
                total,
                product.currency,
                attempt,
                session.idempotency_key,
            )
            logs.append(
                TransactionLogEntry(
                    log_id=f"txlog_{len(logs) + 1}",
                    idempotency_key=session.idempotency_key,
                    tenant_id=session.tenant_id,
                    learner_id=session.learner_id,
                    attempt=attempt,
                    amount=total,
                    currency=product.currency,
                    success=success,
                    retryable=retryable,
                    payment_id=payment_id,
                )
            )
            if success or not retryable:
                break
            await self._sleep_with_backoff(attempt=attempt)

        order_id = f"order_{len(self._orders) + 1}"
        status = OrderStatus.PAID if success else OrderStatus.FAILED
        order = Order(
            order_id=order_id,
            user_id=session.learner_id,
            product_ids=(product.product_id,),
            total_amount=total,
            status=status,
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            learner_id=session.learner_id,
            product=product,
            capability_id=product.primary_capability_id,
            amount=total,
            currency=product.currency,
            payment_id=payment_id,
            idempotency_key=session.idempotency_key,
        )

        txn = Transaction(
            transaction_id=f"txn_{len(self._transactions) + 1}",
            order_id=order_id,
            tenant_id=order.tenant_id,
            amount=total,
            currency=product.currency,
            payment_id=payment_id,
            status=TransactionStatus.SUCCESS if success else TransactionStatus.FAILED,
            retryable=retryable,
            attempt=last_attempt,
        )
        self._transactions[txn.transaction_id] = txn
        order = Order(**{**order.__dict__, "transaction_id": txn.transaction_id})

        self._orders[order.order_id] = order
        self._idempotency_index[idem_key] = order.order_id
        self._transaction_log_store[order.order_id] = logs
        self._sessions[session.session_id] = CheckoutSession(**{**session.__dict__, "status": CheckoutStatus.SUBMITTED, "attempt_count": last_attempt + 1})
        if not success and self._failure_notifier:
            self._failure_notifier(session.tenant_id, session.learner_id, order.order_id)
        return order

    def reconcile_order(self, *, order_id: str) -> Order:
        order = self._orders[order_id.strip()]
        if order.status == OrderStatus.RECONCILED:
            return order
        reconciled = Order(**{**order.__dict__, "status": OrderStatus.RECONCILED})
        self._orders[reconciled.order_id] = reconciled
        if reconciled.transaction_id:
            txn = self._transactions[reconciled.transaction_id]
            self._transactions[txn.transaction_id] = Transaction(**{**txn.__dict__, "status": TransactionStatus.RECONCILED})
        return reconciled

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id.strip())

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        return self._transactions.get(transaction_id.strip())

    def get_transaction_logs(self, *, order_id: str) -> list[TransactionLogEntry]:
        return list(self._transaction_log_store.get(order_id.strip(), []))

    async def _sleep_with_backoff(self, *, attempt: int) -> None:
        if self._backoff_base_seconds <= 0:
            await asyncio.sleep(0)
            return
        await asyncio.sleep(self._backoff_base_seconds * (2**attempt))


OrderRecord = Order
