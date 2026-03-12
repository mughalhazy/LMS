from fastapi.testclient import TestClient

from app.main import app, service

client = TestClient(app)


def setup_function() -> None:
    service.__init__()


def test_transactional_delivery_queue_and_processing() -> None:
    queued = client.post(
        "/emails/transactional",
        json={
            "tenant_id": "tenant-1",
            "template_key": "welcome_email",
            "recipient_email": "learner@example.com",
            "recipient_name": "Ada Lovelace",
            "payload": {"first_name": "Ada", "tenant_name": "Acme University"},
            "metadata": {"source": "unit-test"},
            "provider": "smtp",
        },
    )
    assert queued.status_code == 200
    delivery_id = queued.json()["delivery_id"]

    queue_state = client.get("/queue")
    assert queue_state.status_code == 200
    assert queue_state.json()["queue_depth"] == 1

    processed = client.post("/queue/process?max_batch_size=10")
    assert processed.status_code == 200
    assert processed.json() == {"processed_count": 1, "sent_count": 1, "failed_count": 0}

    delivery = client.get(f"/emails/{delivery_id}")
    assert delivery.status_code == 200
    assert delivery.json()["status"] == "sent"


def test_notification_trigger_uses_template_and_rule_prefix() -> None:
    triggered = client.post(
        "/notifications/trigger",
        json={
            "tenant_id": "tenant-2",
            "event_type": "learning.deadline.approaching",
            "recipient_email": "student@example.com",
            "recipient_name": "Grace Hopper",
            "payload": {
                "course_name": "Distributed Systems",
                "assignment_name": "Capstone",
                "due_date": "2026-01-01",
            },
            "provider": "sendgrid",
        },
    )
    assert triggered.status_code == 200
    body = triggered.json()
    assert body["template_key"] == "deadline_reminder"
    assert body["subject"].startswith("[Reminder]")
    assert body["metadata"]["event_type"] == "learning.deadline.approaching"


def test_queue_processing_handles_failures() -> None:
    queued = client.post(
        "/emails/transactional",
        json={
            "tenant_id": "tenant-3",
            "template_key": "password_reset",
            "recipient_email": "force-fail@example.com",
            "payload": {"reset_link": "https://example.com/reset"},
            "provider": "ses",
        },
    )
    assert queued.status_code == 200
    delivery_id = queued.json()["delivery_id"]

    processed = client.post("/queue/process")
    assert processed.status_code == 200
    assert processed.json()["failed_count"] == 1

    delivery = client.get(f"/emails/{delivery_id}")
    assert delivery.status_code == 200
    assert delivery.json()["status"] == "failed"
    assert delivery.json()["error_message"] == "Simulated provider rejection"
