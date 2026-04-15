from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Protocol

from integrations.payments.base_adapter import PaymentVerificationResult, TenantPaymentContext


class PaymentStatusAdapter(Protocol):
    provider_key: str

    def get_status(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        """Return current provider status for payment."""


class ReconciliationTarget(Protocol):
    def apply_reconciliation(
        self,
        *,
        order_id: str,
        invoice_id: str,
        payment_id: str,
        resolved: bool,
    ) -> None:
        """Update order + invoice state after reconciliation."""


class LedgerTarget(Protocol):
    def post_payment_to_ledger(
        self,
        *,
        tenant_id: str,
        student_id: str,
        payment_id: str,
        amount: Decimal,
        currency: str = "USD",
    ):
        """Write payment into SoR ledger."""


@dataclass(frozen=True)
class ReconciliationTransaction:
    transaction_id: str
    tenant_id: str
    student_id: str
    provider: str
    payment_id: str
    order_id: str
    invoice_id: str
    amount: Decimal
    currency: str
    status: str = "pending"
    attempts: int = 0
    resolved_at: datetime | None = None


class PaymentReconciliationEngine:
    def __init__(
        self,
        *,
        adapters: list[PaymentStatusAdapter],
        commerce_target: ReconciliationTarget,
        ledger_target: LedgerTarget,
        reconcile_interval_seconds: float = 30.0,
        max_attempts: int = 5,
    ) -> None:
        self._adapters = {adapter.provider_key: adapter for adapter in adapters}
        self._commerce_target = commerce_target
        self._ledger_target = ledger_target
        self._reconcile_interval_seconds = reconcile_interval_seconds
        self._max_attempts = max_attempts
        self._transactions: dict[str, ReconciliationTransaction] = {}
        self._job: asyncio.Task[None] | None = None

    def track_transaction(
        self,
        *,
        transaction_id: str,
        tenant_id: str,
        student_id: str,
        provider: str,
        payment_id: str,
        order_id: str,
        invoice_id: str,
        amount: Decimal,
        currency: str,
        status: str = "pending",
    ) -> ReconciliationTransaction:
        txn = ReconciliationTransaction(
            transaction_id=transaction_id,
            tenant_id=tenant_id,
            student_id=student_id,
            provider=provider,
            payment_id=payment_id,
            order_id=order_id,
            invoice_id=invoice_id,
            amount=Decimal(amount),
            currency=currency,
            status=status,
        )
        self._transactions[transaction_id] = txn
        return txn

    def scan_unresolved_transactions(self) -> tuple[ReconciliationTransaction, ...]:
        return tuple(txn for txn in self._transactions.values() if txn.status in {"pending", "unknown"})

    def run_reconciliation_pass(self) -> tuple[ReconciliationTransaction, ...]:
        unresolved = self.scan_unresolved_transactions()
        updates: list[ReconciliationTransaction] = []
        for txn in unresolved:
            adapter = self._adapters.get(txn.provider)
            if adapter is None:
                updated = replace(txn, status="unknown", attempts=txn.attempts + 1)
                if updated.attempts >= self._max_attempts:
                    updated = replace(updated, status="failed", resolved_at=datetime.now(timezone.utc))
                    self._commerce_target.apply_reconciliation(
                        order_id=txn.order_id,
                        invoice_id=txn.invoice_id,
                        payment_id=txn.payment_id,
                        resolved=False,
                    )
                self._transactions[txn.transaction_id] = updated
                updates.append(updated)
                continue

            status_result = adapter.get_status(
                payment_id=txn.payment_id,
                tenant=TenantPaymentContext(tenant_id=txn.tenant_id, country_code="US"),
            )
            if status_result.ok:
                updated = replace(txn, status="verified", attempts=txn.attempts + 1, resolved_at=datetime.now(timezone.utc))
                self._commerce_target.apply_reconciliation(
                    order_id=txn.order_id,
                    invoice_id=txn.invoice_id,
                    payment_id=txn.payment_id,
                    resolved=True,
                )
                try:
                    self._ledger_target.post_payment_to_ledger(
                        tenant_id=txn.tenant_id,
                        student_id=txn.student_id,
                        payment_id=txn.payment_id,
                        amount=txn.amount,
                        currency=txn.currency,
                    )
                except ValueError:
                    pass
            else:
                next_status = "unknown" if txn.attempts + 1 < self._max_attempts else "failed"
                resolved_at = datetime.now(timezone.utc) if next_status == "failed" else None
                updated = replace(txn, status=next_status, attempts=txn.attempts + 1, resolved_at=resolved_at)
                if next_status == "failed":
                    self._commerce_target.apply_reconciliation(
                        order_id=txn.order_id,
                        invoice_id=txn.invoice_id,
                        payment_id=txn.payment_id,
                        resolved=False,
                    )

            self._transactions[txn.transaction_id] = updated
            updates.append(updated)
        return tuple(updates)

    async def _run_periodic(self) -> None:
        try:
            while True:
                self.run_reconciliation_pass()
                if not self.scan_unresolved_transactions():
                    break
                await asyncio.sleep(self._reconcile_interval_seconds)
        finally:
            self._job = None

    def schedule_periodic_reconciliation(self) -> asyncio.Task[None] | None:
        if self._job is not None and not self._job.done():
            return self._job
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            while self.scan_unresolved_transactions():
                self.run_reconciliation_pass()
            return None
        self._job = loop.create_task(self._run_periodic())
        return self._job

    def ensure_all_transactions_resolved(self) -> bool:
        self.schedule_periodic_reconciliation()
        return not self.scan_unresolved_transactions()
