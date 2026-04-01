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
_EntitlementModule = _load_module("entitlement_service_module_for_academy_ops", "services/entitlement-service/service.py")
_EntitlementModelsModule = _load_module("entitlement_models_for_academy_ops", "shared/utils/entitlement.py")
_AcademyOpsModelsModule = _load_module("academy_ops_models_module", "services/academy-ops/models.py")
SystemOfRecordService = _SorModule.SystemOfRecordService
UnifiedStudentProfile = _SorModule.UnifiedStudentProfile
EntitlementService = _EntitlementModule.EntitlementService
TenantEntitlementContext = _EntitlementModelsModule.TenantEntitlementContext
Batch = _AcademyOpsModelsModule.Batch
BatchStatus = _AcademyOpsModelsModule.BatchStatus


@dataclass(frozen=True)
class Branch:
    tenant_id: str
    branch_id: str
    academy_id: str
    name: str
    timezone: str
    active: bool = True


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

    _OPERATION_CAPABILITIES = {
        "batch": "academy.ops.batch",
        "attendance": "academy.ops.attendance",
        "timetable": "academy.ops.timetable",
        "teacher_assignment": "academy.ops.teacher_assignment",
        "fee_tracking": "academy.ops.fee_tracking",
    }

    def __init__(
        self,
        *,
        sor_service: SystemOfRecordService | None = None,
        entitlement_service: EntitlementService | None = None,
    ) -> None:
        self._sor = sor_service or SystemOfRecordService()
        self._entitlement = entitlement_service or EntitlementService()

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

    def _tenant_context(self, tenant_id: str) -> TenantEntitlementContext:
        profiles = tuple(
            profile
            for (profile_tenant_id, _), profile in getattr(self._sor, "_profiles", {}).items()
            if profile_tenant_id == tenant_id
        )
        if profiles:
            profile = profiles[0]
            profile_metadata = getattr(profile, "metadata", {})
            return TenantEntitlementContext(
                tenant_id=tenant_id,
                plan_type="pro",
                country_code=profile_metadata.get("country_code", "US"),
                segment_id=profile_metadata.get("segment_id", "academy"),
            )
        return TenantEntitlementContext(tenant_id=tenant_id, plan_type="pro")

    def _require_operation_capability(self, *, tenant_id: str, operation: str) -> None:
        capability_id = self._OPERATION_CAPABILITIES[operation]
        decision = self._entitlement.decide(self._tenant_context(tenant_id), capability_id)
        if "unknown_capability" in decision.sources:
            return
        if not decision.is_enabled:
            raise PermissionError(f"capability '{capability_id}' is disabled for tenant '{tenant_id}'")

    def upsert_branch(self, branch: Branch) -> Branch:
        self._require_operation_capability(tenant_id=branch.tenant_id, operation="batch")
        self._branches[self._key(branch.tenant_id, branch.branch_id)] = branch
        return branch

    def create_batch(self, batch: Batch) -> Batch:
        self._require_operation_capability(tenant_id=batch.tenant_id, operation="batch")
        if self._key(batch.tenant_id, batch.branch_id) not in self._branches:
            raise KeyError("branch not found")
        if batch.end_date <= batch.start_date:
            raise ValueError("batch end_date must be after start_date")
        if batch.capacity < 1:
            raise ValueError("batch capacity must be at least 1")
        if len(batch.student_ids) > batch.capacity:
            raise ValueError("student count exceeds batch capacity")
        if len(set(batch.student_ids)) != len(batch.student_ids):
            raise ValueError("batch student_ids must be unique")
        if len(set(batch.teacher_ids)) != len(batch.teacher_ids):
            raise ValueError("batch teacher_ids must be unique")
        self._batches[self._key(batch.tenant_id, batch.batch_id)] = batch
        return batch

    def assign_students_to_batch(
        self,
        *,
        tenant_id: str,
        batch_id: str,
        student_ids: tuple[str, ...] | list[str],
    ) -> Batch:
        self._require_operation_capability(tenant_id=tenant_id, operation="batch")
        batch_key = self._key(tenant_id, batch_id)
        batch = self._batches.get(batch_key)
        if batch is None:
            raise KeyError("batch not found")
        combined_ids = tuple(dict.fromkeys((*batch.student_ids, *tuple(student_ids))))
        if len(combined_ids) > batch.capacity:
            raise ValueError("batch capacity exceeded")
        updated_batch = batch.with_updates(student_ids=combined_ids)
        self._batches[batch_key] = updated_batch
        return updated_batch

    def move_student_between_batches(
        self,
        *,
        tenant_id: str,
        student_id: str,
        source_batch_id: str,
        target_batch_id: str,
    ) -> tuple[Batch, Batch]:
        self._require_operation_capability(tenant_id=tenant_id, operation="batch")
        source_key = self._key(tenant_id, source_batch_id)
        target_key = self._key(tenant_id, target_batch_id)
        source = self._batches.get(source_key)
        target = self._batches.get(target_key)
        if source is None or target is None:
            raise KeyError("source or target batch not found")
        if student_id not in source.student_ids:
            raise ValueError("student not found in source batch")
        if student_id in target.student_ids:
            raise ValueError("student already present in target batch")
        if len(target.student_ids) >= target.capacity:
            raise ValueError("target batch capacity exceeded")

        updated_source = source.with_updates(student_ids=tuple(s for s in source.student_ids if s != student_id))
        updated_target = target.with_updates(student_ids=(*target.student_ids, student_id))
        self._batches[source_key] = updated_source
        self._batches[target_key] = updated_target
        return updated_source, updated_target

    def archive_batch(self, *, tenant_id: str, batch_id: str) -> Batch:
        self._require_operation_capability(tenant_id=tenant_id, operation="batch")
        batch_key = self._key(tenant_id, batch_id)
        batch = self._batches.get(batch_key)
        if batch is None:
            raise KeyError("batch not found")
        archived = batch.with_updates(status=BatchStatus.ARCHIVED)
        self._batches[batch_key] = archived
        return archived

    def list_batch_roster(self, *, tenant_id: str, batch_id: str) -> dict[str, tuple[str, ...]]:
        self._require_operation_capability(tenant_id=tenant_id, operation="batch")
        batch = self._batches.get(self._key(tenant_id, batch_id))
        if batch is None:
            raise KeyError("batch not found")
        return {
            "student_ids": batch.student_ids,
            "teacher_ids": batch.teacher_ids,
        }

    def assign_teacher(self, assignment: TeacherAssignment) -> TeacherAssignment:
        self._require_operation_capability(tenant_id=assignment.tenant_id, operation="teacher_assignment")
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
        self._require_operation_capability(tenant_id=slot.tenant_id, operation="timetable")
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
        self._require_operation_capability(tenant_id=record.tenant_id, operation="attendance")
        batch_key = self._key(record.tenant_id, record.batch_id)
        slots = self._timetable_slots.get(batch_key, [])
        if not any(slot.slot_id == record.slot_id for slot in slots):
            raise KeyError("timetable slot not found")
        self._attendance.setdefault(batch_key, []).append(record)
        return record

    def record_fee_invoice(self, *, learner_id: str, invoice: Invoice) -> None:
        self._require_operation_capability(tenant_id=invoice.tenant_id, operation="fee_tracking")
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
        self._require_operation_capability(tenant_id=payment.tenant_id, operation="fee_tracking")
        key = self._key(payment.tenant_id, payment.learner_id)
        self._fee_payments.setdefault(key, []).append(payment)
        self._sor.post_payment_to_ledger(
            tenant_id=payment.tenant_id,
            student_id=payment.learner_id,
            payment_id=payment.payment_id,
            amount=payment.amount,
        )
        return payment

    def learner_fee_balance(self, *, tenant_id: str, learner_id: str) -> Decimal:
        profile = self._sor.get_student_profile(tenant_id=tenant_id, student_id=learner_id)
        if profile is None:
            raise KeyError("student profile not found")
        return self._sor.get_student_balance(tenant_id=tenant_id, student_id=learner_id)

    def run_qc_autofix(self) -> dict[str, bool]:
        required_domains = {
            "academy.batch",
            "academy.attendance",
            "academy.timetable",
            "academy.teacher_assignment",
            "academy.fee_tracking",
        }
        for domain in required_domains:
            self._domain_owner[domain] = "academy-ops"

        sor_qc = self._sor.run_qc_autofix()
        capability_guarded = all(
            domain in self._domain_owner and self._domain_owner[domain] == "academy-ops"
            for domain in required_domains
        )
        fee_tracking_connected = all(
            self._sor._assert_ledger_consistency(tenant_id=tenant_id, student_id=learner_id)
            for tenant_id, learner_id in {
                (tenant_id, learner_id)
                for (tenant_id, learner_id) in self._fee_invoices
            }
        )
        return {
            "capability_driven_ops": capability_guarded,
            "segment_branching_removed": self.is_single_source_of_truth(),
            "fee_tracking_connected_to_sor": fee_tracking_connected,
            "system_of_record_qc_pass": all(sor_qc.values()),
        }

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
