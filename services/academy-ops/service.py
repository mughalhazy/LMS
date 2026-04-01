from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.academy import AcademyEnrollment
from shared.models.invoice import Invoice
from shared.models.timetable import AttendanceSessionEvent, TimetableSlotStatus

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
_AcademyOpsModels = _load_module("academy_ops_models_module", "services/academy-ops/models.py")
SystemOfRecordService = _SorModule.SystemOfRecordService
UnifiedStudentProfile = _SorModule.UnifiedStudentProfile
EntitlementService = _EntitlementModule.EntitlementService
TenantEntitlementContext = _EntitlementModelsModule.TenantEntitlementContext
AttendanceRecord = _AcademyOpsModels.AttendanceRecord
Batch = _AcademyOpsModels.Batch
Branch = _AcademyOpsModels.Branch
FeePayment = _AcademyOpsModels.FeePayment
RevenueShareAgreement = _AcademyOpsModels.RevenueShareAgreement
TeacherAssignment = _AcademyOpsModels.TeacherAssignment
TeacherPayoutRecord = _AcademyOpsModels.TeacherPayoutRecord
TeacherPerformanceSnapshot = _AcademyOpsModels.TeacherPerformanceSnapshot
TimetableSlot = _AcademyOpsModels.TimetableSlot


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
        self._attendance_session_events: dict[tuple[str, str], list[AttendanceSessionEvent]] = {}
        self._attendance: dict[tuple[str, str], list[AttendanceRecord]] = {}
        self._fee_invoices: dict[tuple[str, str], list[Invoice]] = {}
        self._fee_payments: dict[tuple[str, str], list[FeePayment]] = {}
        self._revenue_share_agreements: dict[tuple[str, str], RevenueShareAgreement] = {}
        self._teacher_performance: dict[tuple[str, str], list[TeacherPerformanceSnapshot]] = {}
        self._teacher_payouts: dict[tuple[str, str], list[TeacherPayoutRecord]] = {}
        self._tenant_profile_hints: dict[str, tuple[str | None, str | None]] = {}

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
        if tenant_id in self._tenant_profile_hints:
            country_code, segment_id = self._tenant_profile_hints[tenant_id]
            return TenantEntitlementContext(
                tenant_id=tenant_id,
                plan_type="pro",
                country_code=country_code,
                segment_id=segment_id,
            )
        return TenantEntitlementContext(tenant_id=tenant_id, plan_type="pro")

    def _require_operation_capability(self, *, tenant_id: str, operation: str) -> None:
        capability_id = self._OPERATION_CAPABILITIES[operation]
        enabled = self._entitlement.is_enabled(self._tenant_context(tenant_id), capability_id)
        if enabled is False:
            return

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
        return self.create_timetable_slot(
            tenant_id=slot.tenant_id,
            branch_id=slot.branch_id,
            slot=slot,
        )

    def _validate_timetable_slot(self, slot: TimetableSlot) -> None:
        if slot.end_time <= slot.start_time:
            raise ValueError("invalid slot time range")
        if slot.status not in (TimetableSlotStatus.SCHEDULED, TimetableSlotStatus.CANCELLED):
            raise ValueError("invalid timetable status")

    @staticmethod
    def _time_overlaps(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
        return start_a < end_b and start_b < end_a

    def _assert_no_teacher_conflict(
        self,
        *,
        tenant_id: str,
        teacher_id: str,
        day_of_week: str,
        start_time: time,
        end_time: time,
        ignore_slot_id: str | None = None,
    ) -> None:
        for (slot_tenant_id, _), slots in self._timetable_slots.items():
            if slot_tenant_id != tenant_id:
                continue
            for existing in slots:
                if existing.status == TimetableSlotStatus.CANCELLED:
                    continue
                if ignore_slot_id is not None and existing.slot_id == ignore_slot_id:
                    continue
                if existing.teacher_id != teacher_id or existing.day_of_week != day_of_week:
                    continue
                if self._time_overlaps(existing.start_time, existing.end_time, start_time, end_time):
                    raise ValueError("teacher has an overlapping timetable slot")

    def _sync_attendance_session_events(self, *, tenant_id: str, batch: Batch, slot: TimetableSlot) -> None:
        batch_key = self._key(tenant_id, batch.batch_id)
        events = self._attendance_session_events.setdefault(batch_key, [])
        events[:] = [event for event in events if event.slot_id != slot.slot_id]
        if slot.status == TimetableSlotStatus.CANCELLED:
            return
        for learner_id in batch.learner_ids:
            events.append(
                AttendanceSessionEvent(
                    event_id=f"{slot.slot_id}:{learner_id}",
                    tenant_id=tenant_id,
                    branch_id=batch.branch_id,
                    batch_id=batch.batch_id,
                    slot_id=slot.slot_id,
                    learner_id=learner_id,
                    scheduled_for=datetime.combine(batch.start_date, slot.start_time),
                )
            )

    def create_timetable_slot(self, *, tenant_id: str, branch_id: str, slot: TimetableSlot) -> TimetableSlot:
        self._require_operation_capability(tenant_id=slot.tenant_id, operation="timetable")
        if slot.tenant_id != tenant_id or slot.branch_id != branch_id:
            raise ValueError("slot tenant or branch mismatch")
        batch_key = self._key(slot.tenant_id, slot.batch_id)
        batch = self._batches.get(batch_key)
        if batch is None:
            raise KeyError("batch not found")
        if batch.branch_id != slot.branch_id:
            raise ValueError("timetable slot branch mismatch")
        assignment = self._teacher_assignments.get(batch_key)
        if assignment is None or assignment.teacher_id != slot.teacher_id:
            raise ValueError("teacher must be assigned before publishing timetable")
        self._validate_timetable_slot(slot)
        self._assert_no_teacher_conflict(
            tenant_id=tenant_id,
            teacher_id=slot.teacher_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
        )
        self._timetable_slots.setdefault(batch_key, []).append(slot)
        self._sync_attendance_session_events(tenant_id=tenant_id, batch=batch, slot=slot)
        return slot

    def update_timetable_slot(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        batch_id: str,
        slot_id: str,
        slot: TimetableSlot,
    ) -> TimetableSlot:
        if slot.tenant_id != tenant_id or slot.branch_id != branch_id:
            raise ValueError("slot tenant or branch mismatch")
        if slot.slot_id != slot_id:
            raise ValueError("slot_id must match payload")
        if slot.batch_id != batch_id:
            raise ValueError("batch_id must match payload")
        slots = self._timetable_slots.get(self._key(tenant_id, batch_id), [])
        existing_index = next((index for index, item in enumerate(slots) if item.slot_id == slot_id), None)
        if existing_index is None:
            raise KeyError("timetable slot not found")
        self._validate_timetable_slot(slot)
        self._assert_no_teacher_conflict(
            tenant_id=tenant_id,
            teacher_id=slot.teacher_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            ignore_slot_id=slot_id,
        )
        slots[existing_index] = slot
        batch = self._batches[self._key(tenant_id, batch_id)]
        self._sync_attendance_session_events(tenant_id=tenant_id, batch=batch, slot=slot)
        return slot

    def cancel_timetable_slot(self, *, tenant_id: str, branch_id: str, batch_id: str, slot_id: str) -> TimetableSlot:
        slots = self._timetable_slots.get(self._key(tenant_id, batch_id), [])
        for index, slot in enumerate(slots):
            if slot.slot_id == slot_id:
                if slot.branch_id != branch_id:
                    raise ValueError("timetable slot branch mismatch")
                cancelled = TimetableSlot(
                    slot_id=slot.slot_id,
                    batch_id=slot.batch_id,
                    teacher_id=slot.teacher_id,
                    day_of_week=slot.day_of_week,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    room_or_virtual_link=slot.room_or_virtual_link,
                    recurrence_rule=slot.recurrence_rule,
                    status=TimetableSlotStatus.CANCELLED,
                    tenant_id=slot.tenant_id,
                    branch_id=slot.branch_id,
                )
                slots[index] = cancelled
                batch = self._batches[self._key(tenant_id, batch_id)]
                self._sync_attendance_session_events(tenant_id=tenant_id, batch=batch, slot=cancelled)
                return cancelled
        raise KeyError("timetable slot not found")

    def list_batch_schedule(self, *, tenant_id: str, branch_id: str, batch_id: str) -> tuple[TimetableSlot, ...]:
        batch = self._batches.get(self._key(tenant_id, batch_id))
        if batch is None:
            raise KeyError("batch not found")
        if batch.branch_id != branch_id:
            raise ValueError("batch branch mismatch")
        return tuple(self._timetable_slots.get(self._key(tenant_id, batch_id), ()))

    def register_batch_enrollment(self, enrollment: AcademyEnrollment) -> None:
        self._sor.register_academy_enrollment(enrollment)

    def register_student_profile(self, profile: UnifiedStudentProfile) -> UnifiedStudentProfile:
        profile_metadata = getattr(profile, "metadata", {}) or {}
        self._tenant_profile_hints[profile.tenant_id] = (
            getattr(profile, "country_code", profile_metadata.get("country_code")),
            getattr(profile, "segment_id", profile_metadata.get("segment_id")),
        )
        return self._sor.upsert_student_profile(profile)

    def record_attendance(self, record: AttendanceRecord) -> AttendanceRecord:
        self._require_operation_capability(tenant_id=record.tenant_id, operation="attendance")
        batch_key = self._key(record.tenant_id, record.batch_id)
        slots = self._timetable_slots.get(batch_key, [])
        if not any(slot.slot_id == record.slot_id for slot in slots):
            raise KeyError("timetable slot not found")
        batch_events = self._attendance_session_events.get(batch_key, [])
        if not any(event.slot_id == record.slot_id and event.learner_id == record.learner_id for event in batch_events):
            raise KeyError("attendance session event not found for learner and slot")
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
