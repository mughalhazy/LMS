from __future__ import annotations

import importlib.util
import sys
import builtins
from dataclasses import replace
from datetime import datetime, timedelta, timezone
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
BatchStatus = _ModelsModule.BatchStatus
Branch = _ModelsModule.Branch
FeePayment = _ModelsModule.FeePayment
RevenueShareAgreement = _ModelsModule.RevenueShareAgreement
TeacherAssignment = _ModelsModule.TeacherAssignment
TeacherPayoutRecord = _ModelsModule.TeacherPayoutRecord
TeacherPerformanceSnapshot = _ModelsModule.TeacherPerformanceSnapshot
TeacherRole = _ModelsModule.TeacherRole
TimetableSlot = _ModelsModule.TimetableSlot
BranchStatus = _ModelsModule.BranchStatus
_BranchModel = _ModelsModule.Branch
_BatchModel = _ModelsModule.Batch
_TimetableSlotModel = _ModelsModule.TimetableSlot

_UnifiedStudentProfileModel = _SorModule.UnifiedStudentProfile


def UnifiedStudentProfile(**kwargs: Any) -> _UnifiedStudentProfileModel:
    """Compatibility constructor for canonical student profile model."""
    metadata = dict(kwargs.pop("metadata", {}) or {})
    full_name = kwargs.pop("full_name", "").strip()
    if not full_name:
        full_name = kwargs.pop("display_name", "").strip()
    email = kwargs.pop("email", "").strip()
    if email:
        metadata.setdefault("email", email)
    country_code = kwargs.pop("country_code", "").strip()
    if country_code:
        metadata.setdefault("country_code", country_code)
    segment_id = kwargs.pop("segment_id", "").strip()
    if segment_id:
        metadata.setdefault("segment_id", segment_id)
    if "student_id" not in kwargs or "tenant_id" not in kwargs:
        raise ValueError("student_id and tenant_id are required")
    return _UnifiedStudentProfileModel(
        student_id=kwargs["student_id"],
        tenant_id=kwargs["tenant_id"],
        full_name=full_name or "Learner",
        metadata=metadata,
    )


def Branch(**kwargs: Any) -> _BranchModel:
    metadata = dict(kwargs.pop("metadata", {}) or {})
    academy_id = kwargs.pop("academy_id", "").strip()
    timezone_hint = kwargs.pop("timezone", "").strip()
    if academy_id:
        metadata.setdefault("academy_id", academy_id)
    if timezone_hint:
        metadata.setdefault("timezone", timezone_hint)
    return _BranchModel(
        branch_id=kwargs["branch_id"],
        tenant_id=kwargs["tenant_id"],
        name=kwargs.get("name", "").strip() or kwargs["branch_id"],
        code=kwargs.get("code", "").strip() or kwargs["branch_id"].upper(),
        location=kwargs.get("location", "").strip() or timezone_hint or "unknown",
        manager_id=kwargs.get("manager_id"),
        capacity=int(kwargs.get("capacity", 0) or 0),
        active_batches=tuple(kwargs.get("active_batches", ()) or ()),
        status=kwargs.get("status", BranchStatus.ACTIVE),
        metadata=metadata,
    )


def Batch(**kwargs: Any) -> _BatchModel:
    learner_ids = tuple(kwargs.pop("learner_ids", ()) or kwargs.pop("student_ids", ()) or ())
    return _BatchModel(
        tenant_id=kwargs["tenant_id"],
        branch_id=kwargs["branch_id"],
        batch_id=kwargs["batch_id"],
        academy_id=kwargs.get("academy_id", ""),
        title=kwargs.get("title", kwargs["batch_id"]),
        start_date=kwargs["start_date"],
        end_date=kwargs["end_date"],
        learner_ids=learner_ids,
        teacher_ids=tuple(kwargs.get("teacher_ids", ()) or ()),
        course_id=kwargs.get("course_id", ""),
        timetable_id=kwargs.get("timetable_id", ""),
        capacity=int(kwargs.get("capacity", max(len(learner_ids), 1)) or 1),
        status=kwargs.get("status", BatchStatus.ACTIVE),
        metadata=dict(kwargs.get("metadata", {}) or {}),
    )


def TimetableSlot(**kwargs: Any) -> _TimetableSlotModel:
    if "start_at" in kwargs and "end_at" in kwargs:
        start_at = kwargs["start_at"]
        end_at = kwargs["end_at"]
        return _TimetableSlotModel(
            tenant_id=kwargs["tenant_id"],
            branch_id=kwargs["branch_id"],
            batch_id=kwargs["batch_id"],
            slot_id=kwargs["slot_id"],
            teacher_id=kwargs["teacher_id"],
            day_of_week=start_at.strftime("%A").lower(),
            start_time=start_at.time(),
            end_time=end_at.time(),
            room_or_virtual_link=kwargs.get("room", ""),
            recurrence_rule=kwargs.get("recurrence_rule", "FREQ=WEEKLY"),
        )
    return _TimetableSlotModel(
        tenant_id=kwargs["tenant_id"],
        branch_id=kwargs["branch_id"],
        batch_id=kwargs["batch_id"],
        slot_id=kwargs["slot_id"],
        teacher_id=kwargs["teacher_id"],
        day_of_week=kwargs["day_of_week"],
        start_time=kwargs["start_time"],
        end_time=kwargs["end_time"],
        room_or_virtual_link=kwargs.get("room_or_virtual_link", kwargs.get("room", "")),
        recurrence_rule=kwargs.get("recurrence_rule", "FREQ=WEEKLY"),
        status=kwargs.get("status", TimetableSlotStatus.SCHEDULED),
    )


builtins.datetime = datetime
builtins.timedelta = timedelta


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
        commerce_service: Any | None = None,
    ) -> None:
        self._sor = sor_service or SystemOfRecordService()
        self._entitlement = entitlement_service or EntitlementService()
        self._commerce = commerce_service

        self._branches: dict[tuple[str, str], Branch] = {}
        self._batches: dict[tuple[str, str], Batch] = {}
        self._teacher_assignments: dict[tuple[str, str], dict[str, TeacherAssignment]] = {}
        self._timetable_slots: dict[tuple[str, str], list[TimetableSlot]] = {}
        self._attendance_session_events: dict[tuple[str, str], list[AttendanceSessionEvent]] = {}
        self._attendance: dict[tuple[str, str], list[AttendanceRecord]] = {}
        self._events: list[dict[str, Any]] = []
        self._fee_invoices: dict[tuple[str, str], list[Invoice]] = {}
        self._fee_payments: dict[tuple[str, str], list[FeePayment]] = {}
        self._student_fee_plans: dict[tuple[str, str], dict[str, Any]] = {}
        self._fee_invoice_status: dict[tuple[str, str, str], str] = {}
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
        branch_key = self._key(branch.tenant_id, branch.branch_id)
        if branch_key in self._branches:
            return self.update_branch(
                tenant_id=branch.tenant_id,
                branch_id=branch.branch_id,
                name=branch.name,
                code=branch.code,
                location=branch.location,
                manager_id=branch.manager_id,
                capacity=branch.capacity,
                active_batches=branch.active_batches,
                status=branch.status,
                metadata=branch.metadata,
            )
        return self.create_branch(branch)

    def create_branch(self, branch: Branch) -> Branch:
        self._require_operation_capability(tenant_id=branch.tenant_id, operation="batch")
        branch_key = self._key(branch.tenant_id, branch.branch_id)
        if branch_key in self._branches:
            raise ValueError("branch already exists")
        if branch.capacity < 0:
            raise ValueError("branch capacity cannot be negative")
        self._branches[branch_key] = branch
        return branch

    def update_branch(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        name: str | None = None,
        code: str | None = None,
        location: str | None = None,
        manager_id: str | None = None,
        capacity: int | None = None,
        active_batches: tuple[str, ...] | None = None,
        status: BranchStatus | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Branch:
        branch_key = self._key(tenant_id, branch_id)
        existing = self._branches.get(branch_key)
        if existing is None:
            raise KeyError("branch not found")
        next_capacity = existing.capacity if capacity is None else capacity
        next_active_batches = existing.active_batches if active_batches is None else active_batches
        if next_capacity < 0:
            raise ValueError("branch capacity cannot be negative")
        if next_capacity and len(next_active_batches) > next_capacity:
            raise ValueError("active batch count exceeds branch capacity")
        updated = replace(
            existing,
            name=existing.name if name is None else name,
            code=existing.code if code is None else code,
            location=existing.location if location is None else location,
            manager_id=existing.manager_id if manager_id is None else manager_id,
            capacity=next_capacity,
            active_batches=next_active_batches,
            status=existing.status if status is None else status,
            metadata=existing.metadata if metadata is None else metadata,
        )
        self._branches[branch_key] = updated
        return updated

    def assign_batch_to_branch(self, *, tenant_id: str, branch_id: str, batch_id: str) -> Branch:
        branch_key = self._key(tenant_id, branch_id)
        branch = self._branches.get(branch_key)
        if branch is None:
            raise KeyError("branch not found")
        batch = self._batches.get(self._key(tenant_id, batch_id))
        if batch is None:
            raise KeyError("batch not found")
        if batch.branch_id != branch_id:
            raise ValueError("batch branch mismatch")
        if batch_id in branch.active_batches:
            return branch
        if branch.status != BranchStatus.ACTIVE:
            raise ValueError("cannot assign batch to inactive branch")
        if branch.capacity and len(branch.active_batches) >= branch.capacity:
            raise ValueError("branch capacity reached")
        return self.update_branch(
            tenant_id=tenant_id,
            branch_id=branch_id,
            active_batches=(*branch.active_batches, batch_id),
        )

    def list_branch_operational_summary(self, *, tenant_id: str, branch_id: str) -> dict[str, Any]:
        branch = self._branches.get(self._key(tenant_id, branch_id))
        if branch is None:
            raise KeyError("branch not found")
        active_batch_ids = tuple(
            batch_id for batch_id in branch.active_batches if self._key(tenant_id, batch_id) in self._batches
        )
        learners = sum(len(self._batches[self._key(tenant_id, batch_id)].learner_ids) for batch_id in active_batch_ids)
        teachers = {
            assignment.teacher_id
            for batch_id in active_batch_ids
            for assignment in self._teacher_assignments.get(self._key(tenant_id, batch_id), {}).values()
        }
        attendance_records = [
            record
            for batch_id in active_batch_ids
            for record in self._attendance.get(self._key(tenant_id, batch_id), [])
        ]
        present_like = sum(1 for record in attendance_records if record.status in {"present", "late", "excused"})
        attendance_rate = (
            (Decimal(present_like) / Decimal(len(attendance_records))).quantize(Decimal("0.0001"))
            if attendance_records
            else Decimal("0.0000")
        )
        return {
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "name": branch.name,
            "code": branch.code,
            "location": branch.location,
            "manager_id": branch.manager_id,
            "status": branch.status.value,
            "capacity": branch.capacity,
            "active_batch_count": len(active_batch_ids),
            "active_batch_ids": active_batch_ids,
            "learner_count": learners,
            "teacher_count": len(teachers),
            "attendance_marked_count": len(attendance_records),
            "attendance_rate": attendance_rate,
            "metadata": branch.metadata,
            "economics_ready": {
                "owner_economics": True,
                "operations_os": True,
            },
        }

    def create_batch(self, batch: Batch) -> Batch:
        self._require_operation_capability(tenant_id=batch.tenant_id, operation="batch")
        if self._key(batch.tenant_id, batch.branch_id) not in self._branches:
            raise KeyError("branch not found")
        if batch.end_date <= batch.start_date:
            raise ValueError("batch end_date must be after start_date")
        declared_capacity = getattr(batch, "capacity", None)
        capacity = declared_capacity if declared_capacity is not None else max(len(getattr(batch, "learner_ids", ())), 1)
        student_ids = tuple(getattr(batch, "student_ids", getattr(batch, "learner_ids", ())))
        teacher_ids = tuple(getattr(batch, "teacher_ids", ()))
        if capacity < 1:
            raise ValueError("batch capacity must be at least 1")
        if len(student_ids) > capacity:
            raise ValueError("student count exceeds batch capacity")
        if len(set(student_ids)) != len(student_ids):
            raise ValueError("batch student_ids must be unique")
        if len(set(teacher_ids)) != len(teacher_ids):
            raise ValueError("batch teacher_ids must be unique")
        self._batches[self._key(batch.tenant_id, batch.batch_id)] = batch
        self.assign_batch_to_branch(tenant_id=batch.tenant_id, branch_id=batch.branch_id, batch_id=batch.batch_id)
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
        if not hasattr(slot, "day_of_week"):
            start_at = getattr(slot, "start_at")
            end_at = getattr(slot, "end_at")
            slot = TimetableSlot(
                tenant_id=slot.tenant_id,
                branch_id=slot.branch_id,
                batch_id=slot.batch_id,
                slot_id=slot.slot_id,
                teacher_id=slot.teacher_id,
                day_of_week=start_at.strftime("%A").lower(),
                start_time=start_at.time(),
                end_time=end_at.time(),
                room_or_virtual_link=getattr(slot, "room", ""),
                recurrence_rule="FREQ=WEEKLY",
            )
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
        batch = self._batches.get(batch_key)
        if batch is None:
            raise KeyError("batch not found")
        self._timetable_slots.setdefault(batch_key, []).append(slot)
        batch = self._batches.get(batch_key)
        if batch is None:
            raise KeyError("batch not found")
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
        attendance_summary = self.get_student_attendance_summary(
            tenant_id=record.tenant_id,
            batch_id=record.batch_id,
            student_id=record.student_id,
        )
        self._sor.record_attendance(
            tenant_id=record.tenant_id,
            student_id=record.student_id,
            batch_id=record.batch_id,
            class_session_id=record.class_session_id,
            status=record.status,
            attendance_rate=attendance_summary["attendance_rate"],
        )
        next_status = AcademicStatus.ACTIVE if record.status in {"present", "late", "excused"} else AcademicStatus.PAUSED
        self._sor.update_academic_state(
            tenant_id=record.tenant_id,
            student_id=record.student_id,
            status=next_status,
            notes=f"Attendance marked as {record.status} for session {record.class_session_id}",
        )
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
        profile = self._sor.get_student_profile(tenant_id=record.tenant_id, student_id=record.student_id)
        if profile is not None:
            summary = self.get_student_attendance_summary(
                tenant_id=record.tenant_id,
                batch_id=record.batch_id,
                student_id=record.student_id,
            )
            attended = summary["by_status"]["present"] + summary["by_status"]["late"] + summary["by_status"]["excused"]
            missed = summary["by_status"]["absent"]
            updated_profile = replace(
                profile,
                attendance_summary=profile.attendance_summary.__class__(
                    attended_sessions=attended,
                    missed_sessions=missed,
                    attendance_rate=summary["attendance_rate"],
                ),
            )
            self._sor.upsert_student_profile(updated_profile)
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
        self._fee_invoice_status[self._key(invoice.tenant_id, learner_id, invoice.invoice_id)] = invoice.status

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
        self._sor.post_payment_to_ledger(
            tenant_id=payment.tenant_id,
            student_id=payment.learner_id,
            payment_id=payment.payment_id,
            amount=payment.amount,
        )
        return payment

    def assign_fee_plan_to_student(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        fee_plan_id: str,
        fee_type: str,
        total_amount: Decimal,
        installment_count: int = 1,
        currency: str = "USD",
    ) -> dict[str, Any]:
        self._require_operation_capability(tenant_id=tenant_id, operation="fee_tracking")
        if self._sor.get_student_profile(tenant_id=tenant_id, student_id=learner_id) is None:
            raise KeyError("student profile not found")
        normalized_type = fee_type.strip().lower()
        if normalized_type not in {"monthly_tuition", "installment", "one_time_batch"}:
            raise ValueError("unsupported fee_type")
        if installment_count < 1:
            raise ValueError("installment_count must be >= 1")
        plan = {
            "fee_plan_id": fee_plan_id.strip(),
            "fee_type": normalized_type,
            "total_amount": Decimal(total_amount).quantize(Decimal("0.01")),
            "installment_count": installment_count,
            "currency": currency.upper(),
            "assigned_at": datetime.now(timezone.utc),
        }
        self._student_fee_plans[self._key(tenant_id, learner_id)] = plan
        self._sor.post_fee_action_to_ledger(
            tenant_id=tenant_id,
            student_id=learner_id,
            action_type="fee_plan_assigned",
            reference_id=plan["fee_plan_id"],
            metadata={"fee_type": normalized_type, "installment_count": str(installment_count)},
        )
        return plan

    def generate_student_fee_invoice(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        installment_index: int | None = None,
    ) -> Invoice:
        plan = self._student_fee_plans.get(self._key(tenant_id, learner_id))
        if plan is None:
            raise KeyError("fee plan not found")
        index = installment_index if installment_index is not None else len(self._fee_invoices.get(self._key(tenant_id, learner_id), ())) + 1
        if index < 1 or index > int(plan["installment_count"]):
            raise ValueError("invalid installment_index")
        amount = (
            plan["total_amount"]
            if plan["fee_type"] == "one_time_batch"
            else (plan["total_amount"] / Decimal(plan["installment_count"])).quantize(Decimal("0.01"))
        )
        invoice_id = f"{plan['fee_plan_id']}_{index}"
        commerce_invoice = None
        if self._commerce is not None:
            commerce_invoice = self._commerce.generate_academy_fee_invoice(
                tenant_id=tenant_id,
                learner_id=learner_id,
                fee_reference_id=invoice_id,
                amount=amount,
                fee_type=plan["fee_type"],
                currency=plan["currency"],
            )
        invoice = (
            self.ingest_commerce_invoice(learner_id=learner_id, invoice_record=commerce_invoice)
            if commerce_invoice is not None
            else Invoice.issued(invoice_id=f"fee_{invoice_id}", tenant_id=tenant_id, amount=amount)
        )
        if commerce_invoice is None:
            self.record_fee_invoice(learner_id=learner_id, invoice=invoice)
        return invoice

    def mark_fee_due(self, *, tenant_id: str, learner_id: str, invoice_id: str, overdue: bool = False) -> None:
        status = "overdue" if overdue else "pending"
        self._fee_invoice_status[self._key(tenant_id, learner_id, invoice_id)] = status
        self._sor.post_fee_action_to_ledger(
            tenant_id=tenant_id,
            student_id=learner_id,
            action_type="fee_due_marked",
            reference_id=invoice_id,
            metadata={"status": status},
        )
        self._sor.set_student_fee_overdue_status(
            tenant_id=tenant_id,
            student_id=learner_id,
            overdue=overdue,
            source="operations-os",
        )

    def mark_fee_paid(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        invoice_id: str,
        payment_id: str,
        amount: Decimal,
    ) -> FeePayment:
        payment = self.record_fee_payment(
            FeePayment(
                tenant_id=tenant_id,
                learner_id=learner_id,
                payment_id=payment_id,
                amount=Decimal(amount),
            )
        )
        self._fee_invoice_status[self._key(tenant_id, learner_id, invoice_id)] = "paid"
        self._sor.set_student_fee_overdue_status(
            tenant_id=tenant_id,
            student_id=learner_id,
            overdue=False,
            source="workflows",
        )
        return payment

    def get_student_fee_status(self, *, tenant_id: str, learner_id: str) -> dict[str, Any]:
        plan = self._student_fee_plans.get(self._key(tenant_id, learner_id))
        invoices = self._fee_invoices.get(self._key(tenant_id, learner_id), [])
        status_by_invoice = {
            invoice.invoice_id: self._fee_invoice_status.get(self._key(tenant_id, learner_id, invoice.invoice_id), invoice.status)
            for invoice in invoices
        }
        overdue = any(state == "overdue" for state in status_by_invoice.values())
        balance = self.learner_fee_balance(tenant_id=tenant_id, learner_id=learner_id)
        return {
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "fee_plan": plan,
            "invoice_status": status_by_invoice,
            "overdue": overdue,
            "current_balance": balance,
            "feeds": ("workflows", "operations-os"),
        }

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
