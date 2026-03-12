from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas import (
    DeliveryDrainRequest,
    EventNotificationRequest,
    EventRouteUpsertRequest,
    NotificationOrchestrationRequest,
    PreferenceUpsertRequest,
)
from app.service import NotificationService
from app.store import InMemoryNotificationStore


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
