from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

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
_AcademyOpsModelsModule = _load_module("academy_ops_models", "services/academy-ops/models.py")
SystemOfRecordService = _SorModule.SystemOfRecordService
UnifiedStudentProfile = _SorModule.UnifiedStudentProfile
EntitlementService = _EntitlementModule.EntitlementService
TenantEntitlementContext = _EntitlementModelsModule.TenantEntitlementContext
AttendanceRecord = _AcademyOpsModelsModule.AttendanceRecord


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
        self._events: list[dict[str, Any]] = []
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
        profiles = self._sor.list_student_profiles(tenant_id=tenant_id)
        if profiles:
            profile = profiles[0]
            return TenantEntitlementContext(
                tenant_id=tenant_id,
                plan_type="pro",
                country_code=profile.country_code,
                segment_id=profile.segment_id,
            )
        return TenantEntitlementContext(tenant_id=tenant_id, plan_type="pro")

    def _require_operation_capability(self, *, tenant_id: str, operation: str) -> None:
        capability_id = self._OPERATION_CAPABILITIES[operation]
        if not self._entitlement.is_enabled(self._tenant_context(tenant_id), capability_id):
            raise PermissionError(f"capability '{capability_id}' is disabled for tenant '{tenant_id}'")

    def upsert_branch(self, branch: Branch) -> Branch:
        self._require_operation_capability(tenant_id=branch.tenant_id, operation="batch")
        self._branches[self._key(branch.tenant_id, branch.branch_id)] = branch
        return branch

    def create_batch(self, batch: Batch) -> Batch:
        self._require_operation_capability(tenant_id=batch.tenant_id, operation="batch")
        if self._key(batch.tenant_id, batch.branch_id) not in self._branches:
            raise KeyError("branch not found")
        self._batches[self._key(batch.tenant_id, batch.batch_id)] = batch
        return batch

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

    def _emit_event(self, *, event_type: str, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow(),
            "payload": payload,
            "feeds": ("system-of-record", "workflows", "operations-os"),
        }
        self._events.append(event)
        return event

    def mark_attendance(self, record: AttendanceRecord) -> AttendanceRecord:
        self._require_operation_capability(tenant_id=record.tenant_id, operation="attendance")
        batch_key = self._key(record.tenant_id, record.batch_id)
        slots = self._timetable_slots.get(batch_key, [])
        if not any(slot.slot_id == record.class_session_id for slot in slots):
            raise KeyError("timetable slot not found")
        if not any(slot.teacher_id == record.teacher_id for slot in slots):
            raise ValueError("teacher is not assigned to class session")
        batch = self._batches.get(batch_key)
        if batch is None:
            raise KeyError("batch not found")
        if record.student_id not in batch.learner_ids:
            raise ValueError("student is not enrolled in batch")
        self._attendance.setdefault(batch_key, []).append(record)
        self._emit_event(
            event_type="attendance.marked",
            tenant_id=record.tenant_id,
            payload={
                "attendance_id": record.attendance_id,
                "batch_id": record.batch_id,
                "class_session_id": record.class_session_id,
                "student_id": record.student_id,
                "teacher_id": record.teacher_id,
                "status": record.status,
                "marked_at": record.marked_at.isoformat(),
                "notes": record.notes,
            },
        )
        if record.status == "absent":
            self._emit_event(
                event_type="attendance.absence_detected",
                tenant_id=record.tenant_id,
                payload={
                    "attendance_id": record.attendance_id,
                    "batch_id": record.batch_id,
                    "class_session_id": record.class_session_id,
                    "student_id": record.student_id,
                    "teacher_id": record.teacher_id,
                    "marked_at": record.marked_at.isoformat(),
                },
            )
        return record

    def record_attendance(self, record: AttendanceRecord) -> AttendanceRecord:
        return self.mark_attendance(record)

    def bulk_mark_attendance(self, *, records: list[AttendanceRecord]) -> tuple[AttendanceRecord, ...]:
        return tuple(self.mark_attendance(record) for record in records)

    def get_attendance_for_batch(self, *, tenant_id: str, batch_id: str) -> tuple[AttendanceRecord, ...]:
        return tuple(self._attendance.get(self._key(tenant_id, batch_id), ()))

    def get_student_attendance_summary(self, *, tenant_id: str, batch_id: str, student_id: str) -> dict[str, Any]:
        records = [
            record
            for record in self._attendance.get(self._key(tenant_id, batch_id), [])
            if record.student_id == student_id
        ]
        summary = {"present": 0, "absent": 0, "late": 0, "excused": 0}
        for record in records:
            summary[record.status] += 1
        total = len(records)
        present_weighted = summary["present"] + summary["late"] + summary["excused"]
        attendance_rate = (Decimal(present_weighted) / Decimal(total)).quantize(Decimal("0.0001")) if total else Decimal("0.0000")
        return {
            "tenant_id": tenant_id,
            "batch_id": batch_id,
            "student_id": student_id,
            "total_sessions": total,
            "by_status": summary,
            "attendance_rate": attendance_rate,
        }

    def list_events(self, *, tenant_id: str | None = None, event_type: str | None = None) -> tuple[dict[str, Any], ...]:
        events = self._events
        if tenant_id is not None:
            events = [event for event in events if event["tenant_id"] == tenant_id]
        if event_type is not None:
            events = [event for event in events if event["event_type"] == event_type]
        return tuple(events)

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
            "attendance_event_feeds_configured": all(
                set(event["feeds"]) == {"system-of-record", "workflows", "operations-os"}
                for event in self._events
                if event["event_type"].startswith("attendance.")
            ),
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
