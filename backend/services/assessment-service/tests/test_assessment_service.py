from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SERVICE_ROOT))
sys.modules.pop("app", None)

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_assessment_crud_lifecycle_attempt_submission_and_grade_flow() -> None:
    headers = {"X-Tenant-Id": "tenant-a"}

    create_response = client.post(
        "/api/v1/assessments",
        headers=headers,
        json={
            "course_id": "course-1",
            "lesson_id": "lesson-1",
            "title": "Quiz 1",
            "description": "intro quiz",
            "assessment_type": "quiz",
            "max_score": 100,
            "passing_score": 60,
            "time_limit_minutes": 30,
            "question_count": 10,
            "actor_id": "author-1",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "draft"

    assessment_id = created["assessment_id"]

    publish_response = client.post(
        f"/api/v1/assessments/{assessment_id}/publish",
        headers=headers,
        params={"actor_id": "author-1"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    attempt_response = client.post(
        f"/api/v1/assessments/{assessment_id}/attempts",
        headers=headers,
        json={"learner_id": "learner-1"},
    )
    assert attempt_response.status_code == 200
    attempt = attempt_response.json()
    assert attempt["status"] == "started"

    attempt_id = attempt["attempt_id"]

    submission_response = client.post(
        f"/api/v1/attempts/{attempt_id}/submissions",
        headers=headers,
        json={
            "submitted_by": "learner-1",
            "payload": {"answers": [{"question_id": "q-1", "value": "A"}]},
        },
    )
    assert submission_response.status_code == 200

    grade_response = client.post(
        f"/api/v1/attempts/{attempt_id}/grade",
        headers=headers,
        json={"grading_result_id": "grade-123", "actor_id": "grader-1"},
    )
    assert grade_response.status_code == 200
    graded = grade_response.json()
    assert graded["status"] == "graded"
    assert graded["grading_result_id"] == "grade-123"

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    counters = metrics_response.json()["counters"]
    assert counters["assessments_created"] >= 1
    assert counters["attempts_graded"] >= 1


def test_tenant_boundary_integrity_and_validation() -> None:
    tenant_a = {"X-Tenant-Id": "tenant-boundary-a"}
    tenant_b = {"X-Tenant-Id": "tenant-boundary-b"}

    create_response = client.post(
        "/api/v1/assessments",
        headers=tenant_a,
        json={
            "course_id": "course-boundary",
            "title": "Boundary exam",
            "assessment_type": "exam",
            "max_score": 50,
            "passing_score": 30,
            "question_count": 5,
            "actor_id": "author-1",
        },
    )
    assessment_id = create_response.json()["assessment_id"]

    wrong_tenant_get = client.get(f"/api/v1/assessments/{assessment_id}", headers=tenant_b)
    assert wrong_tenant_get.status_code == 404

    invalid_update = client.patch(
        f"/api/v1/assessments/{assessment_id}",
        headers=tenant_a,
        json={"max_score": 20, "passing_score": 25, "actor_id": "author-1"},
    )
    assert invalid_update.status_code == 422

    missing_tenant = client.get("/api/v1/assessments")
    assert missing_tenant.status_code == 400
