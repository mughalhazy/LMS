from app.schemas import NotificationSendRequest, QueueDrainRequest, SubscriptionCreateRequest
from app.service import PushService
from app.store import InMemoryPushStore


def make_service() -> PushService:
    return PushService(InMemoryPushStore())


def test_create_mobile_and_web_subscriptions() -> None:
    service = make_service()

    status, mobile_payload = service.create_subscription(
        SubscriptionCreateRequest(
            tenant_id="tenant-acme",
            user_id="user-1",
            channel="mobile",
            endpoint="fcm://project/token",
            device_token="device-token-1",
            platform="ios",
        )
    )
    assert status == 201
    assert mobile_payload["subscription"]["channel"] == "mobile"

    status, web_payload = service.create_subscription(
        SubscriptionCreateRequest(
            tenant_id="tenant-acme",
            user_id="user-1",
            channel="web",
            endpoint="https://push.example/subscriptions/abc",
            auth_key="auth",
            p256dh_key="key",
        )
    )
    assert status == 201
    assert web_payload["subscription"]["channel"] == "web"


def test_send_notifications_and_drain_queue() -> None:
    service = make_service()

    service.create_subscription(
        SubscriptionCreateRequest(
            tenant_id="tenant-acme",
            user_id="user-1",
            channel="mobile",
            endpoint="fcm://project/device-token",
            device_token="device-token-1",
            platform="android",
        )
    )
    service.create_subscription(
        SubscriptionCreateRequest(
            tenant_id="tenant-acme",
            user_id="user-1",
            channel="web",
            endpoint="https://push.example/subscriptions/valid",
            auth_key="auth",
            p256dh_key="key",
        )
    )

    status, queued_payload = service.send_notification(
        NotificationSendRequest(
            tenant_id="tenant-acme",
            user_id="user-1",
            title="Course reminder",
            body="Complete module 3",
            channels=["mobile", "web"],
            data={"course_id": "course-123"},
        )
    )
    assert status == 202
    assert queued_payload["queued"] == 2

    status, drain_payload = service.drain_queue(QueueDrainRequest(max_messages=10))
    assert status == 200
    assert drain_payload["processed"] == 2
    assert drain_payload["delivered"] == 2
    assert drain_payload["failed"] == 0


def test_failed_delivery_marks_queue_message_failed() -> None:
    service = make_service()
    service.create_subscription(
        SubscriptionCreateRequest(
            tenant_id="tenant-acme",
            user_id="user-1",
            channel="web",
            endpoint="https://invalid.example/subscriptions/123",
            auth_key="auth",
            p256dh_key="key",
        )
    )

    service.send_notification(
        NotificationSendRequest(
            tenant_id="tenant-acme",
            user_id="user-1",
            title="Maintenance",
            body="Downtime notice",
            channels=["web"],
        )
    )

    status, drain_payload = service.drain_queue(QueueDrainRequest(max_messages=5))
    assert status == 200
    assert drain_payload["failed"] == 1
    assert drain_payload["failed_messages"][0]["last_error"] == "endpoint_unreachable"
