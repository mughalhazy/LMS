from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_badge_definition_and_duplicate_code_guard() -> None:
    payload = {
        "tenant_id": "t1",
        "code": "COURSE-EXCELLENCE",
        "title": "Course Excellence",
        "description": "Awarded for completing all assessments with 90%+ score.",
        "criteria": {"min_score": 90, "completion_required": True},
    }
    created = client.post("/badges", json=payload)
    assert created.status_code == 201

    duplicate = client.post("/badges", json=payload)
    assert duplicate.status_code == 409


def test_badge_issuance_and_learner_history() -> None:
    badge = client.post(
        "/badges",
        json={
            "tenant_id": "t2",
            "code": "LEARNING-STREAK",
            "title": "Learning Streak",
            "description": "Seven days of continuous learning.",
            "criteria": {"days": 7},
        },
    ).json()

    issuance = client.post(
        "/badge-issuances",
        json={
            "tenant_id": "t2",
            "badge_id": badge["badge_id"],
            "learner_id": "u-101",
            "issued_by": "system",
            "evidence": {"streak_days": 7},
        },
    )
    assert issuance.status_code == 201

    duplicate_active = client.post(
        "/badge-issuances",
        json={
            "tenant_id": "t2",
            "badge_id": badge["badge_id"],
            "learner_id": "u-101",
            "issued_by": "system",
            "evidence": {"streak_days": 8},
        },
    )
    assert duplicate_active.status_code == 409

    history = client.get("/learners/u-101/badges", params={"tenant_id": "t2"})
    assert history.status_code == 200
    body = history.json()
    assert body["learner_id"] == "u-101"
    assert len(body["badges"]) == 1
    assert body["badges"][0]["badge"]["code"] == "LEARNING-STREAK"


def test_revocation_allows_reissuance() -> None:
    badge = client.post(
        "/badges",
        json={
            "tenant_id": "t3",
            "code": "SECURITY-CHAMPION",
            "title": "Security Champion",
            "description": "Completed secure coding learning path.",
            "criteria": {"path_id": "lp-secure-coding"},
        },
    ).json()

    issuance = client.post(
        "/badge-issuances",
        json={
            "tenant_id": "t3",
            "badge_id": badge["badge_id"],
            "learner_id": "u-205",
            "issued_by": "manager-1",
            "evidence": {"path_completed": True},
        },
    ).json()

    revoked = client.patch(
        f"/badge-issuances/{issuance['issuance_id']}",
        params={"tenant_id": "t3"},
        json={"status": "revoked", "revoke_reason": "Issued by mistake"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    reissued = client.post(
        "/badge-issuances",
        json={
            "tenant_id": "t3",
            "badge_id": badge["badge_id"],
            "learner_id": "u-205",
            "issued_by": "manager-2",
            "evidence": {"manual_review": "approved"},
        },
    )
    assert reissued.status_code == 201
