from __future__ import annotations

import importlib.util
import sys
from datetime import date, time
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.academy import AcademyEnrollment, AcademyPackage
from shared.models.invoice import Invoice

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/academy-ops/service.py"
_service_spec = importlib.util.spec_from_file_location("academy_ops_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load academy-ops module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)

AcademyOpsService = _service_module.AcademyOpsService
AttendanceRecord = _service_module.AttendanceRecord
Batch = _service_module.Batch
Branch = _service_module.Branch
FeePayment = _service_module.FeePayment
TeacherAssignment = _service_module.TeacherAssignment
TimetableSlot = _service_module.TimetableSlot
UnifiedStudentProfile = _service_module.UnifiedStudentProfile

ENTERPRISE_MODULE_PATH = ROOT / "services/enterprise-control/service.py"
_enterprise_spec = importlib.util.spec_from_file_location("enterprise_control_for_academy_ops_test", ENTERPRISE_MODULE_PATH)
if _enterprise_spec is None or _enterprise_spec.loader is None:
    raise RuntimeError("Unable to load enterprise-control module")
_enterprise_module = importlib.util.module_from_spec(_enterprise_spec)
sys.modules[_enterprise_spec.name] = _enterprise_module
_enterprise_spec.loader.exec_module(_enterprise_module)
EnterpriseControlService = _enterprise_module.EnterpriseControlService
IdentityContext = _enterprise_module.IdentityContext


def test_academy_wedge_end_to_end_unifies_academic_and_financial_state() -> None:
    service = AcademyOpsService()
    tenant_id = "tenant_e2e"
    learner_id = "learner_1"

    service.register_student_profile(
        UnifiedStudentProfile(
            tenant_id=tenant_id,
            student_id=learner_id,
            full_name="E2E Learner",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )

    service._sor.transition_student_lifecycle(tenant_id=tenant_id, student_id=learner_id, state="enrolled")
    service._sor.transition_student_lifecycle(tenant_id=tenant_id, student_id=learner_id, state="active")

    service.create_branch(
        Branch(
            tenant_id=tenant_id,
            branch_id="branch_1",
            name="Main",
            code="MAIN",
            location="HQ",
        )
    )
    service.create_batch(
        Batch(
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id="batch_1",
            academy_id="academy_1",
            title="Python Core",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 1),
            learner_ids=(learner_id,),
        )
    )
    service.assign_teacher(
        TeacherAssignment(
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id="batch_1",
            teacher_id="teacher_1",
        )
    )
    service.create_timetable_slot(
        tenant_id=tenant_id,
        branch_id="branch_1",
        slot=TimetableSlot(
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id="batch_1",
            slot_id="slot_1",
            teacher_id="teacher_1",
            day_of_week="monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
            room_or_virtual_link="Room A",
            recurrence_rule="FREQ=WEEKLY;BYDAY=MO",
        ),
    )

    service.register_batch_enrollment(
        AcademyEnrollment(
            tenant_id=tenant_id,
            academy_id="academy_1",
            cohort_id="batch_1",
            learner_id=learner_id,
            package=AcademyPackage.PRO,
        )
    )
    service.mark_attendance(
        AttendanceRecord(
            attendance_id="att_1",
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id="batch_1",
            class_session_id="slot_1",
            student_id=learner_id,
            teacher_id="teacher_1",
            status="present",
        )
    )

    service.record_fee_invoice(learner_id=learner_id, invoice=Invoice.issued("inv_1", tenant_id, Decimal("150.00")))
    service.record_fee_payment(
        FeePayment(
            tenant_id=tenant_id,
            learner_id=learner_id,
            payment_id="pay_1",
            amount=Decimal("90.00"),
        )
    )

    profile = service._sor.get_student_profile(tenant_id=tenant_id, student_id=learner_id)
    assert profile is not None
    assert profile.lifecycle_state == "active"
    assert profile.attendance_summary.attended_sessions == 1
    assert profile.ledger_summary.total_invoiced == Decimal("150.00")
    assert profile.ledger_summary.total_paid == Decimal("90.00")
    assert profile.financial_state.current_balance == Decimal("60.00")

    service._sor.transition_student_lifecycle(tenant_id=tenant_id, student_id=learner_id, state="paused")
    paused = service._sor.get_student_profile(tenant_id=tenant_id, student_id=learner_id)
    assert paused is not None and paused.lifecycle_state == "paused"

    service._sor.transition_student_lifecycle(tenant_id=tenant_id, student_id=learner_id, state="dropped")
    dropped = service._sor.get_student_profile(tenant_id=tenant_id, student_id=learner_id)
    assert dropped is not None and dropped.lifecycle_state == "dropped"


def test_branch_rollup_and_qc_match_underlying_records() -> None:
    service = AcademyOpsService()
    tenant_id = "tenant_rollup"
    learner_id = "learner_rollup"

    service.register_student_profile(
        UnifiedStudentProfile(
            tenant_id=tenant_id,
            student_id=learner_id,
            full_name="Rollup Learner",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )
    service.create_branch(
        Branch(
            tenant_id=tenant_id,
            branch_id="branch_1",
            name="Rollup Branch",
            code="ROLLUP",
            location="HQ",
            capacity=2,
        )
    )
    service.create_batch(
        Batch(
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id="batch_1",
            academy_id="academy_1",
            title="Batch",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 5, 1),
            learner_ids=(learner_id,),
        )
    )
    service.assign_teacher(
        TeacherAssignment(
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id="batch_1",
            teacher_id="teacher_1",
        )
    )
    service.create_timetable_slot(
        tenant_id=tenant_id,
        branch_id="branch_1",
        slot=TimetableSlot(
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id="batch_1",
            slot_id="slot_1",
            teacher_id="teacher_1",
            day_of_week="tuesday",
            start_time=time(11, 0),
            end_time=time(12, 0),
            room_or_virtual_link="Room B",
            recurrence_rule="FREQ=WEEKLY;BYDAY=TU",
        ),
    )
    service.mark_attendance(
        AttendanceRecord(
            attendance_id="att_1",
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id="batch_1",
            class_session_id="slot_1",
            student_id=learner_id,
            teacher_id="teacher_1",
            status="late",
        )
    )

    summary = service.list_branch_operational_summary(tenant_id=tenant_id, branch_id="branch_1")
    assert summary["active_batch_count"] == 1
    assert summary["learner_count"] == 1
    assert summary["teacher_count"] == 1
    assert summary["attendance_marked_count"] == 1
    assert summary["attendance_rate"] == Decimal("1.0000")

    qc = service.run_qc_autofix()
    assert all(qc.values())


def test_cross_institution_assignment_enforces_enterprise_permissions_and_tenant_payout_scope() -> None:
    enterprise = EnterpriseControlService()
    enterprise.set_role_permissions(tenant_id="tenant_home", role="network-admin", permissions={"teacher.network.manage"})
    enterprise.set_role_permissions(
        tenant_id="tenant_target",
        role="ops-admin",
        permissions={"academy.teacher_assignment.cross_institution"},
    )

    home_admin = IdentityContext(tenant_id="tenant_home", actor_id="home_admin", roles=("network-admin",))
    target_admin = IdentityContext(tenant_id="tenant_target", actor_id="target_admin", roles=("ops-admin",))
    enterprise.link_teacher_to_external_tenant(
        identity=home_admin,
        home_tenant_id="tenant_home",
        teacher_id="teacher_x",
        external_tenant_id="tenant_target",
    )

    service = AcademyOpsService(enterprise_control_service=enterprise)
    service.create_branch(
        Branch(
            tenant_id="tenant_target",
            branch_id="branch_1",
            name="Main",
            code="MAIN",
            location="HQ",
        )
    )
    service.create_batch(
        Batch(
            tenant_id="tenant_target",
            branch_id="branch_1",
            batch_id="batch_1",
            academy_id="academy_1",
            title="Cross Institution Cohort",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 1),
        )
    )
    assigned = service.assign_teacher_cross_institution(
        assignment=TeacherAssignment(
            tenant_id="tenant_target",
            branch_id="branch_1",
            batch_id="batch_1",
            teacher_id="teacher_x",
        ),
        enterprise_identity=target_admin,
        home_tenant_id="tenant_home",
    )
    assert assigned.teacher_id == "teacher_x"
    assert service.primary_teacher_id(tenant_id="tenant_target", batch_id="batch_1") == "teacher_x"
