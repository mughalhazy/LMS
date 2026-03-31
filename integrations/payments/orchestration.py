from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from integrations.payments.adapters import EasyPaisaAdapter, JazzCashAdapter, RaastAdapter
from integrations.payments.base_adapter import PaymentResult, TenantPaymentContext
from integrations.payments.router import PaymentProviderRouter


@dataclass(frozen=True)
class PaymentLedgerEntry:
    idempotency_key: str
    tenant_id: str
    amount: int
    currency: str
    status: str
    provider: str | None
    payment_id: str | None
    invoice_id: str | None
    attempt: int
    verified: bool
    verified_at: datetime | None
    error: str | None = None


class PaymentOrchestrationService:
    """Checkout -> orchestration -> adapter -> verification -> ledger."""

    def __init__(
        self,
        router: PaymentProviderRouter,
        *,
        max_retries: int = 2,
        verification_latency_seconds: float = 0.0,
    ) -> None:
        self._router = router
        self._max_retries = max_retries
        self._verification_latency_seconds = verification_latency_seconds
        self._ledger: dict[str, PaymentLedgerEntry] = {}
        self._verification_tasks: dict[str, asyncio.Task[None]] = {}

    def process_checkout_payment(
        self,
        *,
        idempotency_key: str,
        tenant: TenantPaymentContext,
        amount: int,
        currency: str,
        invoice_id: str | None = None,
    ) -> PaymentLedgerEntry:
        if amount <= 0:
            raise ValueError("amount must be greater than 0")
        existing = self._ledger.get(idempotency_key)
        if existing:
            return existing

        adapter = self._router.resolve(tenant)
        last_result = PaymentResult(ok=False, status="failure", provider=adapter.provider_key, error="unknown")
        for attempt in range(self._max_retries + 1):
            last_result = adapter.process_payment(amount=amount, tenant=tenant, invoice_id=invoice_id)
            if last_result.ok:
                entry = PaymentLedgerEntry(
                    idempotency_key=idempotency_key,
                    tenant_id=tenant.tenant_id,
                    amount=amount,
                    currency=currency,
                    status="pending_verification",
                    provider=last_result.provider,
                    payment_id=last_result.payment_id,
                    invoice_id=invoice_id,
                    attempt=attempt,
                    verified=False,
                    verified_at=None,
                    error=None,
                )
                self._ledger[idempotency_key] = entry
                try:
                    loop = asyncio.get_running_loop()
                    self._verification_tasks[idempotency_key] = loop.create_task(
                        self.verify_payment_async(idempotency_key=idempotency_key)
                    )
                except RuntimeError:
                    # Synchronous callers still pass through verification and ledger.
                    self._ledger[idempotency_key] = PaymentLedgerEntry(
                        **{
                            **entry.__dict__,
                            "status": "verified",
                            "verified": True,
                            "verified_at": datetime.now(timezone.utc),
                        }
                    )
                return entry
            if not self._is_retryable(last_result):
                break

        failed = PaymentLedgerEntry(
            idempotency_key=idempotency_key,
            tenant_id=tenant.tenant_id,
            amount=amount,
            currency=currency,
            status="failed",
            provider=last_result.provider,
            payment_id=None,
            invoice_id=invoice_id,
            attempt=attempt,
            verified=False,
            verified_at=None,
            error=last_result.error,
        )
        self._ledger[idempotency_key] = failed
        return failed

    async def verify_payment_async(self, *, idempotency_key: str) -> PaymentLedgerEntry:
        entry = self._ledger[idempotency_key]
        if entry.status != "pending_verification":
            return entry
        if self._verification_latency_seconds > 0:
            await asyncio.sleep(self._verification_latency_seconds)

        verified = PaymentLedgerEntry(
            **{
                **entry.__dict__,
                "status": "verified",
                "verified": True,
                "verified_at": datetime.now(timezone.utc),
            }
        )
        self._ledger[idempotency_key] = verified
        self._verification_tasks.pop(idempotency_key, None)
        return verified

    async def await_verification(self, *, idempotency_key: str) -> PaymentLedgerEntry:
        task = self._verification_tasks.get(idempotency_key)
        if task:
            await task
        return self._ledger[idempotency_key]

    def get_ledger_entry(self, *, idempotency_key: str) -> PaymentLedgerEntry | None:
        return self._ledger.get(idempotency_key)

    @staticmethod
    def _is_retryable(result: PaymentResult) -> bool:
        return bool(result.error and "timeout" in result.error.lower())


def build_pakistan_payment_router(default_provider: str = "jazzcash") -> PaymentProviderRouter:
    """Commerce orchestration entrypoint for Pakistan-specific provider routing."""
    return PaymentProviderRouter(
        country_provider_config={"PK": default_provider},
        adapters=[JazzCashAdapter(), EasyPaisaAdapter(), RaastAdapter()],
    )


def build_pakistan_payment_orchestration(
    default_provider: str = "jazzcash",
    *,
    max_retries: int = 2,
) -> PaymentOrchestrationService:
    return PaymentOrchestrationService(
        router=build_pakistan_payment_router(default_provider=default_provider),
        max_retries=max_retries,
    )
