from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_course_lifecycle_with_versioning_and_publish() -> None:
    create_payload = {
        "tenant_id": "tenant-a",
        "created_by": "user-1",
        "title": "Intro to LMS",
        "description": "Draft",
        "category_id": "cat-1",
        "language": "en",
        "delivery_mode": "self-paced",
        "duration_minutes": 60,
        "tags": ["intro"],
        "objectives": ["objective-1"],
        "metadata": {"level": "beginner"},
    }

    create_response = client.post("/courses", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "draft"
    assert created["version"] == 1

    course_id = created["course_id"]
    update_response = client.patch(
        f"/courses/{course_id}",
        json={
            "tenant_id": "tenant-a",
            "updated_by": "user-2",
            "description": "Updated description",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["description"] == "Updated description"

    version_response = client.post(
        f"/courses/{course_id}/versions",
        json={
            "tenant_id": "tenant-a",
            "based_on_version": 1,
            "created_by": "user-3",
            "change_summary": "Prepare v2",
            "metadata_overrides": {"level": "intermediate"},
        },
    )
    assert version_response.status_code == 200
    assert version_response.json()["new_version"] == 2

    publish_response = client.post(
        f"/courses/{course_id}/publish",
        json={"tenant_id": "tenant-a", "requested_by": "user-4"},
    )
    assert publish_response.status_code == 200
    published = publish_response.json()
    assert published["status"] == "published"
    assert published["published_version"] == 2


def test_tenant_scoping_enforced() -> None:
    create_response = client.post(
        "/courses",
        json={"tenant_id": "tenant-scope", "created_by": "owner", "title": "Scoped Course"},
    )
    course_id = create_response.json()["course_id"]

    unauthorized_response = client.get(f"/courses/{course_id}?tenant_id=wrong-tenant")
    assert unauthorized_response.status_code == 404


def test_delete_course_endpoint_matches_core_rest_api() -> None:
    create_response = client.post(
        "/courses",
        json={"tenant_id": "tenant-del", "created_by": "owner", "title": "Disposable"},
    )
    course_id = create_response.json()["course_id"]

    delete_response = client.delete(f"/courses/{course_id}?tenant_id=tenant-del")
    assert delete_response.status_code == 204

    not_found_response = client.get(f"/courses/{course_id}?tenant_id=tenant-del")
    assert not_found_response.status_code == 404
