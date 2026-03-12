from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ai_tutor_capabilities_flow() -> None:
    base_payload = {
        "tenant_id": "tenant-a",
        "learner_id": "learner-1",
        "context": {
            "course_id": "course-python",
            "lesson_id": "lesson-loops",
            "skill_level": "beginner",
            "struggling_topics": ["loop invariants", "boundary conditions"],
        },
    }

    explanation = client.post(
        "/ai-tutor/explanations",
        json={**base_payload, "concept": "Loop Invariants", "learner_goal": "debug loops"},
    )
    assert explanation.status_code == 200
    explanation_data = explanation.json()
    assert explanation_data["interaction_type"] == "explanation"

    question = client.post(
        "/ai-tutor/questions",
        json={**base_payload, "question": "How do loop invariants prevent bugs?"},
    )
    assert question.status_code == 200
    assert question.json()["session_id"] == explanation_data["session_id"]

    tutoring = client.post(
        "/ai-tutor/contextual-tutoring",
        json={
            **base_payload,
            "activity_type": "coding-exercise",
            "learner_submission": "for i in range(n+1)",
            "expected_outcome": "iterate from 0 to n-1",
        },
    )
    assert tutoring.status_code == 200
    assert tutoring.json()["interaction_type"] == "contextual_tutoring"

    guidance = client.post(
        "/ai-tutor/guidance",
        json={
            **base_payload,
            "current_progress": 35,
            "time_available_minutes": 45,
        },
    )
    assert guidance.status_code == 200
    assert guidance.json()["interaction_type"] == "guidance"

    summary = client.get(
        f"/ai-tutor/sessions/{explanation_data['session_id']}?tenant_id=tenant-a"
    )
    assert summary.status_code == 200
    assert len(summary.json()["interactions"]) == 4


def test_session_scoped_by_tenant() -> None:
    response = client.post(
        "/ai-tutor/explanations",
        json={
            "tenant_id": "tenant-x",
            "learner_id": "learner-z",
            "context": {"course_id": "course-1"},
            "concept": "Functions",
        },
    )
    session_id = response.json()["session_id"]

    unauthorized = client.get(f"/ai-tutor/sessions/{session_id}?tenant_id=tenant-y")
    assert unauthorized.status_code == 404
