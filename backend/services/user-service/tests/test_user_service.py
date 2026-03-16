import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app, service

client = TestClient(app)


def headers(tenant_id: str = "tenant-1") -> dict[str, str]:
    return {"X-Tenant-Id": tenant_id}


def setup_function() -> None:
    service.user_store._items.clear()  # type: ignore[attr-defined]
    service.audit_store._items.clear()  # type: ignore[attr-defined]
    service.event_publisher.events.clear()  # type: ignore[attr-defined]
    service.observability.counters.clear()  # type: ignore[attr-defined]


def create_user(tenant_id: str = "tenant-1", user_id: str = "rails-user-1") -> str:
    response = client.post(
        "/api/v1/users",
        headers=headers(tenant_id),
        json={
            "tenant_id": tenant_id,
            "actor_id": "admin-1",
            "user_id": user_id,
            "email": "ada@example.com",
            "username": "ada",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "department": "Engineering",
        },
    )
    assert response.status_code == 201
    return response.json()["user"]["user_id"]


def test_user_crud_status_role_and_events() -> None:
    user_id = create_user()

    updated = client.put(
        f"/api/v1/users/{user_id}?tenant_id=tenant-1",
        headers=headers(),
        json={"tenant_id": "tenant-1", "actor_id": "admin-1", "title": "Principal Engineer"},
    )
    assert updated.status_code == 200
    assert updated.json()["user"]["profile"]["title"] == "Principal Engineer"

    status = client.patch(
        f"/api/v1/users/{user_id}/status?tenant_id=tenant-1",
        headers=headers(),
        json={"tenant_id": "tenant-1", "actor_id": "admin-1", "status": "active", "reason": "verified"},
    )
    assert status.status_code == 200
    assert status.json()["user"]["status"] == "active"

    link = client.post(
        f"/api/v1/users/{user_id}/role-links?tenant_id=tenant-1",
        headers=headers(),
        json={"tenant_id": "tenant-1", "actor_id": "admin-1", "role_id": "role-instructor"},
    )
    assert link.status_code == 200
    assert len(link.json()["user"]["role_links"]) == 1

    audit = client.get(f"/api/v1/users/{user_id}/audit?tenant_id=tenant-1", headers=headers())
    assert audit.status_code == 200
    assert len(audit.json()["entries"]) >= 3

    events = client.get("/api/v1/events/users?tenant_id=tenant-1", headers=headers())
    assert events.status_code == 200
    event_types = [item["event_type"] for item in events.json()["events"]]
    assert "lms.user.created" in event_types
    assert "lms.user.profile.updated" in event_types

    deleted = client.delete(f"/api/v1/users/{user_id}?tenant_id=tenant-1&actor_id=admin-1", headers=headers())
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/users/{user_id}?tenant_id=tenant-1", headers=headers())
    assert missing.status_code == 404


def test_tenant_safety_and_health_metrics() -> None:
    user_id = create_user(tenant_id="tenant-a", user_id="rails-user-a")

    denied = client.get(f"/api/v1/users/{user_id}?tenant_id=tenant-a", headers=headers("tenant-b"))
    assert denied.status_code == 403

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["service"] == "user-service"
    assert metrics.json()["counters"].get("user.create", 0) >= 1
