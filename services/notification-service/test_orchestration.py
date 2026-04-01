from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from shared.models.template import Template
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


def test_workflow_drives_whatsapp_attendance_and_reminders() -> None:
    orchestrator = NotificationOrchestrator()
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


def test_templates_are_reusable_and_localization_ready() -> None:
    orchestrator = NotificationOrchestrator()
    orchestrator.register_template(
        Template(
            template_id="tpl_payment_reminder",
            type="payment",
            channel="sms",
            variables=["name", "amount"],
            content={
                "default": "Hi {name}, your balance is {amount}.",
                "es-US": "Hola {name}, tu saldo es {amount}.",
            },
        )
    )

    _, en_message = orchestrator.render_template(
        template_id="tpl_payment_reminder",
        payload={"name": "Ava", "amount": "$40"},
        locale="en-US",
    )
    _, es_message = orchestrator.render_template(
        template_id="tpl_payment_reminder",
        payload={"name": "Ava", "amount": "$40"},
        locale="es-US",
    )

    assert en_message == "Hi Ava, your balance is $40."
    assert es_message == "Hola Ava, tu saldo es $40."
