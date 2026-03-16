from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from src.repository import InMemorySessionRepository
from src.service import (
    SessionService,
    SessionValidationError,
    TenantBoundaryError,
)


def _make_service() -> SessionService:
    return SessionService(InMemorySessionRepository())


def _create_online_session(service: SessionService, tenant_id: str = "tenant-a"):
    return service.create_session(
        tenant_id=tenant_id,
        created_by="author-1",
        title="Office Hours",
        course_id="course-1",
        delivery_mode="online",
        delivery_metadata={"online_join_url": "https://meet.example.com/room"},
        cohort_ids=["cohort-1"],
    )


def test_create_schedule_and_lifecycle_events() -> None:
    service = _make_service()
    session = _create_online_session(service)

    scheduled = service.schedule_session(
        tenant_id="tenant-a",
        session_id=session.session_id,
        scheduled_by="author-1",
        timezone_name="UTC",
        start_at=datetime.now(timezone.utc) + timedelta(days=1),
        end_at=datetime.now(timezone.utc) + timedelta(days=1, hours=2),
        recurrence_rule="FREQ=WEEKLY;COUNT=2",
    )

    assert scheduled.status.value == "scheduled"

    started = service.start_session(tenant_id="tenant-a", session_id=session.session_id, actor_id="inst-1")
    assert started.status.value == "live"
    assert started.actual_start_at is not None

    completed = service.complete_session(tenant_id="tenant-a", session_id=session.session_id, actor_id="inst-1")
    assert completed.status.value == "completed"
    assert completed.actual_end_at is not None

    archived = service.archive_session(tenant_id="tenant-a", session_id=session.session_id, actor_id="ops-1")
    assert archived.status.value == "archived"

    events = service.repository.list_events(tenant_id="tenant-a")
    assert [evt.event_type for evt in events] == [
        "session.created.v1",
        "session.scheduled.v1",
        "session.started.v1",
        "session.completed.v1",
        "session.archived.v1",
    ]


def test_delivery_mode_constraints_and_reschedule_history() -> None:
    service = _make_service()

    with pytest.raises(SessionValidationError):
        service.create_session(
            tenant_id="tenant-a",
            created_by="author-1",
            title="Invalid in person",
            course_id="course-1",
            delivery_mode="in_person",
            delivery_metadata={},
        )

    hybrid = service.create_session(
        tenant_id="tenant-a",
        created_by="author-1",
        title="Hybrid seminar",
        course_id="course-2",
        delivery_mode="hybrid",
        delivery_metadata={
            "online_join_url": "https://meet.example.com/hybrid",
            "location": {"building": "North", "room": "101", "address": "1 Main"},
        },
    )

    service.schedule_session(
        tenant_id="tenant-a",
        session_id=hybrid.session_id,
        scheduled_by="author-1",
        timezone_name="UTC",
        start_at=datetime.now(timezone.utc) + timedelta(days=2),
        end_at=datetime.now(timezone.utc) + timedelta(days=2, hours=1),
    )
    updated = service.schedule_session(
        tenant_id="tenant-a",
        session_id=hybrid.session_id,
        scheduled_by="author-1",
        timezone_name="UTC",
        start_at=datetime.now(timezone.utc) + timedelta(days=3),
        end_at=datetime.now(timezone.utc) + timedelta(days=3, hours=1),
        reason="teacher conflict",
    )

    assert len(updated.reschedule_history) == 1
    assert service.repository.list_events(tenant_id="tenant-a")[-1].event_type == "session.rescheduled.v1"


def test_tenant_boundary_and_invalid_transition() -> None:
    service = _make_service()
    session = _create_online_session(service, tenant_id="tenant-a")

    with pytest.raises(TenantBoundaryError):
        service.get_session(tenant_id="tenant-b", session_id=session.session_id)

    with pytest.raises(SessionValidationError):
        service.start_session(tenant_id="tenant-a", session_id=session.session_id, actor_id="inst-1")


def test_api_routes_health_and_querying() -> None:
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    create_response = client.post(
        "/api/v2/sessions",
        json={
            "tenant_id": "tenant-api",
            "created_by": "author-2",
            "title": "API Session",
            "course_id": "course-api",
            "delivery_mode": "online",
            "delivery_metadata": {"online_join_url": "https://meet.example.com/api"},
            "cohort_ids": ["cohort-api"],
        },
    )
    assert create_response.status_code == 201

    list_response = client.get("/api/v2/sessions", params={"tenant_id": "tenant-api", "cohort_id": "cohort-api"})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert metrics_response.json()["service_up"] == 1
