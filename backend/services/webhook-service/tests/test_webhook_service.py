from datetime import datetime

from src.webhook_service import WebhookService


class StubTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, payload, headers, timeout):
        self.calls.append({"url": url, "payload": payload, "headers": headers, "timeout": timeout})
        if self.responses:
            return self.responses.pop(0)
        return 200, "ok"


def test_event_subscription_filtering_and_successful_delivery():
    service = WebhookService(jitter_ratio=0)
    now = datetime(2026, 1, 22, 10, 0, 0)
    service.create_subscription(
        subscription_id="sub_1",
        tenant_id="tenant_abc",
        endpoint_url="https://client.example.com/webhooks/lms",
        secret="secret",
        subscribed_events=["course.published"],
        now=now,
    )
    service.process_due_deliveries(transport=StubTransport([(200, "ok")]), now=now)

    deliveries = service.publish_event(
        event_id="evt_90001",
        event_type="course.published",
        tenant_id="tenant_abc",
        data={"course_id": "course_778"},
        now=now,
    )
    assert len(deliveries) == 1

    transport = StubTransport([(200, "accepted")])
    service.process_due_deliveries(transport=transport, now=now)
    assert len(service.pending) == 0
    assert len(transport.calls) == 1


def test_retry_schedule_and_dead_letter_after_max_attempts():
    service = WebhookService(jitter_ratio=0)
    start = datetime(2026, 1, 22, 12, 0, 0)
    service.create_subscription(
        subscription_id="sub_2",
        tenant_id="tenant_abc",
        endpoint_url="https://client.example.com/webhooks/lms",
        secret="secret",
        subscribed_events=["enrollment.completed"],
        now=start,
    )
    service.process_due_deliveries(transport=StubTransport([(200, "ok")]), now=start)

    service.publish_event(
        event_id="evt_90002",
        event_type="enrollment.completed",
        tenant_id="tenant_abc",
        data={"enrollment_id": "enr_4421"},
        now=start,
    )

    failing = StubTransport([(500, "error")] * 8)
    tick = start
    for _ in range(8):
        service.process_due_deliveries(transport=failing, now=tick)
        if service.pending:
            tick = service.pending[0].next_attempt_at

    assert len(service.dead_letters) == 1
    assert service.dead_letters[0].attempt_count == 8


def test_signature_verification_and_replay_protection():
    service = WebhookService(jitter_ratio=0)
    now = datetime(2026, 1, 22, 15, 0, 0)

    payload = '{"hello":"world"}'
    delivery_id = "dlv_test"
    ts = str(int(now.timestamp()))
    signer = service._signer
    headers = signer.build_headers(secret="secret", payload=payload, timestamp=ts, delivery_id=delivery_id)

    assert service.verify_incoming_webhook(secret="secret", payload=payload, headers=headers, now=now) is True
    assert service.verify_incoming_webhook(secret="secret", payload=payload, headers=headers, now=now) is False


def test_deleted_subscription_stops_future_business_events():
    service = WebhookService(jitter_ratio=0)
    now = datetime(2026, 1, 24, 9, 0, 0)
    service.create_subscription(
        subscription_id="sub_3",
        tenant_id="tenant_abc",
        endpoint_url="https://client.example.com/webhooks/lms",
        secret="secret",
        subscribed_events=["course.published"],
        now=now,
    )
    service.process_due_deliveries(transport=StubTransport([(200, "ok")]), now=now)

    service.delete_subscription(subscription_id="sub_3", now=now)
    service.process_due_deliveries(transport=StubTransport([(200, "ok")]), now=now)

    deliveries = service.publish_event(
        event_id="evt_90009",
        event_type="course.published",
        tenant_id="tenant_abc",
        data={"course_id": "course_deleted"},
        now=now,
    )
    assert deliveries == []
