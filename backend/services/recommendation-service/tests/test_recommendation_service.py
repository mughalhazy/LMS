from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_all_recommendation_types_and_bundle() -> None:
    learner_id = "learner-123"
    tenant_id = "tenant-123"

    personalized = client.post(
        "/recommendations/personalized-courses",
        json={
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "target_skills": ["python", "data-modeling"],
            "preferred_modalities": ["video", "lab"],
            "available_minutes_per_week": 240,
        },
    )
    assert personalized.status_code == 200
    assert len(personalized.json()["items"]) == 2

    skill_gap = client.post(
        "/recommendations/skill-gaps",
        json={
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "required_skills": ["python", "sql"],
            "current_skill_levels": {"python": 0.3, "sql": 0.2},
            "target_skill_levels": {"python": 0.8, "sql": 0.7},
        },
    )
    assert skill_gap.status_code == 200
    assert skill_gap.json()["items"][0]["severity"] in {"critical", "moderate", "minor"}

    learning_path = client.post(
        "/recommendations/learning-paths",
        json={
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "goal": "Data Engineer",
            "available_hours_per_week": 5,
            "mandatory_course_ids": ["course-foundations"],
        },
    )
    assert learning_path.status_code == 200
    assert len(learning_path.json()["items"]) == 3

    behavioral = client.post(
        "/recommendations/behavioral",
        json={
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "activity_streak_days": 1,
            "average_session_minutes": 8,
            "dropoff_rate": 0.55,
        },
    )
    assert behavioral.status_code == 200
    assert len(behavioral.json()["items"]) >= 2

    bundle = client.get(f"/learners/{learner_id}/recommendations?tenant_id={tenant_id}")
    assert bundle.status_code == 200
    body = bundle.json()["bundle"]
    assert len(body["personalized_courses"]) == 2
    assert len(body["skill_gaps"]) == 2
    assert len(body["learning_paths"]) == 3
    assert len(body["behavioral"]) >= 2


def test_bundle_is_tenant_scoped() -> None:
    learner_id = "learner-scope"

    client.post(
        "/recommendations/personalized-courses",
        json={
            "tenant_id": "tenant-a",
            "learner_id": learner_id,
            "target_skills": ["security"],
            "available_minutes_per_week": 120,
        },
    )

    wrong_tenant_bundle = client.get(f"/learners/{learner_id}/recommendations?tenant_id=tenant-b")
    assert wrong_tenant_bundle.status_code == 200
    assert wrong_tenant_bundle.json()["bundle"]["personalized_courses"] == []
