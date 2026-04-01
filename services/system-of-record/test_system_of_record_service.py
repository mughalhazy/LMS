from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.academy import AcademyEnrollment, AcademyPackage
from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope
from shared.models.invoice import Invoice

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/system-of-record/service.py"
_service_spec = importlib.util.spec_from_file_location("system_of_record_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load system-of-record module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)

StudentLifecycleState = _service_module.StudentLifecycleState
LifecycleTransitionError = _service_module.LifecycleTransitionError
SystemOfRecordService = _service_module.SystemOfRecordService
UnifiedStudentProfile = _service_module.UnifiedStudentProfile



def test_student_lifecycle_profile_and_learning_path_are_canonical() -> None:
    service = SystemOfRecordService()

    profile = service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_1",
            student_id="student_1",
            display_name="Ana Learner",
            email="ana@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )

    assert profile.lifecycle_state == StudentLifecycleState.PROSPECT

    service.transition_student_lifecycle(
        tenant_id="tenant_1",
        student_id="student_1",
        state=StudentLifecycleState.ENROLLED,
    )
    active = service.transition_student_lifecycle(
        tenant_id="tenant_1",
        student_id="student_1",
        state=StudentLifecycleState.ACTIVE,
    )
    assert active.lifecycle_state == StudentLifecycleState.ACTIVE

    service.register_academy_enrollment(
        AcademyEnrollment(
            tenant_id="tenant_1",
            academy_id="academy_1",
            cohort_id="cohort_1",
            learner_id="student_1",
            package=AcademyPackage.PRO,
        )
    )

    progress = service.assign_learning_path(
        tenant_id="tenant_1",
        student_id="student_1",
        learning_path_id="lp_python",
        course_ids=["course_1", "course_2"],
    )

    persisted = service.get_student_profile(tenant_id="tenant_1", student_id="student_1")
    assert persisted is not None
    assert "lp_python" in persisted.learning_path_ids
    assert "lp_python" in progress["learning_paths"]
    assert persisted.academic_state.lifecycle_state == StudentLifecycleState.ACTIVE
    assert persisted.academic_state.active_learning_path_count == 1


def test_student_financial_ledger_uses_shared_invoice_model() -> None:
    service = SystemOfRecordService()
    service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_2",
            student_id="student_2",
            display_name="Leo Student",
            email="leo@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )

    first = Invoice.issued("inv_100", "tenant_2", Decimal("49.50"))
    second = Invoice.issued("inv_101", "tenant_2", Decimal("19.50"))

    service.post_invoice_to_ledger(student_id="student_2", invoice=first)
    service.post_invoice_to_ledger(student_id="student_2", invoice=second)
    service.post_payment_to_ledger(
        tenant_id="tenant_2",
        student_id="student_2",
        payment_id="pay_200",
        amount=Decimal("20.00"),
    )

    ledger = service.get_student_ledger(tenant_id="tenant_2", student_id="student_2")
    assert len(ledger) == 3
    assert service.get_student_balance(tenant_id="tenant_2", student_id="student_2") == Decimal("49.00")
    profile = service.get_student_profile(tenant_id="tenant_2", student_id="student_2")
    assert profile is not None
    assert profile.financial_state.total_invoiced == Decimal("69.00")
    assert profile.financial_state.total_paid == Decimal("20.00")
    assert profile.financial_state.ledger_balance == Decimal("49.00")


def test_config_service_controls_profile_policy_and_qc_ownership_constraints() -> None:
    service = SystemOfRecordService()

    service._config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_3"),
            behavior_tuning={"system_of_record": {"required_profile_fields": ["display_name", "email", "metadata"]}},
        )
    )

    try:
        service.upsert_student_profile(
            UnifiedStudentProfile(
                tenant_id="tenant_3",
                student_id="student_3",
                display_name="No Meta",
                email="nometa@example.edu",
                country_code="US",
                segment_id="academy",
                metadata={},
            )
        )
        assert False, "expected required metadata enforcement"
    except ValueError:
        pass

    profile = service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_3",
            student_id="student_3",
            display_name="Meta Student",
            email="meta@example.edu",
            country_code="US",
            segment_id="academy",
            metadata={"sis_id": "S-33"},
        )
    )

    assert profile.metadata["sis_id"] == "S-33"
    assert service.transition_student_lifecycle(
        tenant_id="tenant_3", student_id="student_3", state=StudentLifecycleState.ENROLLED
    ).lifecycle_state == StudentLifecycleState.ENROLLED
    try:
        service.transition_student_lifecycle(
            tenant_id="tenant_3", student_id="student_3", state=StudentLifecycleState.PROSPECT
        )
        assert False, "expected invalid lifecycle transition"
    except LifecycleTransitionError:
        pass

    qc = service.run_qc_autofix()
    assert qc["student_profile_unified_state"] is True
    assert qc["ledger_consistency"] is True
    assert qc["lifecycle_transitions"] is True
    assert qc["payments_update_ledger"] is True
    assert qc["fragmented_state_removed"] is True
    assert service.is_single_source_of_truth() is True
    assert service.has_duplicate_data_ownership() is False


def test_operational_read_models_support_ops_and_risk_views() -> None:
    service = SystemOfRecordService()
    service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_ops",
            student_id="student_ops",
            display_name="Ops Learner",
            email="ops@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )
    service.transition_student_lifecycle(
        tenant_id="tenant_ops",
        student_id="student_ops",
        state=StudentLifecycleState.ENROLLED,
    )
    service.transition_student_lifecycle(
        tenant_id="tenant_ops",
        student_id="student_ops",
        state=StudentLifecycleState.ACTIVE,
    )
    service.register_academy_enrollment(
        AcademyEnrollment(
            tenant_id="tenant_ops",
            academy_id="academy_1",
            cohort_id="batch_A",
            learner_id="student_ops",
            package=AcademyPackage.FOUNDATION,
        )
    )
    service.record_attendance(
        tenant_id="tenant_ops",
        student_id="student_ops",
        class_id="class_1",
        attended=False,
    )
    service.post_invoice_to_ledger(
        student_id="student_ops",
        invoice=Invoice.create(
            invoice_id="inv_due_1",
            user_id="tenant_ops",
            order_id="ord_1",
            amount=Decimal("100"),
            status="overdue",
        ),
    )
    state = service.get_student_operational_state(tenant_id="tenant_ops", student_id="student_ops")
    assert state.batch_id == "batch_A"
    assert state.has_dues is True
    assert state.is_overdue is True
    assert state.at_risk is True
    assert "financial_dues" in state.at_risk_reasons
    assert "low_attendance" in state.at_risk_reasons

    dues = service.list_students_with_dues(tenant_id="tenant_ops")
    inactive = service.list_inactive_students(tenant_id="tenant_ops")
    at_risk = service.list_at_risk_students(tenant_id="tenant_ops")
    assert len(dues) == 1
    assert len(inactive) == 0
    assert len(at_risk) == 1
