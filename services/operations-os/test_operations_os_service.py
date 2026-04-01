from __future__ import annotations

import importlib.util
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
OPS_MODULE_PATH = ROOT / "services/operations-os/service.py"
SRO_MODULE_PATH = ROOT / "services/system-of-record/service.py"

ops_spec = importlib.util.spec_from_file_location("operations_os_test_module", OPS_MODULE_PATH)
if ops_spec is None or ops_spec.loader is None:
    raise RuntimeError("Unable to load operations-os module")
ops_module = importlib.util.module_from_spec(ops_spec)
sys.modules[ops_spec.name] = ops_module
ops_spec.loader.exec_module(ops_module)

sor_spec = importlib.util.spec_from_file_location("system_of_record_test_module_for_ops", SRO_MODULE_PATH)
if sor_spec is None or sor_spec.loader is None:
    raise RuntimeError("Unable to load system-of-record module")
sor_module = importlib.util.module_from_spec(sor_spec)
sys.modules[sor_spec.name] = sor_module
sor_spec.loader.exec_module(sor_module)

AcademyOpsService = ops_module.AcademyOpsService
OperationsOSService = ops_module.OperationsOSService
UnifiedStudentProfile = sor_module.UnifiedStudentProfile
Invoice = sor_module.Invoice


def test_build_daily_alerts_aggregates_fees_and_attendance() -> None:
    academy_ops = AcademyOpsService()
    sor = sor_module.SystemOfRecordService()

    sor.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_ops",
            student_id="stu_1",
            display_name="Student One",
            email="one@example.com",
            country_code="US",
            segment_id="academy",
        )
    )
    sor.post_invoice_to_ledger(
        student_id="stu_1",
        invoice=Invoice.issued(
            invoice_id="inv_001",
            tenant_id="tenant_ops",
            amount=Decimal("125.00"),
        ),
    )

    academy_ops.upsert_attendance_exception(
        tenant_id="tenant_ops",
        run_date=date(2026, 3, 31),
        student_id="stu_1",
        attendance_state="absent",
        session_ref="sess_44",
    )

    service = OperationsOSService(academy_ops_service=academy_ops, system_of_record_service=sor)
    alerts = service.build_daily_alerts(tenant_id="tenant_ops", run_date=date(2026, 3, 31))

    assert len(alerts) == 2
    assert {alert.alert_type for alert in alerts} == {"unpaid_fees", "absence"}
    assert {alert.source for alert in alerts} == {"system-of-record+commerce", "academy-ops"}


def test_daily_operations_dashboard_surfaces_all_operational_categories() -> None:
    academy_ops = AcademyOpsService()
    sor = sor_module.SystemOfRecordService()

    active_student = UnifiedStudentProfile(
        tenant_id="tenant_ops",
        student_id="stu_active",
        display_name="Student Active",
        email="active@example.com",
        country_code="US",
        segment_id="academy",
        metadata={"activity.last_active_at": "2026-02-01T00:00:00+00:00"},
    )
    inactive_student = UnifiedStudentProfile(
        tenant_id="tenant_ops",
        student_id="stu_inactive",
        display_name="Student Inactive",
        email="inactive@example.com",
        country_code="US",
        segment_id="academy",
        metadata={"activity.last_active_at": "2025-01-01T00:00:00+00:00"},
    )
    sor.upsert_student_profile(active_student)
    sor.upsert_student_profile(inactive_student)
    sor.post_invoice_to_ledger(
        student_id="stu_active",
        invoice=Invoice.issued(invoice_id="inv_002", tenant_id="tenant_ops", amount=Decimal("10.00")),
    )

    academy_ops.upsert_attendance_exception(
        tenant_id="tenant_ops",
        run_date=date.today(),
        student_id="stu_active",
        attendance_state="absent",
        session_ref="sess_99",
    )
    academy_ops.create_operational_alert(
        tenant_id="tenant_ops",
        alert_id="ops_alert_1",
        severity="high",
        message="Generator outage",
    )

    service = OperationsOSService(academy_ops_service=academy_ops, system_of_record_service=sor)
    dashboard = service.get_daily_operations_dashboard("tenant_ops")

    assert dashboard.summary.total_unpaid_fees == 1
    assert dashboard.summary.total_absent_students == 1
    assert dashboard.summary.total_inactive_users >= 1
    assert dashboard.summary.total_unresolved_alerts >= 3


def test_action_system_supports_create_and_resolve() -> None:
    service = OperationsOSService()
    alert = ops_module.DailyAlert(
        alert_id="fees:tenant:student:2026-03-31",
        tenant_id="tenant",
        student_id="student",
        alert_type="fees",
        severity="high",
        message="Outstanding fees due",
        source="system-of-record",
    )

    created = service.create_action(alert=alert, action_type="fee_follow_up", owner="branch_ops")
    assert created.status == "open"
    assert len(service.list_actions(tenant_id="tenant", status="open")) == 1

    resolved = service.resolve_action(action_id=created.action_id, notes="Guardian confirmed payment")
    assert resolved.status == "resolved"
    assert resolved.metadata["resolution_note"] == "Guardian confirmed payment"
    assert len(service.list_actions(tenant_id="tenant", status="open")) == 0


def test_generate_daily_actions_covers_operational_attention_cases() -> None:
    academy_ops = AcademyOpsService()
    sor = sor_module.SystemOfRecordService()
    service = OperationsOSService(academy_ops_service=academy_ops, system_of_record_service=sor)

    sor.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_ops",
            student_id="stu_1",
            display_name="Student One",
            email="one@example.com",
            country_code="US",
            segment_id="academy",
        )
    )
    sor.post_invoice_to_ledger(
        student_id="stu_1",
        invoice=Invoice.issued(invoice_id="inv_001", tenant_id="tenant_ops", amount=Decimal("300.00")),
    )
    academy_ops.upsert_absence_streak(tenant_id="tenant_ops", run_date=date(2026, 3, 31), student_id="stu_1", absent_days=4)
    academy_ops.upsert_student_inactivity(
        tenant_id="tenant_ops", run_date=date(2026, 3, 31), student_id="stu_2", inactive_days=9
    )
    academy_ops.upsert_failed_communication(
        tenant_id="tenant_ops", run_date=date(2026, 3, 31), student_id="stu_3", channel="whatsapp", attempts=3
    )
    academy_ops.upsert_operational_issue(
        tenant_id="tenant_ops",
        run_date=date(2026, 3, 31),
        issue_id="issue_1",
        reason="Branch audit task still open",
        opened_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
        due_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
    )

    created = service.generate_daily_actions(tenant_id="tenant_ops", run_date=date(2026, 3, 31))
    assert len(created) >= 5
    action_types = {action.action_type for action in created}
    assert action_types >= {
        "unpaid_fees_follow_up",
        "repeated_absence_intervention",
        "inactivity_reengagement",
        "failed_communication_retry",
        "overdue_operational_issue",
    }


def test_qc_no_business_logic_duplication() -> None:
    service = OperationsOSService()

    assert service.has_business_logic_duplication() is False
