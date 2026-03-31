from __future__ import annotations

import importlib.util
import sys
from datetime import date
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
    assert {alert.alert_type for alert in alerts} == {"fees", "attendance"}
    assert {alert.source for alert in alerts} == {"system-of-record", "academy-ops"}


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
    assert resolved.notes == "Guardian confirmed payment"
    assert len(service.list_actions(tenant_id="tenant", status="open")) == 0


def test_qc_no_business_logic_duplication() -> None:
    service = OperationsOSService()

    assert service.has_business_logic_duplication() is False
