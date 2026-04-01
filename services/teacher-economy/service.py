from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Any, Callable

from shared.models.teacher_economics import TeacherBatchEconomics


class TeacherEconomyService:
    """Teacher-owned batch economics with commerce and ledger integrations."""

    def __init__(
        self,
        *,
        sor_service: Any,
        commerce_service: Any | None,
        assignment_getter: Callable[[str, str, str], Any | None],
        assignment_upserter: Callable[[Any], Any],
        batch_getter: Callable[[str, str], Any | None],
        primary_teacher_getter: Callable[[str, str], str | None],
        key_builder: Callable[..., tuple[str, ...]],
        revenue_share_agreements: dict[tuple[str, str], Any] | None = None,
        teacher_batch_economics: dict[tuple[str, str], TeacherBatchEconomics] | None = None,
        teacher_payouts: dict[tuple[str, str], list[Any]] | None = None,
    ) -> None:
        self._sor = sor_service
        self._commerce = commerce_service
        self._assignment_getter = assignment_getter
        self._assignment_upserter = assignment_upserter
        self._batch_getter = batch_getter
        self._primary_teacher_getter = primary_teacher_getter
        self._key = key_builder
        self._revenue_share_agreements = revenue_share_agreements or {}
        self._teacher_batch_economics = teacher_batch_economics or {}
        self._teacher_payouts = teacher_payouts or {}

    def configure_revenue_share(self, agreement: Any) -> Any:
        if agreement.share_ratio < Decimal("0") or agreement.share_ratio > Decimal("1"):
            raise ValueError("share ratio must be between 0 and 1")
        assignment = self._assignment_getter(agreement.tenant_id, agreement.batch_id, agreement.teacher_id)
        if assignment is None:
            raise ValueError("teacher must be assigned to batch before configuring revenue share")
        self._revenue_share_agreements[self._key(agreement.tenant_id, agreement.batch_id)] = agreement
        return agreement

    def mark_batch_teacher_owned(
        self,
        *,
        tenant_id: str,
        batch_id: str,
        teacher_id: str,
        ownership_mode: str = "teacher_owned",
        payout_schedule: str = "monthly",
        metadata: dict[str, str] | None = None,
    ) -> TeacherBatchEconomics:
        assignment = self._assignment_getter(tenant_id, batch_id, teacher_id)
        if assignment is None:
            raise ValueError("teacher must be assigned to batch before ownership is enabled")
        owned_assignment = replace(
            assignment,
            teacher_owned_batch=True,
            ownership_metadata={**assignment.ownership_metadata, **(metadata or {}), "ownership_mode": ownership_mode},
        )
        self._assignment_upserter(owned_assignment)
        economics = self._teacher_batch_economics.get(self._key(tenant_id, batch_id))
        if economics is None:
            economics = TeacherBatchEconomics(
                teacher_id=teacher_id,
                batch_id=batch_id,
                ownership_mode=ownership_mode,
                revenue_share_percent=Decimal("0"),
                payout_schedule=payout_schedule,
                metadata={"tenant_id": tenant_id, **(metadata or {})},
            )
        self._teacher_batch_economics[self._key(tenant_id, batch_id)] = economics
        return economics

    def assign_revenue_share(
        self,
        *,
        agreement_factory: Callable[..., Any],
        tenant_id: str,
        batch_id: str,
        teacher_id: str,
        revenue_share_percent: Decimal,
        payout_schedule: str = "monthly",
        metadata: dict[str, str] | None = None,
    ) -> TeacherBatchEconomics:
        share = Decimal(revenue_share_percent)
        if share < Decimal("0") or share > Decimal("100"):
            raise ValueError("revenue_share_percent must be between 0 and 100")
        agreement = self.configure_revenue_share(
            agreement_factory(
                tenant_id=tenant_id,
                batch_id=batch_id,
                teacher_id=teacher_id,
                share_ratio=(share / Decimal("100")).quantize(Decimal("0.0001")),
            )
        )
        existing = self._teacher_batch_economics.get(self._key(tenant_id, batch_id))
        economics = TeacherBatchEconomics(
            teacher_id=teacher_id,
            batch_id=batch_id,
            ownership_mode=(existing.ownership_mode if existing else "teacher_owned"),
            revenue_share_percent=share.quantize(Decimal("0.01")),
            payout_schedule=payout_schedule,
            earnings_to_date=existing.earnings_to_date if existing else Decimal("0.00"),
            pending_payout_amount=existing.pending_payout_amount if existing else Decimal("0.00"),
            metadata={
                **(existing.metadata if existing else {"tenant_id": tenant_id}),
                **(metadata or {}),
                "agreement_share_ratio": str(agreement.share_ratio),
            },
        )
        self._teacher_batch_economics[self._key(tenant_id, batch_id)] = economics
        return economics

    def calculate_teacher_batch_earnings(self, *, tenant_id: str, batch_id: str) -> TeacherBatchEconomics:
        economics = self._teacher_batch_economics.get(self._key(tenant_id, batch_id))
        if economics is None:
            raise KeyError("teacher batch economics not found")
        payouts = self._teacher_payouts.get(self._key(tenant_id, batch_id), [])
        earnings = sum((payout.payout_amount for payout in payouts if payout.teacher_id == economics.teacher_id), start=Decimal("0.00"))
        settled_so_far = (economics.earnings_to_date - economics.pending_payout_amount).quantize(Decimal("0.01"))
        if settled_so_far < Decimal("0.00"):
            settled_so_far = Decimal("0.00")
        pending = (earnings - settled_so_far).quantize(Decimal("0.01"))
        if pending < Decimal("0.00"):
            pending = Decimal("0.00")
        updated = replace(
            economics,
            earnings_to_date=earnings.quantize(Decimal("0.01")),
            pending_payout_amount=pending,
        )
        self._teacher_batch_economics[self._key(tenant_id, batch_id)] = updated
        return updated

    def list_teacher_owned_batches(self, *, tenant_id: str, teacher_id: str) -> tuple[Any, ...]:
        owned_batch_ids = [
            batch_id
            for (econ_tenant_id, batch_id), economics in self._teacher_batch_economics.items()
            if econ_tenant_id == tenant_id and economics.teacher_id == teacher_id
        ]
        return tuple(
            batch for batch_id in owned_batch_ids if (batch := self._batch_getter(tenant_id, batch_id)) is not None
        )

    def ingest_commerce_invoice_for_batch(
        self,
        *,
        invoice: Any,
        learner_id: str,
        batch_id: str,
        payout_record_factory: Callable[..., Any],
    ) -> None:
        batch_key = self._key(invoice.tenant_id, batch_id)
        agreement = self._revenue_share_agreements.get(batch_key)
        primary_teacher_id = self._primary_teacher_getter(invoice.tenant_id, batch_id)
        assignment = self._assignment_getter(invoice.tenant_id, batch_id, primary_teacher_id) if primary_teacher_id else None
        if agreement is None or assignment is None:
            return

        if self._key(invoice.tenant_id, batch_id) not in self._teacher_batch_economics:
            self._teacher_batch_economics[self._key(invoice.tenant_id, batch_id)] = TeacherBatchEconomics(
                teacher_id=assignment.teacher_id,
                batch_id=batch_id,
                ownership_mode="teacher_owned",
                revenue_share_percent=(agreement.share_ratio * Decimal("100")).quantize(Decimal("0.01")),
                payout_schedule="monthly",
                metadata={"tenant_id": invoice.tenant_id, "source": "invoice_ingestion_backfill"},
            )
        payout_amount = (Decimal(invoice.amount) * agreement.share_ratio).quantize(Decimal("0.01"))
        payout = payout_record_factory(
            tenant_id=invoice.tenant_id,
            batch_id=batch_id,
            teacher_id=assignment.teacher_id,
            invoice_id=invoice.invoice_id,
            revenue_amount=Decimal(invoice.amount),
            payout_amount=payout_amount,
        )
        self._teacher_payouts.setdefault(batch_key, []).append(payout)
        learner_id_for_invoice = learner_id
        self._sor.post_teacher_payout_audit_to_ledger(
            tenant_id=invoice.tenant_id,
            student_id=learner_id_for_invoice,
            batch_id=batch_id,
            teacher_id=assignment.teacher_id,
            payout_id=f"{invoice.invoice_id}:{assignment.teacher_id}",
            invoice_id=invoice.invoice_id,
            revenue_amount=Decimal(invoice.amount),
            payout_amount=payout_amount,
        )
        if self._commerce is not None and hasattr(self._commerce, "record_teacher_revenue_share"):
            self._commerce.record_teacher_revenue_share(
                tenant_id=invoice.tenant_id,
                batch_id=batch_id,
                teacher_id=assignment.teacher_id,
                invoice_id=invoice.invoice_id,
                revenue_amount=Decimal(invoice.amount),
                payout_amount=payout_amount,
            )
        self.calculate_teacher_batch_earnings(tenant_id=invoice.tenant_id, batch_id=batch_id)

    def settle_payouts_for_invoice(self, *, tenant_id: str, batch_id: str, invoice_id: str) -> Decimal:
        economics = self._teacher_batch_economics.get(self._key(tenant_id, batch_id))
        if economics is None:
            return Decimal("0.00")
        payout_total = sum(
            (
                payout.payout_amount
                for payout in self._teacher_payouts.get(self._key(tenant_id, batch_id), ())
                if payout.invoice_id == invoice_id and payout.teacher_id == economics.teacher_id
            ),
            start=Decimal("0.00"),
        )
        if payout_total > 0:
            self._teacher_batch_economics[self._key(tenant_id, batch_id)] = replace(
                economics,
                pending_payout_amount=(economics.pending_payout_amount - payout_total).quantize(Decimal("0.01")),
            )
        return payout_total

    def teacher_payouts(self, *, tenant_id: str, batch_id: str) -> tuple[Any, ...]:
        return tuple(self._teacher_payouts.get(self._key(tenant_id, batch_id), ()))
