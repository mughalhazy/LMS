import base64
import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient

os.environ["JWT_SHARED_SECRET"] = "test-secret"

from app.main import app, service

client = TestClient(app)


def _jwt() -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": "test-user", "exp": time.time() + 3600}

    def _b64(data: dict) -> str:
        raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    h = _b64(header)
    p = _b64(payload)
    sig = hmac.new(b"test-secret", f"{h}.{p}".encode("utf-8"), hashlib.sha256).digest()
    s = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{h}.{p}.{s}"


def _headers(tenant_id: str = "tenant-a") -> dict[str, str]:
    return {"X-Tenant-Id": tenant_id, "Authorization": f"Bearer {_jwt()}"}


def test_course_lifecycle_and_linkage_flows() -> None:
    create_response = client.post(
        "/api/v1/courses",
        headers=_headers(),
        json={
            "tenant_id": "tenant-a",
            "created_by": "user-1",
            "title": "Engineering Onboarding",
            "description": "v1",
            "course_code": "ENG-ONB-101",
            "language_code": "en",
            "metadata": {"duration_minutes": 90, "tags": ["eng"]},
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["status"] == "draft"
    assert created["publish_status"] == "unpublished"

    course_id = created["course_id"]

    update_response = client.patch(
        f"/api/v1/courses/{course_id}",
        headers=_headers(),
        json={"tenant_id": "tenant-a", "updated_by": "user-2", "description": "updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["description"] == "updated"

    links_response = client.put(
        f"/api/v1/courses/{course_id}/program-links",
        headers=_headers(),
        json={
            "tenant_id": "tenant-a",
            "updated_by": "user-2",
            "program_links": [{"program_id": "prog-1", "is_primary": True}],
        },
    )
    assert links_response.status_code == 200
    assert links_response.json()["data"][0]["program_id"] == "prog-1"

    session_links_response = client.put(
        f"/api/v1/courses/{course_id}/session-links",
        headers=_headers(),
        json={
            "tenant_id": "tenant-a",
            "updated_by": "user-2",
            "session_links": [{"session_id": "sess-1", "delivery_role": "default"}],
        },
    )
    assert session_links_response.status_code == 200

    publish_response = client.post(
        f"/api/v1/courses/{course_id}/publish",
        headers=_headers(),
        json={"tenant_id": "tenant-a", "requested_by": "publisher-1"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["status"] == "published"

    archive_response = client.post(
        f"/api/v1/courses/{course_id}/archive",
        headers=_headers(),
        json={"tenant_id": "tenant-a", "requested_by": "admin-1"},
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["status"] == "archived"


def test_tenant_header_context_is_enforced() -> None:
    create_response = client.post(
        "/api/v1/courses",
        headers=_headers("tenant-header"),
        json={"tenant_id": "tenant-body", "created_by": "user-1", "title": "Mismatch"},
    )
    assert create_response.status_code == 400


def test_metrics_endpoint_includes_observability_counters() -> None:
    metrics_response = client.get("/metrics", headers=_headers())
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert "courses_created_total" in metrics
    assert metrics["service_up"] == 1


def test_events_are_published_for_lifecycle_changes() -> None:
    before_count = len(service.event_publisher.list_events())
    response = client.post(
        "/api/v1/courses",
        headers=_headers("tenant-events"),
        json={"tenant_id": "tenant-events", "created_by": "user-1", "title": "Event Course"},
    )
    assert response.status_code == 201
    after_count = len(service.event_publisher.list_events())
    assert after_count == before_count + 1
    assert service.event_publisher.list_events()[-1].event_name == "course.lifecycle.created.v1"


def test_workforce_mandatory_course_requires_policy_and_updates_metrics() -> None:
    bad_response = client.post(
        "/api/v1/courses",
        headers=_headers("tenant-workforce"),
        json={
            "tenant_id": "tenant-workforce",
            "created_by": "hr-1",
            "title": "Annual Safety",
            "metadata": {"audience": "workforce", "mandatory_training": True},
        },
    )
    assert bad_response.status_code == 422

    ok_response = client.post(
        "/api/v1/courses",
        headers=_headers("tenant-workforce"),
        json={
            "tenant_id": "tenant-workforce",
            "created_by": "hr-1",
            "title": "Annual Safety",
            "metadata": {
                "audience": "workforce",
                "mandatory_training": True,
                "compliance_policy_id": "policy-safety-annual",
                "manager_visibility_enabled": True,
            },
        },
    )
    assert ok_response.status_code == 201
    metrics_response = client.get("/metrics", headers=_headers("tenant-workforce"))
    assert metrics_response.status_code == 200
    assert metrics_response.json()["workforce_mandatory_courses_total"] >= 1
