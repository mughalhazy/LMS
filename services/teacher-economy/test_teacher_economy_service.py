from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
MODULE_PATH = ROOT / "services/teacher-economy/service.py"
_spec = importlib.util.spec_from_file_location("teacher_economy_test_module", MODULE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Unable to load teacher-economy module")
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

TeacherEconomyService = _module.TeacherEconomyService


@dataclass(frozen=True)
class Assignment:
    tenant_id: str
    batch_id: str
    teacher_id: str
    teacher_owned_batch: bool = False
    ownership_metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Agreement:
    tenant_id: str
    batch_id: str
    teacher_id: str
    share_ratio: Decimal


@dataclass(frozen=True)
class PayoutRecord:
    tenant_id: str
    batch_id: str
    teacher_id: str
    invoice_id: str
    revenue_amount: Decimal
    payout_amount: Decimal


@dataclass(frozen=True)
class Invoice:
    tenant_id: str
    invoice_id: str
    amount: Decimal


class SorStub:
    def __init__(self) -> None:
        self.audit_calls: list[dict[str, str]] = []

    def post_teacher_payout_audit_to_ledger(self, **kwargs):
        self.audit_calls.append({k: str(v) for k, v in kwargs.items()})


class CommerceStub:
    def __init__(self) -> None:
        self.records: list[dict[str, str]] = []

    def record_teacher_revenue_share(self, **kwargs):
        self.records.append({k: str(v) for k, v in kwargs.items()})


def test_teacher_economy_integrates_sor_and_commerce() -> None:
    assignments: dict[tuple[str, str], dict[str, Assignment]] = {("tenant_1", "batch_1"): {"teacher_1": Assignment("tenant_1", "batch_1", "teacher_1")}}
    agreements: dict[tuple[str, str], Agreement] = {}
    economics: dict[tuple[str, str], object] = {}
    payouts: dict[tuple[str, str], list[PayoutRecord]] = {}
    batches = {("tenant_1", "batch_1"): object()}

    sor = SorStub()
    commerce = CommerceStub()

    def get_assignment(tenant_id: str, batch_id: str, teacher_id: str):
        return assignments.get((tenant_id, batch_id), {}).get(teacher_id)

    def upsert_assignment(assignment: Assignment):
        assignments.setdefault((assignment.tenant_id, assignment.batch_id), {})[assignment.teacher_id] = assignment

    service = TeacherEconomyService(
        sor_service=sor,
        commerce_service=commerce,
        assignment_getter=get_assignment,
        assignment_upserter=upsert_assignment,
        batch_getter=lambda tenant_id, batch_id: batches.get((tenant_id, batch_id)),
        primary_teacher_getter=lambda tenant_id, batch_id: "teacher_1",
        key_builder=lambda *parts: tuple(parts),
        revenue_share_agreements=agreements,
        teacher_batch_economics=economics,
        teacher_payouts=payouts,
    )

    service.mark_batch_teacher_owned(tenant_id="tenant_1", batch_id="batch_1", teacher_id="teacher_1")
    service.assign_revenue_share(
        agreement_factory=Agreement,
        tenant_id="tenant_1",
        batch_id="batch_1",
        teacher_id="teacher_1",
        revenue_share_percent=Decimal("50"),
    )

    service.ingest_commerce_invoice_for_batch(
        invoice=Invoice(tenant_id="tenant_1", invoice_id="inv_1", amount=Decimal("200.00")),
        learner_id="learner_1",
        batch_id="batch_1",
        payout_record_factory=PayoutRecord,
    )

    snapshot = service.calculate_teacher_batch_earnings(tenant_id="tenant_1", batch_id="batch_1")
    assert snapshot.earnings_to_date == Decimal("100.00")
    assert len(service.teacher_payouts(tenant_id="tenant_1", batch_id="batch_1")) == 1
    assert len(sor.audit_calls) == 1
    assert len(commerce.records) == 1

    service.settle_payouts_for_invoice(tenant_id="tenant_1", batch_id="batch_1", invoice_id="inv_1")
    settled = service.calculate_teacher_batch_earnings(tenant_id="tenant_1", batch_id="batch_1")
    assert settled.pending_payout_amount == Decimal("0.00")
