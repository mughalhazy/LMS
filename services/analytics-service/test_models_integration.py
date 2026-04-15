from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS_PATH = ROOT / "services/analytics-service/models.py"
SOR_MODELS_PATH = ROOT / "shared/models/student_profile.py"
INIT_PATH = ROOT / "services/analytics-service/__init__.py"

models_spec = importlib.util.spec_from_file_location("analytics_models_integration_test", MODELS_PATH)
sor_spec = importlib.util.spec_from_file_location("student_profile_models_integration_test", SOR_MODELS_PATH)
init_spec = importlib.util.spec_from_file_location("analytics_package_init_test", INIT_PATH)
if (
    models_spec is None
    or models_spec.loader is None
    or sor_spec is None
    or sor_spec.loader is None
    or init_spec is None
    or init_spec.loader is None
):
    raise RuntimeError("Unable to load modules")

models_module = importlib.util.module_from_spec(models_spec)
sor_module = importlib.util.module_from_spec(sor_spec)
init_module = importlib.util.module_from_spec(init_spec)
sys.modules[models_spec.name] = models_module
sys.modules[sor_spec.name] = sor_module
sys.modules[init_spec.name] = init_module
sor_spec.loader.exec_module(sor_module)
models_spec.loader.exec_module(models_module)
init_spec.loader.exec_module(init_module)

AcademicState = sor_module.AcademicState
AttendanceSummary = sor_module.AttendanceSummary
FinancialState = sor_module.FinancialState
UnifiedStudentProfile = sor_module.UnifiedStudentProfile

ExamEngineSnapshot = models_module.ExamEngineSnapshot
ProgressSnapshot = models_module.ProgressSnapshot
SystemOfRecordSnapshot = models_module.SystemOfRecordSnapshot


def test_system_of_record_snapshot_from_profile() -> None:
    profile = UnifiedStudentProfile(
        student_id="learner-1",
        tenant_id="tenant-1",
        full_name="Ada Lovelace",
        lifecycle_state="active",
        attendance_summary=AttendanceSummary(attended_sessions=18, missed_sessions=2, attendance_rate=Decimal("90")),
        financial_state=FinancialState(current_balance=Decimal("50"), dues_outstanding=Decimal("30"), payment_status="due", installment_status="active"),
        academic_state=AcademicState(),
    )

    snapshot = SystemOfRecordSnapshot.from_profile(profile)
    assert snapshot.learner_id == "learner-1"
    assert snapshot.tenant_id == "tenant-1"
    assert snapshot.lifecycle_state == "active"
    assert snapshot.attendance_rate == 90.0
    assert snapshot.overdue_balance == 30.0


def test_progress_snapshot_from_progress_payload() -> None:
    payload = {
        "courses": {
            "c1": {"completion_status": "completed"},
            "c2": {"completion_status": "in_progress"},
            "c3": {"completion_status": "completed"},
        },
        "metadata": {
            "weekly_active_minutes": 140,
            "missed_deadlines": 1,
            "activity_streak_days": 6,
        },
    }

    snapshot = ProgressSnapshot.from_progress_payload(payload)
    assert snapshot.completion_rate == 66.67
    assert snapshot.weekly_active_minutes == 140
    assert snapshot.missed_deadlines == 1
    assert snapshot.activity_streak_days == 6


def test_exam_engine_snapshot_from_exam_events() -> None:
    events = [
        {"event_type": "exam.session.submitted", "score": 40},
        {"event_type": "exam.session.submitted", "score": 76},
        {"event_type": "exam.session.expired"},
    ]

    snapshot = ExamEngineSnapshot.from_exam_events(events)
    assert snapshot.average_score == 58.0
    assert snapshot.failed_attempts == 1
    assert snapshot.no_show_count == 1
    assert snapshot.trend_delta == 36.0


def test_package_exports_analytics_models() -> None:
    assert hasattr(init_module, "ExamEngineSnapshot")
    assert hasattr(init_module, "SystemOfRecordSnapshot")
    assert hasattr(init_module, "ProgressSnapshot")
    assert hasattr(init_module, "LearningOptimizationInsightRequest")
