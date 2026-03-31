from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SERVICE_ROOT))

from app.schemas import (  # noqa: E402
    DeliveryDrainRequest,
    EventNotificationRequest,
    EventRouteUpsertRequest,
    NotificationOrchestrationRequest,
    PreferenceUpsertRequest,
)
from app.service import NotificationService  # noqa: E402
from app.store import InMemoryNotificationStore  # noqa: E402


def make_service() -> NotificationService:
    return NotificationService(InMemoryNotificationStore())


def test_orchestration_respects_preferences_and_tenant_scope() -> None:
    service = make_service()

    service.upsert_preference(
        PreferenceUpsertRequest(
            tenant_id="tenant-acme",
            user_id="user1@acme.com",
            category="learning",
            channels={"email": False, "push": True, "in_app": True},
        )
    )

    status, payload = service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-acme",
            category="learning",
            recipients=["user1@acme.com", "user2@acme.com"],
            subject="Reminder",
            body="Complete your assignment",
            channels=["email", "push"],
        )
    )

    assert status == 202
    # user1 gets push only, user2 gets both channels (default allow)
    assert payload["queued"] == 3
    assert all(m["tenant_id"] == "tenant-acme" for m in payload["messages"])


def test_event_based_notifications_use_route_templates() -> None:
    service = make_service()

    service.upsert_event_route(
        EventRouteUpsertRequest(
            tenant_id="tenant-acme",
            event_type="TrainingEnrollmentAssigned",
            category="learning",
            channels=["email", "in_app"],
            subject_template="Enrollment assigned: {course_title}",
            body_template="You were assigned {course_title} due by {due_date}.",
        )
    )

    status, payload = service.process_event(
        EventNotificationRequest(
            tenant_id="tenant-acme",
            event_type="TrainingEnrollmentAssigned",
            actor_id="manager-1",
            recipients=["learner@acme.com"],
            payload={"course_title": "Security 101", "due_date": "2026-12-01"},
        )
    )

    assert status == 202
    assert payload["queued"] == 2
    assert payload["messages"][0]["subject"] == "Enrollment assigned: Security 101"
    assert payload["event"]["tenant_id"] == "tenant-acme"


def test_event_without_route_is_ignored() -> None:
    service = make_service()
    status, payload = service.process_event(
        EventNotificationRequest(
            tenant_id="tenant-acme",
            event_type="UnknownEvent",
            recipients=["learner@acme.com"],
            payload={"k": "v"},
        )
    )
    assert status == 202
    assert payload["status"] == "ignored"


def test_workflow_trigger_event_uses_default_route_templates() -> None:
    service = make_service()
    status, payload = service.process_event(
        EventNotificationRequest(
            tenant_id="tenant-acme",
            event_type="learning.low_engagement",
            actor_id="analytics-service",
            recipients=["learner@acme.com"],
            payload={"learner_id": "learner-1", "course_id": "course-1"},
        )
    )
    assert status == 202
    assert payload["status"] == "accepted"
    assert payload["queued"] == 2
    assert payload["messages"][0]["metadata"]["workflow_action"] == "alert"


def test_workforce_compliance_reminder_route_and_manager_visibility() -> None:
    service = make_service()
    status, payload = service.process_event(
        EventNotificationRequest(
            tenant_id="tenant-acme",
            event_type="workforce.compliance.reminder_required",
            actor_id="progress-service",
            recipients=["manager@acme.com"],
            payload={
                "audience": "workforce",
                "learner_id": "learner-7",
                "course_id": "course-safe-101",
                "due_date": "2026-04-05",
            },
        )
    )
    assert status == 202
    assert payload["status"] == "accepted"
    assert payload["messages"][0]["subject"] == "Mandatory training due soon: course-safe-101"


def test_workforce_event_ignored_for_non_workforce_audience() -> None:
    service = make_service()
    status, payload = service.process_event(
        EventNotificationRequest(
            tenant_id="tenant-acme",
            event_type="workforce.compliance.reminder_required",
            recipients=["manager@acme.com"],
            payload={"audience": "academy", "learner_id": "learner-8", "course_id": "c-1", "due_date": "2026-05-01"},
        )
    )
    assert status == 202
    assert payload["status"] == "ignored"
    assert payload["reason"] == "non_workforce_audience"


def test_drain_delivery_queue_marks_failed_email_recipient() -> None:
    service = make_service()
    service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-acme",
            category="alerts",
            recipients=["not-an-email"],
            subject="Alert",
            body="Check system status",
            channels=["email"],
        )
    )

    status, payload = service.drain_delivery_queue(DeliveryDrainRequest(max_messages=10))
    assert status == 200
    assert payload["failed"] == 1
    assert payload["failed_messages"][0]["failure_reason"] == "unresolvable_email_recipient"


def test_service_crash_and_restart_recovery() -> None:
    service = make_service()
    service.store.crash_service()

    status, payload = service.list_preferences("tenant-acme", "user1@acme.com")
    assert status == 503
    assert payload["error"] == "service_restarting"

    service.store.restart_service()
    status, payload = service.list_preferences("tenant-acme", "user1@acme.com")
    assert status == 200
    assert payload["preferences"] == []


def test_event_bus_failure_opens_circuit_breaker_and_gracefully_degrades() -> None:
    service = make_service()
    service.store.set_event_bus_availability(False)

    status, payload = service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-acme",
            category="alerts",
            recipients=["user1@acme.com"],
            subject="Alert",
            body="Check system status",
            channels=["push"],
        )
    )
    assert status == 202
    assert payload["status"] == "degraded"
    assert payload["reason"] == "event_bus_unavailable"

    # second failed attempt should open circuit breaker
    service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-acme",
            category="alerts",
            recipients=["user1@acme.com"],
            subject="Alert",
            body="Check system status",
            channels=["push"],
        )
    )
    assert service.circuit_breaker_open is True

    status, payload = service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-acme",
            category="alerts",
            recipients=["user1@acme.com"],
            subject="Alert",
            body="Check system status",
            channels=["push"],
        )
    )
    assert payload["reason"] == "event_bus_circuit_open"


def test_database_failure_returns_retry_exhausted_error() -> None:
    service = make_service()
    service.store.set_database_availability(False)

    status, payload = service.upsert_preference(
        PreferenceUpsertRequest(
            tenant_id="tenant-acme",
            user_id="user1@acme.com",
            category="learning",
            channels={"email": True},
        )
    )
    assert status == 503
    assert payload["error"] == "database_unavailable"


def test_gateway_restart_blocks_drain_until_available() -> None:
    service = make_service()
    service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-acme",
            category="alerts",
            recipients=["user1@acme.com"],
            subject="Alert",
            body="Check system status",
            channels=["push"],
        )
    )

    service.store.set_gateway_availability(False)
    status, payload = service.drain_delivery_queue(DeliveryDrainRequest(max_messages=10))
    assert status == 503
    assert payload["error"] == "gateway_unavailable"

    service.store.set_gateway_availability(True)
    status, payload = service.drain_delivery_queue(DeliveryDrainRequest(max_messages=10))
    assert status == 200
    assert payload["delivered"] == 1


def test_message_queue_delays_are_observed_and_recovered() -> None:
    service = make_service()
    service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-acme",
            category="alerts",
            recipients=["user1@acme.com"],
            subject="Alert",
            body="Check system status",
            channels=["push"],
        )
    )

    service.store.set_queue_delay_cycles(2)
    status, payload = service.drain_delivery_queue(DeliveryDrainRequest(max_messages=3))
    assert status == 200
    assert payload["delayed_cycles"] == 2
    assert payload["delivered"] == 1


def test_whatsapp_primary_selected_for_supported_country() -> None:
    service = make_service()
    service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-india",
            tenant_country_code="IN",
            category="alerts",
            recipients=["+919999999999"],
            subject="Alert",
            body="Check system status",
            channels=["whatsapp"],
        )
    )

    status, payload = service.drain_delivery_queue(DeliveryDrainRequest(max_messages=10))
    assert status == 200
    assert payload["delivered"] == 1
    assert payload["delivered_messages"][0]["metadata"]["adapter_provider"] == "whatsapp"
    assert payload["delivered_messages"][0]["metadata"]["adapter_fallback_used"] is False


def test_sms_fallback_used_when_whatsapp_fails() -> None:
    service = make_service()
    service.communication_router.whatsapp_adapter.disabled_recipients.add("+521111111111")
    service.orchestrate_notification(
        NotificationOrchestrationRequest(
            tenant_id="tenant-mx",
            tenant_country_code="MX",
            category="alerts",
            recipients=["+521111111111"],
            subject="Alert",
            body="Check system status",
            channels=["whatsapp"],
        )
    )

    status, payload = service.drain_delivery_queue(DeliveryDrainRequest(max_messages=10))
    assert status == 200
    assert payload["delivered"] == 1
    assert payload["delivered_messages"][0]["metadata"]["adapter_provider"] == "sms"
    assert payload["delivered_messages"][0]["metadata"]["adapter_fallback_used"] is True

from shared.models.workflow import WorkflowAction, WorkflowDefinition, WorkflowTrigger


def test_workflow_engine_executes_low_performance_actions() -> None:
    service = make_service()
    workflow = WorkflowDefinition(
        workflow_id="wf-low-performance",
        name="Low Performance Escalation",
        trigger=WorkflowTrigger(trigger_type="low_performance", config={"threshold": 70}),
        actions=[
            WorkflowAction(
                action_type="send_notification",
                config={
                    "subject": "Performance intervention",
                    "body": "Learner score dropped below threshold",
                    "channels": ["in_app"],
                    "recipients": ["coach@acme.com"],
                },
            ),
            WorkflowAction(action_type="raise_alert", config={"severity": "critical"}),
            WorkflowAction(action_type="create_follow_up_task", config={"assignee": "advisor@acme.com"}),
        ],
    )

    status, payload = service.execute_workflows(
        tenant_id="tenant-acme",
        workflows=[workflow],
        context={"performance_score": 55, "recipients": ["learner@acme.com"]},
    )

    assert status == 200
    assert payload["matched_workflows"] == 1
    assert payload["executed_actions"] == 3
    assert len(service.raised_alerts) == 1
    assert len(service.follow_up_tasks) == 1


def test_workflow_engine_executes_missed_payment_trigger() -> None:
    service = make_service()
    workflow = WorkflowDefinition(
        workflow_id="wf-payment",
        name="Payment Recovery",
        trigger=WorkflowTrigger(trigger_type="missed_payment", config={}),
        actions=[
            WorkflowAction(
                action_type="send_notification",
                config={
                    "subject": "Payment missed",
                    "body": "Please update billing details",
                    "channels": ["email"],
                    "recipients": ["billing@acme.com"],
                },
            ),
            WorkflowAction(action_type="create_follow_up_task", config={"task_type": "billing_follow_up"}),
        ],
    )

    status, payload = service.execute_workflows(
        tenant_id="tenant-acme",
        workflows=[workflow],
        context={"payment_status": "overdue", "recipients": ["owner@acme.com"]},
    )

    assert status == 200
    assert payload["matched_workflows"] == 1
    assert payload["executed_actions"] == 2
    assert service.follow_up_tasks[0]["task_type"] == "billing_follow_up"


def test_workflow_engine_executes_inactivity_trigger_without_false_positives() -> None:
    service = make_service()
    inactivity_workflow = WorkflowDefinition(
        workflow_id="wf-inactive",
        name="Inactivity Nudges",
        trigger=WorkflowTrigger(trigger_type="inactivity", config={"days": 14}),
        actions=[
            WorkflowAction(
                action_type="send_notification",
                config={
                    "subject": "We miss you",
                    "body": "Resume your learning path",
                    "channels": ["push"],
                    "recipients": ["learner@acme.com"],
                },
            )
        ],
    )

    status, payload = service.execute_workflows(
        tenant_id="tenant-acme",
        workflows=[inactivity_workflow],
        context={"inactive_days": 5, "recipients": ["learner@acme.com"]},
    )
    assert status == 200
    assert payload["matched_workflows"] == 0
    assert payload["executed_actions"] == 0

    status, payload = service.execute_workflows(
        tenant_id="tenant-acme",
        workflows=[inactivity_workflow],
        context={"inactive_days": 21, "recipients": ["learner@acme.com"]},
    )
    assert status == 200
    assert payload["matched_workflows"] == 1
    assert payload["executed_actions"] == 1
