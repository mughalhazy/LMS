from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app, audit_store, event_publisher, observability, store
from app.security import require_jwt
from app.models import EnrollmentStatus


def _headers(tenant: str, actor: str = "admin-1") -> dict[str, str]:
    return {"x-tenant-id": tenant, "x-actor-id": actor}


def _reset_state() -> None:
    app.dependency_overrides[require_jwt] = lambda: None
    store._by_tenant.clear()  # noqa: SLF001 - test reset for singleton app state
    audit_store._entries.clear()  # noqa: SLF001 - test reset for singleton app state
    event_publisher.events.clear()
    observability.metrics.clear()


def test_enrollment_lifecycle_and_events():
    _reset_state()
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/enrollments",
        headers=_headers("tenant-a"),
        json={
            "learner_id": "learner-10",
            "course_id": "course-10",
            "assignment_source": "manager",
            "cohort_id": "cohort-20",
            "session_id": "session-30",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == EnrollmentStatus.ASSIGNED.value

    transition_response = client.post(
        f"/api/v1/enrollments/{created['id']}/status-transitions",
        headers=_headers("tenant-a", "manager-1"),
        json={"to_status": EnrollmentStatus.ACTIVE.value, "reason": "session started"},
    )
    assert transition_response.status_code == 200
    transitioned = transition_response.json()
    assert transitioned["status"] == EnrollmentStatus.ACTIVE.value

    complete_response = client.post(
        f"/api/v1/enrollments/{created['id']}/status-transitions",
        headers=_headers("tenant-a"),
        json={"to_status": EnrollmentStatus.COMPLETED.value, "reason": "all required modules passed"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == EnrollmentStatus.COMPLETED.value

    assert len(event_publisher.events) == 3
    assert event_publisher.events[-1].payload["status"] == EnrollmentStatus.COMPLETED.value


def test_tenant_isolation_and_duplicate_active_enrollment_guard():
    _reset_state()
    client = TestClient(app)

    payload = {"learner_id": "learner-1", "course_id": "course-1", "assignment_source": "admin"}
    first = client.post("/api/v1/enrollments", headers=_headers("tenant-a"), json=payload)
    assert first.status_code == 201

    conflict = client.post("/api/v1/enrollments", headers=_headers("tenant-a"), json=payload)
    assert conflict.status_code == 409

    other_tenant = client.post("/api/v1/enrollments", headers=_headers("tenant-b"), json=payload)
    assert other_tenant.status_code == 201

    wrong_tenant_fetch = client.get(f"/api/v1/enrollments/{first.json()['id']}", headers=_headers("tenant-b"))
    assert wrong_tenant_fetch.status_code == 404


def test_invalid_transition_and_audit_logs():
    _reset_state()
    client = TestClient(app)

    created = client.post(
        "/api/v1/enrollments",
        headers=_headers("tenant-a"),
        json={"learner_id": "learner-2", "course_id": "course-2", "assignment_source": "admin"},
    ).json()

    invalid = client.post(
        f"/api/v1/enrollments/{created['id']}/status-transitions",
        headers=_headers("tenant-a"),
        json={"to_status": EnrollmentStatus.COMPLETED.value, "reason": "skip"},
    )
    assert invalid.status_code == 422

    audit = client.get("/api/v1/audit-logs", headers=_headers("tenant-a"))
    assert audit.status_code == 200
    assert len(audit.json()) == 1


def test_metrics_and_health_available():
    _reset_state()
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["service"] == "enrollment-service"
