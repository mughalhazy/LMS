from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(tenant_id: str = "tenant-1") -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id}


def test_cohort_batch_and_membership_flow() -> None:
    cohort_response = client.post(
        "/api/v1/cohorts",
        headers=_headers(),
        json={
            "name": "Grade 10 - Section A",
            "code": "G10-A",
            "kind": "formal_cohort",
            "program_id": "program-1",
            "created_by": "admin-1",
            "schedule": {"timezone": "UTC"},
        },
    )
    assert cohort_response.status_code == 201
    cohort = cohort_response.json()
    assert cohort["kind"] == "formal_cohort"

    batch_response = client.post(
        "/api/v1/batches",
        headers=_headers(),
        json={
            "name": "Data Science Academy Batch 2026",
            "code": "DSA-2026",
            "kind": "formal_cohort",
            "created_by": "academy-admin",
            "schedule": {"timezone": "UTC"},
        },
    )
    assert batch_response.status_code == 201
    batch = batch_response.json()
    assert batch["kind"] == "academy_batch"

    link_response = client.post(
        f"/api/v1/cohorts/{cohort['cohort_id']}/program-link",
        headers=_headers(),
        json={"program_id": "program-2", "linked_by": "admin-1"},
    )
    assert link_response.status_code == 200
    assert link_response.json()["program_id"] == "program-2"

    membership_response = client.post(
        f"/api/v1/cohorts/{cohort['cohort_id']}/memberships",
        headers=_headers(),
        json={"user_id": "learner-1", "role": "student", "added_by": "admin-1"},
    )
    assert membership_response.status_code == 201
    membership = membership_response.json()

    read_response = client.get(f"/api/v1/cohorts/{cohort['cohort_id']}", headers=_headers())
    assert read_response.status_code == 200
    payload = read_response.json()
    assert payload["cohort"]["cohort_id"] == cohort["cohort_id"]
    assert payload["memberships"][0]["membership_id"] == membership["membership_id"]


def test_tenant_isolation_and_metrics() -> None:
    created = client.post(
        "/api/v1/cohorts",
        headers=_headers("tenant-a"),
        json={
            "name": "Tutor Group Blue",
            "code": "TG-BLUE",
            "kind": "tutor_group",
            "created_by": "teacher-1",
            "schedule": {"timezone": "UTC"},
        },
    ).json()

    wrong_tenant = client.get(f"/api/v1/cohorts/{created['cohort_id']}", headers=_headers("tenant-b"))
    assert wrong_tenant.status_code == 404

    update_response = client.patch(
        f"/api/v1/cohorts/{created['cohort_id']}",
        headers=_headers("tenant-a"),
        json={"status": "active", "updated_by": "teacher-1"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "active"

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert metrics_response.json()["service"] == "cohort-service"
