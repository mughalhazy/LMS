from fastapi.testclient import TestClient

from app.main import app, service


client = TestClient(app)


class StubProvider:
    def get_course(self, tenant_id: str, course_id: str) -> dict:
        return {"course_id": course_id, "title": "Python Foundations"}

    def get_course_progress(self, tenant_id: str, learner_id: str, course_id: str) -> dict:
        return {"course_id": course_id, "progress_percentage": 72.5}

    def get_analytics(self, tenant_id: str, learner_id: str, course_id: str) -> dict:
        return {"learner_id": learner_id, "trend_direction": "declining"}


def test_ai_tutor_capabilities_flow() -> None:
    service._data_provider = StubProvider()
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
    assert "Python Foundations" in explanation_data["message"]

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

    summary = client.get(f"/ai-tutor/sessions/{explanation_data['session_id']}?tenant_id=tenant-a")
    assert summary.status_code == 200
    summary_json = summary.json()
    assert len(summary_json["interactions"]) == 4
    assert summary_json["context"]["course_data"]["title"] == "Python Foundations"
    assert summary_json["context"]["progress_data"]["progress_percentage"] == 72.5
    assert summary_json["context"]["analytics_data"]["trend_direction"] == "declining"


def test_session_scoped_by_tenant() -> None:
    service._data_provider = StubProvider()
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


def test_learning_insight_guidance_endpoint() -> None:
    service._data_provider = StubProvider()
    response = client.post(
        "/ai-tutor/learning-insight-guidance",
        json={
            "tenant_id": "tenant-ai",
            "learner_id": "learner-ai",
            "context": {
                "course_id": "course-risk",
                "lesson_id": "lesson-1",
            },
            "dropout_risk_score": 78,
            "engagement_risk_score": 66,
            "predicted_performance_score": 51,
            "risk_band": "high",
            "suggested_focus": "exam-readiness",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["interaction_type"] == "guidance"
    assert "risk is high" in body["message"]
