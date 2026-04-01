from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


WorkflowModule = _load_module("workflow_whatsapp_validation_module", "services/workflow-engine/service.py")
NotificationModule = _load_module("notification_whatsapp_validation_module", "services/notification-service/orchestration.py")

WorkflowEngine = WorkflowModule.WorkflowEngine
NotificationOrchestrator = NotificationModule.NotificationOrchestrator


def test_attendance_and_fee_events_route_to_whatsapp_without_duplicate_sends() -> None:
    engine = WorkflowEngine()
    engine.bootstrap_default_workflows()
    now = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)

    attendance_envelope = {
        "event_id": "evt-att-001",
        "event_type": "attendance.marked",
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "tenant_id": "tenant-whatsapp",
        "correlation_id": "corr-att-001",
        "payload": {
            "country_code": "US",
            "segment_id": "academy",
            "student_id": "student-1",
            "attendance_status": "absent",
            "parent_user_ids": ["parent-1"],
        },
        "metadata": {"actor": {"user_id": "teacher-1"}},
    }

    first_attendance = engine.handle_event_envelope(attendance_envelope)
    second_attendance = engine.handle_event_envelope(attendance_envelope)
    executed_attendance = engine.run_due(now=now)

    assert len(first_attendance["scheduled"]) >= 1
    assert second_attendance["scheduled"] == []

    attendance_notifies = [
        item for item in executed_attendance["executed"] if item["step_id"] == "step_attendance_notify"
    ]
    assert attendance_notifies
    assert attendance_notifies[0]["result"]["status"] == "sent"
    assert attendance_notifies[0]["result"]["deliveries"][0]["provider"] == "whatsapp"

    fee_envelope = {
        "event_id": "evt-fee-001",
        "event_type": "fee.due",
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "tenant_id": "tenant-whatsapp",
        "correlation_id": "corr-fee-001",
        "payload": {
            "country_code": "US",
            "segment_id": "academy",
            "student_id": "student-1",
            "invoice_id": "inv-1",
            "amount": "200",
            "currency": "USD",
            "due_date": "2026-04-07",
        },
        "metadata": {"actor": {"user_id": "parent-1"}},
    }

    first_fee = engine.handle_event_envelope(fee_envelope)
    second_fee = engine.handle_event_envelope(fee_envelope)
    executed_fee = engine.run_due(now=now)

    assert len(first_fee["scheduled"]) >= 1
    assert second_fee["scheduled"] == []

    fee_notifies = [item for item in executed_fee["executed"] if item["step_id"] == "step_fees_notify"]
    assert fee_notifies
    assert fee_notifies[0]["result"]["template_name"] == "fee_reminder"
    assert fee_notifies[0]["result"]["deliveries"][0]["provider"] == "whatsapp"

    # one idempotency record per unique send (attendance + fee)
    assert len(engine._notification_orchestrator._idempotent_send_log) == 2


def test_whatsapp_replies_are_mapped_to_actions() -> None:
    orchestrator = NotificationOrchestrator()
    orchestrator.register_phone_user(phone="+1 (555) 000-1111", user_id="parent-1")

    attendance_reply = orchestrator.handle_inbound_whatsapp(
        source_phone="+1 (555) 000-1111",
        reply="WF:wf_default_attendance|OP:attendance|ACTION:confirm",
        provider_verified=True,
    )
    assert attendance_reply["status"] == "accepted"
    assert attendance_reply["routed_action"] == "confirm_attendance"

    fee_reply = orchestrator.handle_inbound_whatsapp(
        source_phone="+1 (555) 000-1111",
        reply="WF:wf_default_fees|OP:fee|ACTION:ack",
        provider_verified=True,
    )
    assert fee_reply["status"] == "accepted"
    assert fee_reply["routed_action"] == "acknowledge_reminder"
