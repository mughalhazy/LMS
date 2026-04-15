from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_attempt_flow_answers_scoring_and_history() -> None:
    start_payload = {
        "tenant_id": "tenant-a",
        "learner_id": "learner-1",
        "assessment_id": "assessment-1",
        "enrollment_id": "enr-1",
        "course_id": "course-1",
        "started_by": "learner-1",
    }

    first_attempt_response = client.post("/attempts", json=start_payload)
    assert first_attempt_response.status_code == 200
    first_attempt = first_attempt_response.json()
    assert first_attempt["attempt_number"] == 1
    assert first_attempt["status"] == "in_progress"

    first_attempt_id = first_attempt["attempt_id"]

    answer_response = client.post(
        f"/attempts/{first_attempt_id}/answers",
        json={
            "tenant_id": "tenant-a",
            "answers": [
                {"question_id": "q-1", "response": "A", "is_final": True},
                {"question_id": "q-2", "response": ["B", "C"], "is_final": False},
            ],
        },
    )
    assert answer_response.status_code == 200
    answered_attempt = answer_response.json()
    assert answered_attempt["status"] == "submitted"
    assert len(answered_attempt["answers"]) == 2

    score_response = client.post(
        f"/attempts/{first_attempt_id}/score",
        json={
            "tenant_id": "tenant-a",
            "scored_by": "instructor-1",
            "max_score": 100,
            "awarded_score": 82,
            "passing_score": 70,
            "feedback": "Good work",
        },
    )
    assert score_response.status_code == 200
    scored_attempt = score_response.json()
    assert scored_attempt["status"] == "scored"
    assert scored_attempt["passed"] is True
    assert scored_attempt["awarded_score"] == 82

    second_attempt_response = client.post("/attempts", json=start_payload)
    assert second_attempt_response.status_code == 200
    second_attempt = second_attempt_response.json()
    assert second_attempt["attempt_number"] == 2

    history_response = client.get(
        "/attempts/history",
        params={
            "tenant_id": "tenant-a",
            "learner_id": "learner-1",
            "assessment_id": "assessment-1",
        },
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history["attempts"]) == 2
    assert history["attempts"][0]["attempt_id"] == first_attempt_id


def test_tenant_isolation_and_validation() -> None:
    created = client.post(
        "/attempts",
        json={
            "tenant_id": "tenant-scope-a",
            "learner_id": "learner-2",
            "assessment_id": "assessment-scope",
            "started_by": "learner-2",
        },
    ).json()

    wrong_tenant_read = client.get(
        f"/attempts/{created['attempt_id']}", params={"tenant_id": "tenant-scope-b"}
    )
    assert wrong_tenant_read.status_code == 404

    invalid_score = client.post(
        f"/attempts/{created['attempt_id']}/score",
        json={
            "tenant_id": "tenant-scope-a",
            "scored_by": "instructor",
            "max_score": 50,
            "awarded_score": 55,
            "passing_score": 30,
        },
    )
    assert invalid_score.status_code == 422
