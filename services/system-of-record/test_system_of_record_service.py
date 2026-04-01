from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

import pytest

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


def test_canonical_lifecycle_flow_is_event_driven_and_validated() -> None:
    service = SystemOfRecordService()
    service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_flow",
            student_id="student_flow",
            display_name="Flow Learner",
            email="flow@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )

    enrolled = service.on_enrollment_created(
        tenant_id="tenant_flow",
        student_id="student_flow",
        learning_object_id="course_1",
        enrollment_id="enr_1",
    )
    assert enrolled.lifecycle_state == StudentLifecycleState.ENROLLED

    active = service.on_learning_started(tenant_id="tenant_flow", student_id="student_flow", enrollment_id="enr_1")
    assert active.lifecycle_state == StudentLifecycleState.ACTIVE

    with_milestone = service.on_progress_milestone(
        tenant_id="tenant_flow",
        student_id="student_flow",
        milestone_key="course_1.lesson_1",
        progress_percentage=25.0,
    )
    assert with_milestone.metadata["milestone.course_1.lesson_1"] == "25.0"

    completed = service.on_completion(tenant_id="tenant_flow", student_id="student_flow", completion_ref="cert_1")
    assert completed.lifecycle_state == StudentLifecycleState.GRADUATED

    with pytest.raises(LifecycleTransitionError):
        service.on_pause(tenant_id="tenant_flow", student_id="student_flow", reason="should fail after completion")


def test_dropout_and_pause_are_valid_only_for_non_terminal_paths() -> None:
    service = SystemOfRecordService()
    service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_alt",
            student_id="student_alt",
            display_name="Alt Learner",
            email="alt@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )
    service.on_enrollment_created(tenant_id="tenant_alt", student_id="student_alt")
    paused = service.on_pause(tenant_id="tenant_alt", student_id="student_alt", reason="leave")
    assert paused.lifecycle_state == StudentLifecycleState.SUSPENDED
    dropped = service.on_dropout(tenant_id="tenant_alt", student_id="student_alt", reason="disengaged")
    assert dropped.lifecycle_state == StudentLifecycleState.WITHDRAWN
