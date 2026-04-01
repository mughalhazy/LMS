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

WorkflowEngine = WorkflowModule.WorkflowEngine


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
    assert attendance_notifies[0]["result"]["capability"] == "communication.whatsapp.operations"

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
    assert fee_notifies[0]["result"]["capability"] == "communication.whatsapp.operations"

    # one idempotency record per unique send (attendance + fee)
    assert len(engine._notification_orchestrator._idempotent_send_log) == 2


def test_whatsapp_replies_are_mapped_to_actions() -> None:
    engine = WorkflowEngine()
    engine.register_phone_user(phone="+1 (555) 000-1111", user_id="parent-1")

    attendance_reply = engine.handle_inbound_whatsapp_envelope(
        {
            "tenant_id": "tenant-whatsapp",
            "source_phone": "+1 (555) 000-1111",
            "message": "WF:wf_default_attendance|OP:attendance|ACTION:confirm",
            "provider_verified": True,
        }
    )
    assert attendance_reply["status"] == "accepted"
    assert attendance_reply["routed_action"] == "confirm_attendance"
    assert attendance_reply["workflow_action"] == "attendance_confirmation_received"
    assert attendance_reply["capability"] == "communication.whatsapp.operations"

    fee_reply = engine.handle_inbound_whatsapp_envelope(
        {
            "tenant_id": "tenant-whatsapp",
            "source_phone": "+1 (555) 000-1111",
            "message": "WF:wf_default_fees|OP:fee|ACTION:ack",
            "provider_verified": True,
        }
    )
    assert fee_reply["status"] == "accepted"
    assert fee_reply["routed_action"] == "acknowledge_reminder"
    assert fee_reply["workflow_action"] == "fee_interaction_acknowledged"
    assert fee_reply["capability"] == "communication.whatsapp.operations"


def test_whatsapp_admin_commands_are_routed_deterministically_via_workflow_engine() -> None:
    engine = WorkflowEngine()
    engine.register_phone_user(phone="+1 (555) 222-3333", user_id="admin-1")

    admin_reply = engine.handle_inbound_whatsapp_envelope(
        {
            "tenant_id": "tenant-whatsapp",
            "source_phone": "+1 (555) 222-3333",
            "message": "ADMIN:fees status",
            "provider_verified": True,
        }
    )

    assert admin_reply["status"] == "accepted"
    assert admin_reply["routed_action"] == "admin_command"
    assert admin_reply["workflow_action"] == "admin_fee_status_lookup"
    assert "action_item_id" in admin_reply
    assert admin_reply["capability"] == "communication.whatsapp.operations"


def test_end_to_end_operational_interface_flow_has_no_broken_loops_or_duplicates() -> None:
    engine = WorkflowEngine()
    engine.bootstrap_default_workflows()
    engine.register_phone_user(phone="+1 (555) 111-0000", user_id="parent-1")
    now = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)

    fee_due_envelope = {
        "event_id": "evt-fee-loop-001",
        "event_type": "fee.due",
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "tenant_id": "tenant-whatsapp",
        "payload": {
            "country_code": "US",
            "segment_id": "academy",
            "student_id": "student-1",
            "invoice_id": "inv-loop-1",
            "amount": "120",
            "currency": "USD",
            "due_date": "2026-04-08",
        },
        "metadata": {"actor": {"user_id": "parent-1"}},
    }

    first = engine.handle_event_envelope(fee_due_envelope)
    duplicate = engine.handle_event_envelope(fee_due_envelope)
    run = engine.run_due(now=now)
    reply = engine.handle_inbound_whatsapp_envelope(
        {
            "tenant_id": "tenant-whatsapp",
            "source_phone": "+1 (555) 111-0000",
            "message": "WF:wf_default_fees|OP:fee|ACTION:ack",
            "provider_verified": True,
        }
    )

    assert len(first["scheduled"]) > 0
    assert duplicate["scheduled"] == []
    assert any(item["step"] == "step.skipped_duplicate" for item in duplicate["trace"])
    assert run["executed"][0]["result"]["status"] == "sent"
    assert run["executed"][0]["result"]["capability"] == "communication.whatsapp.operations"
    assert reply["workflow_action"] == "fee_interaction_acknowledged"
    assert reply["capability"] == "communication.whatsapp.operations"
