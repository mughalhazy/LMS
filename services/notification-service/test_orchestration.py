from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from shared.models.workflow import WorkflowAction, WorkflowDefinition, WorkflowTrigger

spec = importlib.util.spec_from_file_location(
    "notification_orchestration",
    Path(__file__).with_name("orchestration.py"),
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
NotificationOrchestrator = module.NotificationOrchestrator
NotificationOrchestrationConfig = module.NotificationOrchestrationConfig


def test_workflow_drives_whatsapp_attendance_and_reminders() -> None:
    orchestrator = NotificationOrchestrator(
        NotificationOrchestrationConfig(
            capability_enabled={"whatsapp_primary_interface": True},
            behavior_tuning={"communication": {"routing_priority": ["sms", "email"]}},
        )
    )
    workflow = WorkflowDefinition(
        workflow_id="wf-ops-1",
        name="Ops Attendance",
        trigger=WorkflowTrigger(trigger_type="inactivity", config={"days": 1}),
        actions=[
            WorkflowAction(
                action_type="send_notification",
                config={
                    "channel": "whatsapp",
                    "operation": "attendance",
                    "message": "Mark attendance for today",
                    "choices": ["PRESENT", "ABSENT"],
                    "recipients": ["+15550000001"],
                },
            ),
            WorkflowAction(
                action_type="send_notification",
                config={
                    "channel": "whatsapp",
                    "operation": "reminder",
                    "message": "Training starts in 1 hour",
                    "choices": ["CONFIRM", "SNOOZE"],
                    "recipients": ["+15550000002"],
                },
            ),
        ],
    )

    result = orchestrator.execute_workflow(
        workflow=workflow,
        tenant_country_code="US",
        context={"recipients": ["+15550000003"]},
    )

    assert result["workflow_id"] == "wf-ops-1"
    assert result["executed_actions"] == 2
    assert all(item["deliveries"][0]["ok"] for item in result["results"])


def test_whatsapp_primary_interface_falls_back_to_sms_then_email_on_failure() -> None:
    orchestrator = NotificationOrchestrator(
        NotificationOrchestrationConfig(
            capability_enabled={"whatsapp_primary_interface": True},
            behavior_tuning={"communication": {"routing_priority": ["sms", "email"]}},
            whatsapp_disabled_recipients={"+15550000011"},
        )
    )

    attempt = orchestrator.send_notification(
        tenant_country_code="PK",
        user_id="+15550000011",
        message="Routing check",
    )

    assert attempt.ok is True
    assert attempt.provider == "sms"
    assert attempt.fallback_used is True


def test_routing_priority_uses_config_when_whatsapp_primary_capability_is_disabled() -> None:
    orchestrator = NotificationOrchestrator(
        NotificationOrchestrationConfig(
            capability_enabled={"whatsapp_primary_interface": False},
            behavior_tuning={"communication": {"routing_priority": ["email", "sms"]}},
        )
    )

    attempt = orchestrator.send_notification(
        tenant_country_code="US",
        user_id="+15550000010",
        message="Config-first email route",
    )

    assert attempt.ok is True
    assert attempt.provider == "email"
    assert attempt.fallback_used is False


def test_interactive_reply_is_parsed_for_workflow_update() -> None:
    orchestrator = NotificationOrchestrator()

    parsed = orchestrator.handle_interactive_reply(
        user_id="+15550000001",
        reply="WF:wf-ops-1|OP:update|ACTION:ack|task=attendance",
    )

    assert parsed["status"] == "accepted"
    assert parsed["workflow_id"] == "wf-ops-1"
    assert parsed["operation"] == "update"
    assert parsed["payload"]["task"] == "attendance"


def test_whatsapp_send_is_idempotent_for_same_key() -> None:
    orchestrator = NotificationOrchestrator()

    first = orchestrator.send_whatsapp_operation(
        tenant_country_code="US",
        user_id="+15550000001",
        workflow_id="wf-ops-2",
        operation="reminder",
        template_name="fee_reminder",
        template_context={"invoice_id": "INV-1", "amount": "100", "currency": "USD", "due_date": "2026-04-10"},
        idempotency_key="evt-1:wf-ops-2:reminder:+15550000001",
    )
    second = orchestrator.send_whatsapp_operation(
        tenant_country_code="US",
        user_id="+15550000001",
        workflow_id="wf-ops-2",
        operation="reminder",
        template_name="fee_reminder",
        template_context={"invoice_id": "INV-1", "amount": "100", "currency": "USD", "due_date": "2026-04-10"},
        idempotency_key="evt-1:wf-ops-2:reminder:+15550000001",
    )

    assert first.ok is True
    assert second.ok is True
    assert len(orchestrator._idempotent_send_log) == 1
