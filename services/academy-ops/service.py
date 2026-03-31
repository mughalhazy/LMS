from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.academy import AcademyEnrollment
from shared.models.invoice import Invoice

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_SorModule = _load_module("system_of_record_module_for_academy_ops", "services/system-of-record/service.py")
SystemOfRecordService = _SorModule.SystemOfRecordService
UnifiedStudentProfile = _SorModule.UnifiedStudentProfile


@dataclass(frozen=True)
class Branch:
    tenant_id: str
    branch_id: str
    academy_id: str
    name: str
    timezone: str
    active: bool = True


@dataclass(frozen=True)
class Batch:
    tenant_id: str
    branch_id: str
    batch_id: str
    academy_id: str
    title: str
    start_date: date
    end_date: date
    learner_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TeacherAssignment:
    tenant_id: str
    branch_id: str
    batch_id: str
    teacher_id: str
    assigned_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class TimetableSlot:
    tenant_id: str
    branch_id: str
    batch_id: str
    slot_id: str
    teacher_id: str
    start_at: datetime
    end_at: datetime
    room: str


@dataclass(frozen=True)
class AttendanceRecord:
    tenant_id: str
    branch_id: str
    batch_id: str
    learner_id: str
    slot_id: str
    present: bool


@dataclass(frozen=True)
class FeePayment:
    tenant_id: str
    learner_id: str
    payment_id: str
    amount: Decimal
    paid_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RevenueShareAgreement:
    tenant_id: str
    batch_id: str
    teacher_id: str
    share_ratio: Decimal


@dataclass(frozen=True)
class TeacherPerformanceSnapshot:
    tenant_id: str
    batch_id: str
    teacher_id: str
    attendance_rate: Decimal
    completion_rate: Decimal
    learner_satisfaction: Decimal
    captured_at: datetime = field(default_factory=datetime.utcnow)

    def score(self) -> Decimal:
        return (
            (self.attendance_rate * Decimal("0.40"))
            + (self.completion_rate * Decimal("0.35"))
            + (self.learner_satisfaction * Decimal("0.25"))
        ).quantize(Decimal("0.0001"))


@dataclass(frozen=True)
class TeacherPayoutRecord:
    tenant_id: str
    batch_id: str
    teacher_id: str
    invoice_id: str
    revenue_amount: Decimal
    payout_amount: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)


class AcademyOpsService:
    """Academy operations bounded context for branch-level execution data."""

    def __init__(self, *, sor_service: SystemOfRecordService | None = None) -> None:
        self._sor = sor_service or SystemOfRecordService()

        self._branches: dict[tuple[str, str], Branch] = {}
        self._batches: dict[tuple[str, str], Batch] = {}
        self._teacher_assignments: dict[tuple[str, str], TeacherAssignment] = {}
        self._timetable_slots: dict[tuple[str, str], list[TimetableSlot]] = {}
        self._attendance: dict[tuple[str, str], list[AttendanceRecord]] = {}
        self._fee_invoices: dict[tuple[str, str], list[Invoice]] = {}
        self._fee_payments: dict[tuple[str, str], list[FeePayment]] = {}
        self._revenue_share_agreements: dict[tuple[str, str], RevenueShareAgreement] = {}
        self._teacher_performance: dict[tuple[str, str], list[TeacherPerformanceSnapshot]] = {}
        self._teacher_payouts: dict[tuple[str, str], list[TeacherPayoutRecord]] = {}

        self._domain_owner = {
            "academy.branch": "academy-ops",
            "academy.batch": "academy-ops",
            "academy.timetable": "academy-ops",
            "academy.attendance": "academy-ops",
            "academy.teacher_assignment": "academy-ops",
            "academy.fee_tracking": "academy-ops",
            "student.profile": "system-of-record",
            "commerce.invoice": "commerce-service",
            "learning.progress": "learning-service",
            "learning.lesson": "learning-service",
            "learning.course": "learning-service",
        }

    def _key(self, *parts: str) -> tuple[str, ...]:
        return tuple(part.strip() for part in parts)

    def upsert_branch(self, branch: Branch) -> Branch:
        self._branches[self._key(branch.tenant_id, branch.branch_id)] = branch
        return branch

    def create_batch(self, batch: Batch) -> Batch:
        if self._key(batch.tenant_id, batch.branch_id) not in self._branches:
            raise KeyError("branch not found")
        self._batches[self._key(batch.tenant_id, batch.batch_id)] = batch
        return batch

    def assign_teacher(self, assignment: TeacherAssignment) -> TeacherAssignment:
        batch_key = self._key(assignment.tenant_id, assignment.batch_id)
        batch = self._batches.get(batch_key)
        if batch is None:
            raise KeyError("batch not found")
        if batch.branch_id != assignment.branch_id:
            raise ValueError("teacher assignment branch mismatch")
        self._teacher_assignments[batch_key] = assignment
        return assignment

    def teacher_batches(self, *, tenant_id: str, teacher_id: str) -> tuple[Batch, ...]:
        teacher_batch_ids = [
            batch_id
            for (assignment_tenant, batch_id), assignment in self._teacher_assignments.items()
            if assignment_tenant == tenant_id and assignment.teacher_id == teacher_id
        ]
        return tuple(
            self._batches[self._key(tenant_id, batch_id)]
            for batch_id in teacher_batch_ids
            if self._key(tenant_id, batch_id) in self._batches
        )

    def configure_revenue_share(self, agreement: RevenueShareAgreement) -> RevenueShareAgreement:
        if agreement.share_ratio < Decimal("0") or agreement.share_ratio > Decimal("1"):
            raise ValueError("share ratio must be between 0 and 1")
        assignment = self._teacher_assignments.get(self._key(agreement.tenant_id, agreement.batch_id))
        if assignment is None or assignment.teacher_id != agreement.teacher_id:
            raise ValueError("teacher must be assigned to batch before configuring revenue share")
        self._revenue_share_agreements[self._key(agreement.tenant_id, agreement.batch_id)] = agreement
        return agreement

    def record_teacher_performance(self, snapshot: TeacherPerformanceSnapshot) -> TeacherPerformanceSnapshot:
        batch_key = self._key(snapshot.tenant_id, snapshot.batch_id)
        assignment = self._teacher_assignments.get(batch_key)
        if assignment is None or assignment.teacher_id != snapshot.teacher_id:
            raise ValueError("teacher must be assigned to batch before recording performance")
        self._teacher_performance.setdefault(batch_key, []).append(snapshot)
        return snapshot

    def latest_teacher_performance(
        self, *, tenant_id: str, batch_id: str, teacher_id: str
    ) -> TeacherPerformanceSnapshot | None:
        snapshots = self._teacher_performance.get(self._key(tenant_id, batch_id), [])
        teacher_snapshots = [snapshot for snapshot in snapshots if snapshot.teacher_id == teacher_id]
        return teacher_snapshots[-1] if teacher_snapshots else None

    def publish_timetable_slot(self, slot: TimetableSlot) -> TimetableSlot:
        batch_key = self._key(slot.tenant_id, slot.batch_id)
        assignment = self._teacher_assignments.get(batch_key)
        if assignment is None or assignment.teacher_id != slot.teacher_id:
            raise ValueError("teacher must be assigned before publishing timetable")
        if slot.end_at <= slot.start_at:
            raise ValueError("invalid slot time range")
        self._timetable_slots.setdefault(batch_key, []).append(slot)
        return slot

    def register_batch_enrollment(self, enrollment: AcademyEnrollment) -> None:
        self._sor.register_academy_enrollment(enrollment)

    def register_student_profile(self, profile: UnifiedStudentProfile) -> UnifiedStudentProfile:
        return self._sor.upsert_student_profile(profile)

    def record_attendance(self, record: AttendanceRecord) -> AttendanceRecord:
        batch_key = self._key(record.tenant_id, record.batch_id)
        slots = self._timetable_slots.get(batch_key, [])
        if not any(slot.slot_id == record.slot_id for slot in slots):
            raise KeyError("timetable slot not found")
        self._attendance.setdefault(batch_key, []).append(record)
        return record

    def record_fee_invoice(self, *, learner_id: str, invoice: Invoice) -> None:
        key = self._key(invoice.tenant_id, learner_id)
        self._fee_invoices.setdefault(key, []).append(invoice)
        self._sor.post_invoice_to_ledger(student_id=learner_id, invoice=invoice)

    def ingest_commerce_invoice(self, *, learner_id: str, invoice_record: Any) -> Invoice:
        invoice = Invoice.issued(
            invoice_id=invoice_record.invoice_id,
            tenant_id=invoice_record.tenant_id,
            amount=Decimal(invoice_record.amount),
        )
        self.record_fee_invoice(learner_id=learner_id, invoice=invoice)
        return invoice

    def ingest_commerce_invoice_for_batch(
        self,
        *,
        learner_id: str,
        batch_id: str,
        invoice_record: Any,
    ) -> Invoice:
        invoice = self.ingest_commerce_invoice(learner_id=learner_id, invoice_record=invoice_record)
        batch_key = self._key(invoice.tenant_id, batch_id)
        agreement = self._revenue_share_agreements.get(batch_key)
        assignment = self._teacher_assignments.get(batch_key)
        if agreement is not None and assignment is not None:
            payout_amount = (Decimal(invoice.amount) * agreement.share_ratio).quantize(Decimal("0.01"))
            payout = TeacherPayoutRecord(
                tenant_id=invoice.tenant_id,
                batch_id=batch_id,
                teacher_id=assignment.teacher_id,
                invoice_id=invoice.invoice_id,
                revenue_amount=Decimal(invoice.amount),
                payout_amount=payout_amount,
            )
            self._teacher_payouts.setdefault(batch_key, []).append(payout)
        return invoice

    def teacher_payouts(self, *, tenant_id: str, batch_id: str) -> tuple[TeacherPayoutRecord, ...]:
        return tuple(self._teacher_payouts.get(self._key(tenant_id, batch_id), ()))

    def record_fee_payment(self, payment: FeePayment) -> FeePayment:
        key = self._key(payment.tenant_id, payment.learner_id)
        self._fee_payments.setdefault(key, []).append(payment)
        return payment

    def learner_fee_balance(self, *, tenant_id: str, learner_id: str) -> Decimal:
        key = self._key(tenant_id, learner_id)
        invoiced = sum((Decimal(inv.amount) for inv in self._fee_invoices.get(key, [])), start=Decimal("0"))
        paid = sum((p.amount for p in self._fee_payments.get(key, [])), start=Decimal("0"))
        return invoiced - paid

    def has_learning_core_overlap(self) -> bool:
        owned = {cap for cap, owner in self._domain_owner.items() if owner == "academy-ops"}
        learning_core = {
            "learning.progress",
            "learning.lesson",
            "learning.course",
            "learning.assessment",
        }
        return len(owned & learning_core) > 0

    def is_single_source_of_truth(self) -> bool:
        return not self.has_learning_core_overlap()
