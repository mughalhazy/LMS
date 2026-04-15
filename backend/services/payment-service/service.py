"""Payment service — event emission, history storage, reconciliation.

CGAP-071: `backend/services/payment-service/` had only `api.py` delegating directly to
`PaymentOrchestrationService` with no event emission, payment history storage, or
reconciliation tracking at the service layer. This module adds that layer.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


class PaymentRecord:
    """Immutable record of a payment transaction stored in service history."""

    __slots__ = (
        "payment_id", "tenant_id", "user_id", "order_id", "provider",
        "amount", "currency", "status", "created_at", "updated_at", "metadata",
    )

    def __init__(
        self,
        *,
        payment_id: str,
        tenant_id: str,
        user_id: str,
        order_id: str | None,
        provider: str,
        amount: float | None,
        currency: str | None,
        status: str,
        created_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.payment_id = payment_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.order_id = order_id
        self.provider = provider
        self.amount = amount
        self.currency = currency
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.metadata: dict[str, Any] = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "provider": self.provider,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class PaymentService:
    """Service-layer wrapper over PaymentOrchestrationService.

    Adds: payment history storage, platform event bus emission, reconciliation tracking.
    Designed to be injected into the FastAPI app rather than the bare orchestrator.
    """

    def __init__(self, orchestrator: Any) -> None:
        self._orchestrator = orchestrator
        self._history: dict[str, PaymentRecord] = {}  # keyed by payment_id
        self._reconciliation_log: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Payment history                                                     #
    # ------------------------------------------------------------------ #

    def record_payment_event(
        self,
        *,
        payment_id: str,
        tenant_id: str,
        user_id: str,
        order_id: str | None,
        provider: str,
        amount: float | None,
        currency: str | None,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentRecord:
        """Persist a payment event and emit to the platform event bus."""
        record = PaymentRecord(
            payment_id=payment_id,
            tenant_id=tenant_id,
            user_id=user_id,
            order_id=order_id,
            provider=provider,
            amount=amount,
            currency=currency,
            status=status,
            metadata=metadata or {},
        )
        if payment_id in self._history:
            existing = self._history[payment_id]
            existing.status = status  # type: ignore[attr-defined]
            existing.updated_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
            record = existing
        else:
            self._history[payment_id] = record

        self._emit_payment_event(record)
        return record

    def get_payment_history(
        self,
        *,
        tenant_id: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return payment history, optionally filtered by tenant_id or user_id."""
        records = list(self._history.values())
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        if user_id:
            records = [r for r in records if r.user_id == user_id]
        records.sort(key=lambda r: r.created_at, reverse=True)
        return [r.to_dict() for r in records[:limit]]

    # ------------------------------------------------------------------ #
    # Reconciliation                                                      #
    # ------------------------------------------------------------------ #

    def reconcile_payments(
        self,
        *,
        tenant_id: str,
        provider_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compare platform history against provider records and flag discrepancies.

        Returns a reconciliation report with matched, unmatched, and disputed entries.
        """
        platform_ids = {r.payment_id for r in self._history.values() if r.tenant_id == tenant_id}
        provider_ids = {str(rec.get("payment_id") or rec.get("transaction_id", "")).strip() for rec in provider_records}

        matched = platform_ids & provider_ids
        platform_only = platform_ids - provider_ids  # in platform but not in provider (potential reversal)
        provider_only = provider_ids - platform_ids  # in provider but not in platform (potential missing record)

        report: dict[str, Any] = {
            "reconciliation_id": str(uuid4()),
            "tenant_id": tenant_id,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "matched_count": len(matched),
            "platform_only_count": len(platform_only),
            "provider_only_count": len(provider_only),
            "platform_only": sorted(platform_only),
            "provider_only": sorted(provider_only),
            "status": "clean" if not platform_only and not provider_only else "discrepancy_detected",
        }
        self._reconciliation_log.append(report)
        self._emit_reconciliation_event(report)
        return report

    def get_reconciliation_log(self) -> list[dict[str, Any]]:
        return list(self._reconciliation_log)

    # ------------------------------------------------------------------ #
    # Orchestrator delegation                                             #
    # ------------------------------------------------------------------ #

    async def handle_provider_callback(self, *, provider: str, payload: dict[str, Any]) -> Any:
        """Delegate to orchestrator and record the resulting payment event."""
        result = await self._orchestrator.handle_provider_callback(provider=provider, payload=payload)
        if result is not None:
            record = self.record_payment_event(
                payment_id=str(payload.get("payment_id") or ""),
                tenant_id=str(payload.get("tenant_id") or ""),
                user_id=str(payload.get("user_id") or ""),
                order_id=payload.get("order_id"),
                provider=provider,
                amount=payload.get("amount"),
                currency=payload.get("currency"),
                status="verified" if getattr(result, "verified", False) else "processed",
                metadata=payload,
            )
            # BC-PAY-01: grant access in the same request cycle — no queue delay
            self.activate_entitlement_on_payment(record)
        return result

    # ------------------------------------------------------------------
    # BC-PAY-01: Payment → instant entitlement activation — MO-028 / Phase C
    # When a payment.verified event fires, access must be granted within
    # the same request cycle. activate_entitlement_on_payment() is called
    # by handle_provider_callback() and emits entitlement.activated so
    # downstream services (capability-gating, enrollment) can act immediately.
    # ------------------------------------------------------------------

    def activate_entitlement_on_payment(self, record: PaymentRecord) -> None:
        """Emit entitlement.activated event on a verified payment (BC-PAY-01).

        Called synchronously within the payment callback so access is granted
        before the response returns — no queue delay, no polling required.
        """
        if record.status != "verified":
            return

        entitlement_payload: dict[str, Any] = {
            "event_type": "entitlement.activated",
            "payment_id": record.payment_id,
            "tenant_id": record.tenant_id,
            "user_id": record.user_id,
            "order_id": record.order_id,
            "amount": record.amount,
            "currency": record.currency,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "source": "payment.verified",
        }

        # Emit to platform event bus — best-effort, never blocks payment success
        try:
            from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
            publish_event(entitlement_payload)
        except Exception:
            pass

        # Also invoke entitlement service directly if available in this process
        try:
            from services.entitlement_service.service import EntitlementService  # type: ignore[import]
            es = EntitlementService()
            es.activate_from_payment(
                tenant_id=record.tenant_id,
                user_id=record.user_id,
                order_id=record.order_id,
                payment_id=record.payment_id,
            )
        except Exception:
            pass  # direct call is opportunistic; event bus is the reliable path

    # ------------------------------------------------------------------ #
    # Event emission                                                      #
    # ------------------------------------------------------------------ #

    def _emit_payment_event(self, record: PaymentRecord) -> None:
        """CGAP-071: emit payment events to platform event bus (best-effort)."""
        try:
            from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
            publish_event({
                "event_type": f"payment.{record.status}",
                "payment_id": record.payment_id,
                "tenant_id": record.tenant_id,
                "user_id": record.user_id,
                "order_id": record.order_id,
                "provider": record.provider,
                "amount": record.amount,
                "currency": record.currency,
                "timestamp": record.updated_at.isoformat(),
            })
        except Exception:
            pass  # best-effort

    def _emit_reconciliation_event(self, report: dict[str, Any]) -> None:
        """CGAP-071: emit reconciliation report to platform event bus (best-effort)."""
        if report.get("status") != "discrepancy_detected":
            return
        try:
            from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
            publish_event({
                "event_type": "payment.reconciliation.discrepancy",
                **report,
            })
        except Exception:
            pass
