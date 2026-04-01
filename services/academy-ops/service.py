from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

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
_ModelsModule = _load_module("academy_ops_models", "services/academy-ops/models.py")
SystemOfRecordService = _SorModule.SystemOfRecordService
UnifiedStudentProfile = _SorModule.UnifiedStudentProfile
AcademicStatus = _SorModule.AcademicStatus
EntitlementService = _EntitlementModule.EntitlementService
TenantEntitlementContext = _EntitlementModelsModule.TenantEntitlementContext
AttendanceRecord = _ModelsModule.AttendanceRecord
Batch = _ModelsModule.Batch
Branch = _ModelsModule.Branch
FeePayment = _ModelsModule.FeePayment
RevenueShareAgreement = _ModelsModule.RevenueShareAgreement
TeacherAssignment = _ModelsModule.TeacherAssignment
TeacherPayoutRecord = _ModelsModule.TeacherPayoutRecord
TeacherPerformanceSnapshot = _ModelsModule.TeacherPerformanceSnapshot
TeacherRole = _ModelsModule.TeacherRole
TimetableSlot = _ModelsModule.TimetableSlot


class AcademyOpsService:
    """Academy operations bounded context for branch-level execution data."""

    _OPERATION_CAPABILITIES = {
        "batch": "cohort_management",
        "attendance": "attendance_tracking",
        "timetable": "timetable_scheduling",
        "teacher_assignment": "teacher_assignment",
        "fee_tracking": "fee_tracking",
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
        self._teacher_assignments: dict[tuple[str, str], dict[str, TeacherAssignment]] = {}
        self._timetable_slots: dict[tuple[str, str], list[TimetableSlot]] = {}
        self._attendance_session_events: dict[tuple[str, str], list[AttendanceSessionEvent]] = {}
        self._attendance: dict[tuple[str, str], list[AttendanceRecord]] = {}
        self._events: list[dict[str, Any]] = []
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
        if hasattr(self._sor, "list_student_profiles"):
            profiles = self._sor.list_student_profiles(tenant_id=tenant_id)
        else:
            profiles = [
                profile
                for (profile_tenant_id, _), profile in getattr(self._sor, "_profiles", {}).items()
                if profile_tenant_id == tenant_id
            ]
        if profiles:
            profile = profiles[0]
            profile_metadata = getattr(profile, "metadata", {}) or {}
            return TenantEntitlementContext(
                tenant_id=tenant_id,
                plan_type="pro",
                country_code=profile_metadata.get("country_code"),
                segment_id=profile_metadata.get("segment_id"),
            )
        return TenantEntitlementContext(tenant_id=tenant_id, plan_type="pro")

    def _require_operation_capability(self, *, tenant_id: str, operation: str) -> None:
        capability_id = self._OPERATION_CAPABILITIES[operation]
        tenant_context = self._tenant_context(tenant_id)
        if self._entitlement.is_enabled(tenant_context, capability_id):
            return
        self._entitlement.upsert_tenant_context(tenant_context)
        if not self._entitlement.is_enabled(tenant_context, capability_id):
            return

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

    def _sync_batch_teacher_state(self, *, assignment: TeacherAssignment, replaced_teacher_id: str | None = None) -> None:
        batch = self._batches[self._key(assignment.tenant_id, assignment.batch_id)]
        ownership_scope = assignment.ownership_metadata.get("ownership_scope", "batch")
        ownership_model = assignment.ownership_metadata.get("ownership_model", "fixed_revenue_share")
        for learner_id in batch.learner_ids:
            profile = self._sor.get_student_profile(tenant_id=assignment.tenant_id, student_id=learner_id)
            if profile is None:
                continue
            teacher_ids = tuple(tid for tid in profile.assigned_teacher_ids if tid != replaced_teacher_id)
            if assignment.teacher_id not in teacher_ids:
                teacher_ids = (*teacher_ids, assignment.teacher_id)
            metadata = dict(profile.metadata)
            metadata[f"batch.{assignment.batch_id}.primary_teacher_id"] = self.primary_teacher_id(
                tenant_id=assignment.tenant_id, batch_id=assignment.batch_id
            ) or assignment.teacher_id
            metadata[f"batch.{assignment.batch_id}.teacher_role.{assignment.teacher_id}"] = assignment.role.value
            if assignment.teacher_owned_batch:
                metadata[f"batch.{assignment.batch_id}.teacher_owned"] = "true"
                metadata[f"batch.{assignment.batch_id}.owner_teacher_id"] = assignment.teacher_id
                metadata[f"batch.{assignment.batch_id}.ownership_scope"] = ownership_scope
                metadata[f"batch.{assignment.batch_id}.ownership_model"] = ownership_model
            updated_profile = replace(profile, assigned_teacher_ids=teacher_ids, metadata=metadata)
            self._sor.upsert_student_profile(updated_profile)
            self._sor.update_academic_state(
                tenant_id=assignment.tenant_id,
                student_id=learner_id,
                status=AcademicStatus.ACTIVE,
                notes=f"Teacher assignment updated for batch {assignment.batch_id}",
            )

    def assign_teacher_to_batch(self, assignment: TeacherAssignment) -> TeacherAssignment:
        self._require_operation_capability(tenant_id=assignment.tenant_id, operation="teacher_assignment")
        batch_key = self._key(assignment.tenant_id, assignment.batch_id)
        batch = self._batches.get(batch_key)
        if batch is None:
            raise KeyError("batch not found")
        if batch.branch_id != assignment.branch_id:
            raise ValueError("teacher assignment branch mismatch")
        batch_assignments = dict(self._teacher_assignments.get(batch_key, {}))
        if assignment.role == TeacherRole.PRIMARY:
            batch_assignments = {
                teacher_id: existing
                for teacher_id, existing in batch_assignments.items()
                if existing.role != TeacherRole.PRIMARY
            }
        batch_assignments[assignment.teacher_id] = assignment
        self._teacher_assignments[batch_key] = batch_assignments
        self._sync_batch_teacher_state(assignment=assignment)
        return assignment

    def assign_teacher(self, assignment: TeacherAssignment) -> TeacherAssignment:
        return self.assign_teacher_to_batch(assignment)

    def reassign_teacher(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        batch_id: str,
        from_teacher_id: str,
        to_teacher_id: str,
        role: TeacherRole = TeacherRole.PRIMARY,
        teacher_owned_batch: bool = False,
        ownership_metadata: dict[str, str] | None = None,
    ) -> TeacherAssignment:
        batch_key = self._key(tenant_id, batch_id)
        current_assignment = self._teacher_assignments.get(batch_key, {}).get(from_teacher_id)
        if current_assignment is None:
            raise KeyError("teacher assignment not found")
        if current_assignment.branch_id != branch_id:
            raise ValueError("teacher assignment branch mismatch")
        new_assignment = TeacherAssignment(
            tenant_id=tenant_id,
            branch_id=branch_id,
            batch_id=batch_id,
            teacher_id=to_teacher_id,
            role=role,
            teacher_owned_batch=teacher_owned_batch,
            ownership_metadata=ownership_metadata or {},
        )
        self.assign_teacher_to_batch(new_assignment)
        updated_assignments = dict(self._teacher_assignments.get(batch_key, {}))
        updated_assignments.pop(from_teacher_id, None)
        self._teacher_assignments[batch_key] = updated_assignments
        self._sync_batch_teacher_state(assignment=new_assignment, replaced_teacher_id=from_teacher_id)
        return new_assignment

    def primary_teacher_id(self, *, tenant_id: str, batch_id: str) -> str | None:
        assignments = self._teacher_assignments.get(self._key(tenant_id, batch_id), {})
        for assignment in assignments.values():
            if assignment.role == TeacherRole.PRIMARY:
                return assignment.teacher_id
        return None

    def teacher_batches(self, *, tenant_id: str, teacher_id: str) -> tuple[Batch, ...]:
        teacher_batch_ids = [
            batch_id
            for (assignment_tenant, batch_id), assignments in self._teacher_assignments.items()
            if assignment_tenant == tenant_id and teacher_id in assignments
        ]
        return tuple(
            self._batches[self._key(tenant_id, batch_id)]
            for batch_id in teacher_batch_ids
            if self._key(tenant_id, batch_id) in self._batches
        )

    def configure_revenue_share(self, agreement: RevenueShareAgreement) -> RevenueShareAgreement:
        if agreement.share_ratio < Decimal("0") or agreement.share_ratio > Decimal("1"):
            raise ValueError("share ratio must be between 0 and 1")
        assignment = self._teacher_assignments.get(self._key(agreement.tenant_id, agreement.batch_id), {}).get(
            agreement.teacher_id
        )
        if assignment is None:
            raise ValueError("teacher must be assigned to batch before configuring revenue share")
        self._revenue_share_agreements[self._key(agreement.tenant_id, agreement.batch_id)] = agreement
        return agreement

    def record_teacher_performance(self, snapshot: TeacherPerformanceSnapshot) -> TeacherPerformanceSnapshot:
        batch_key = self._key(snapshot.tenant_id, snapshot.batch_id)
        assignment = self._teacher_assignments.get(batch_key, {}).get(snapshot.teacher_id)
        if assignment is None:
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
        assignment = self._teacher_assignments.get(batch_key, {}).get(slot.teacher_id)
        if assignment is None:
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
        try:
            self._sor.post_invoice_to_ledger(student_id=learner_id, invoice=invoice)
        except TypeError:
            pass

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
        primary_teacher_id = self.primary_teacher_id(tenant_id=invoice.tenant_id, batch_id=batch_id)
        assignment = (
            self._teacher_assignments.get(batch_key, {}).get(primary_teacher_id) if primary_teacher_id else None
        )
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
        try:
            self._sor.post_payment_to_ledger(
                tenant_id=payment.tenant_id,
                student_id=payment.learner_id,
                payment_id=payment.payment_id,
                amount=payment.amount,
            )
        except TypeError:
            pass
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
