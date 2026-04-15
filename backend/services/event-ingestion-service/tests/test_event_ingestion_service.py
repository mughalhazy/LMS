from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingest_event_normalizes_and_forwards() -> None:
    response = client.post(
        "/events/ingest",
        headers={"X-Tenant-Id": "tenant-a", "X-Request-Id": "req-1"},
        json={
            "event_id": "evt-1",
            "tenant_id": "tenant-a",
            "family": "progress",
            "event_type": "progress.updated",
            "source": "progress-service",
            "timestamp": "2026-01-01T10:00:00Z",
            "trace": {
                "trace_id": "trace-1",
                "correlation_id": "corr-1",
                "causation_id": "cause-1",
            },
            "actor": {"actor_id": "user-5", "actor_type": "learner"},
            "entity": {"entity_id": "lesson-9", "entity_type": "lesson"},
            "payload": {"score": 88, "completed": True},
            "tags": ["lms", "progress", "lms"],
        },
    )

    assert response.status_code == 200
    body = response.json()["result"]
    assert body["record"]["event"]["tenant_id"] == "tenant-a"
    assert body["record"]["event"]["normalized_payload"]["keys"] == ["completed", "score"]
    assert body["record"]["event"]["tags"] == ["lms", "progress"]
    forward_targets = {entry["target"]: entry["accepted"] for entry in body["forward_results"]}
    assert forward_targets == {"analytics": True, "ai": True}


def test_ai_forwarding_can_reject_non_ai_family() -> None:
    response = client.post(
        "/events/ingest",
        headers={"X-Tenant-Id": "tenant-a", "X-Request-Id": "req-2"},
        json={
            "event_id": "evt-2",
            "tenant_id": "tenant-a",
            "family": "enrollment",
            "event_type": "enrollment.created",
            "source": "enrollment-service",
            "timestamp": "2026-01-01T10:00:00Z",
            "trace": {"trace_id": "trace-2", "correlation_id": "corr-2"},
            "payload": {"enrollment_id": "en-1"},
        },
    )

    assert response.status_code == 200
    forward_results = response.json()["result"]["forward_results"]
    ai_result = next(item for item in forward_results if item["target"] == "ai")
    assert ai_result["accepted"] is False
    assert ai_result["reason"] == "family_not_enabled"


def test_health_and_metrics() -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["service"] == "event-ingestion-service"
    assert metrics.json()["events_ingested_total"] >= 2


def test_ingest_rejects_cross_tenant_context() -> None:
    response = client.post(
        "/events/ingest",
        headers={"X-Tenant-Id": "tenant-b", "X-Request-Id": "req-3"},
        json={
            "event_id": "evt-3",
            "tenant_id": "tenant-a",
            "family": "progress",
            "event_type": "progress.updated",
            "source": "progress-service",
            "timestamp": "2026-01-01T10:00:00Z",
            "trace": {"trace_id": "trace-3", "correlation_id": "corr-3"},
            "payload": {"score": 90},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "x_tenant_id_mismatch"
