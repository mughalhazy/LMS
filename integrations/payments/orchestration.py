from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from integrations.payments.adapters import EasyPaisaAdapter, JazzCashAdapter, RaastAdapter
from integrations.payments.base_adapter import PaymentResult, TenantPaymentContext
from integrations.payments.router import PaymentProviderRouter


@dataclass(frozen=True)
class PaymentLedgerEntry:
    idempotency_key: str
    tenant_id: str
    tenant_country_code: str
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
        self._payment_id_to_idempotency_key: dict[str, str] = {}
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

        last_result = PaymentResult(ok=False, status="failure", provider=None, error="unknown")
        for attempt in range(self._max_retries + 1):
            last_result = self._router.process_checkout(
                tenant=tenant,
                amount=amount,
                invoice_id=invoice_id,
            )
            if last_result.ok:
                entry = PaymentLedgerEntry(
                    idempotency_key=idempotency_key,
                    tenant_id=tenant.tenant_id,
                    tenant_country_code=tenant.country_code,
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
                if entry.payment_id:
                    self._payment_id_to_idempotency_key[entry.payment_id] = idempotency_key
                try:
                    loop = asyncio.get_running_loop()
                    self._verification_tasks[idempotency_key] = loop.create_task(
                        self.verify_payment_async(idempotency_key=idempotency_key)
                    )
                except RuntimeError:
                    self._ledger[idempotency_key] = self._run_verification(entry=entry)
                return entry
            if not self._is_retryable(last_result):
                break

        failed = PaymentLedgerEntry(
            idempotency_key=idempotency_key,
            tenant_id=tenant.tenant_id,
            tenant_country_code=tenant.country_code,
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

        verified = self._run_verification(entry=entry)
        self._ledger[idempotency_key] = verified
        self._verification_tasks.pop(idempotency_key, None)
        return verified

    async def handle_provider_callback(
        self,
        *,
        provider: str,
        payload: dict[str, Any],
    ) -> PaymentLedgerEntry | None:
        callback_result = self._router.parse_callback(provider=provider, payload=payload)
        if callback_result is None:
            return None
        idempotency_key = self._payment_id_to_idempotency_key.get(callback_result.payment_id)
        if idempotency_key is None:
            return None
        current = self._ledger[idempotency_key]
        if current.status == "verified":
            return current

        if callback_result.ok:
            updated = PaymentLedgerEntry(
                **{
                    **current.__dict__,
                    "status": "verified",
                    "verified": True,
                    "verified_at": datetime.now(timezone.utc),
                    "error": None,
                }
            )
        else:
            updated = PaymentLedgerEntry(
                **{
                    **current.__dict__,
                    "status": "failed",
                    "verified": False,
                    "verified_at": None,
                    "error": callback_result.error or "callback_failed",
                }
            )
        self._ledger[idempotency_key] = updated
        task = self._verification_tasks.pop(idempotency_key, None)
        if task and not task.done():
            task.cancel()
        return updated

    async def await_verification(self, *, idempotency_key: str) -> PaymentLedgerEntry:
        task = self._verification_tasks.get(idempotency_key)
        if task:
            await task
        return self._ledger[idempotency_key]

    def get_ledger_entry(self, *, idempotency_key: str) -> PaymentLedgerEntry | None:
        return self._ledger.get(idempotency_key)

    def _run_verification(self, *, entry: PaymentLedgerEntry) -> PaymentLedgerEntry:
        if entry.payment_id is None or entry.provider is None:
            return PaymentLedgerEntry(
                **{**entry.__dict__, "status": "failed", "error": "missing_payment_reference"}
            )

        verification = self._router.verify(
            tenant=TenantPaymentContext(
                tenant_id=entry.tenant_id,
                country_code=entry.tenant_country_code,
            ),
            provider=entry.provider,
            payment_id=entry.payment_id,
        )
        return PaymentLedgerEntry(
            **{
                **entry.__dict__,
                "status": "verified" if verification.ok else "failed",
                "verified": verification.ok,
                "verified_at": datetime.now(timezone.utc) if verification.ok else None,
                "error": verification.error,
            }
        )

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
