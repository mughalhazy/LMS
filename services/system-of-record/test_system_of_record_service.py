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

AcademicStatus = _service_module.AcademicStatus
LifecycleTransitionError = _service_module.LifecycleTransitionError
SystemOfRecordService = _service_module.SystemOfRecordService
UnifiedStudentProfile = _service_module.UnifiedStudentProfile


def test_student_lifecycle_profile_and_learning_path_are_canonical() -> None:
    service = SystemOfRecordService()

    profile = service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_1",
            student_id="student_1",
            full_name="Ana Learner",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )

    assert profile.lifecycle_state == "prospect"

    service.transition_student_lifecycle(
        tenant_id="tenant_1",
        student_id="student_1",
        state="enrolled",
    )
    active = service.transition_student_lifecycle(
        tenant_id="tenant_1",
        student_id="student_1",
        state="active",
    )
    assert active.lifecycle_state == "active"

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
    assert "lp_python" in persisted.active_batches
    assert "lp_python" in progress["learning_paths"]
    assert persisted.academic_state.status == AcademicStatus.ACTIVE


def test_invalid_lifecycle_transitions_are_rejected() -> None:
    service = SystemOfRecordService()
    service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_lifecycle",
            student_id="student_lifecycle",
            full_name="Lifecycle Learner",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )

    with pytest.raises(LifecycleTransitionError):
        service.transition_student_lifecycle(
            tenant_id="tenant_lifecycle",
            student_id="student_lifecycle",
            state="completed",
        )

    service.transition_student_lifecycle(
        tenant_id="tenant_lifecycle",
        student_id="student_lifecycle",
        state="enrolled",
    )
    service.transition_student_lifecycle(
        tenant_id="tenant_lifecycle",
        student_id="student_lifecycle",
        state="active",
    )
    service.transition_student_lifecycle(
        tenant_id="tenant_lifecycle",
        student_id="student_lifecycle",
        state="completed",
    )
    with pytest.raises(LifecycleTransitionError):
        service.transition_student_lifecycle(
            tenant_id="tenant_lifecycle",
            student_id="student_lifecycle",
            state="active",
        )


def test_student_financial_ledger_uses_shared_invoice_model() -> None:
    service = SystemOfRecordService()
    service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_2",
            student_id="student_2",
            full_name="Leo Student",
            metadata={"country_code": "US", "segment_id": "academy"},
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
    assert profile.ledger_summary.total_invoiced == Decimal("69.00")
    assert profile.ledger_summary.total_paid == Decimal("20.00")
    assert profile.financial_state.current_balance == Decimal("49.00")


def test_config_service_controls_profile_policy_and_qc_ownership_constraints() -> None:
    service = SystemOfRecordService()

    service._config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_3"),
            behavior_tuning={"system_of_record": {"required_profile_fields": ["full_name", "metadata"]}},
        )
    )

    profile = service.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_3",
            student_id="student_3",
            full_name="Meta Student",
            metadata={"sis_id": "S-33", "country_code": "US", "segment_id": "academy"},
        )
    )

    assert profile.metadata["sis_id"] == "S-33"
    assert service.transition_student_lifecycle(
        tenant_id="tenant_3", student_id="student_3", state="enrolled"
    ).lifecycle_state == "enrolled"
    try:
        service.transition_student_lifecycle(
            tenant_id="tenant_3", student_id="student_3", state="prospect"
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
