import base64
import hashlib
import hmac
import json
import os
import sys
import time
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from fastapi.testclient import TestClient

os.environ["JWT_SHARED_SECRET"] = "test-secret"

_APP_ROOT = Path(__file__).resolve().parents[1] / "app"
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load_main(package_name: str):
    main_path = _APP_ROOT / "main.py"
    if package_name not in sys.modules:
        package = ModuleType(package_name)
        package.__path__ = [str(_APP_ROOT)]  # type: ignore[attr-defined]
        sys.modules[package_name] = package
    spec = spec_from_file_location(
        f"{package_name}.main",
        main_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {main_path}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_MAIN = _load_main("recommendation_service_app")
app = _MAIN.app


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


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_jwt()}"}


def test_generate_all_recommendation_types_and_bundle() -> None:
    learner_id = "learner-123"
    tenant_id = "tenant-123"

    personalized = client.post(
        "/recommendations/personalized-courses",
        headers=_headers(),
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
        headers=_headers(),
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
        headers=_headers(),
        json={
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "goal": "Data Engineer",
            "available_hours_per_week": 5,
            "mandatory_course_ids": ["course-foundations"],
        },
    )
    assert learning_path.status_code == 200
    assert len(learning_path.json()["items"]) == 2

    behavioral = client.post(
        "/recommendations/behavioral",
        headers=_headers(),
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

    bundle = client.get(f"/learners/{learner_id}/recommendations?tenant_id={tenant_id}", headers=_headers())
    assert bundle.status_code == 200
    body = bundle.json()["bundle"]
    assert len(body["personalized_courses"]) == 2
    assert len(body["skill_gaps"]) == 2
    assert len(body["learning_paths"]) == 2
    assert len(body["behavioral"]) >= 2


def test_bundle_is_tenant_scoped() -> None:
    learner_id = "learner-scope"

    client.post(
        "/recommendations/personalized-courses",
        headers=_headers(),
        json={
            "tenant_id": "tenant-a",
            "learner_id": learner_id,
            "target_skills": ["security"],
            "available_minutes_per_week": 120,
        },
    )

    wrong_tenant_bundle = client.get(f"/learners/{learner_id}/recommendations?tenant_id=tenant-b", headers=_headers())
    assert wrong_tenant_bundle.status_code == 200
    assert wrong_tenant_bundle.json()["bundle"]["personalized_courses"] == []


def test_generate_recommendations_from_learning_insight() -> None:
    response = client.post(
        "/recommendations/from-learning-insight",
        headers=_headers(),
        json={
            "tenant_id": "tenant-insight",
            "learner_id": "learner-insight",
            "risk_band": "high",
            "dropoff_rate": 0.62,
            "engagement_score": 36,
            "completion_rate": 42,
            "predicted_performance_score": 48,
        },
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(item["behavior_signal"] == "predicted_low_performance" for item in items)


def test_integrated_recommendations_use_analytics_skill_inference_and_progress() -> None:
    payload = {
        "tenant_id": "tenant-int",
        "learner_id": "learner-int",
        "goal": "Data Engineer",
        "target_skills": ["sql", "python", "orchestration"],
        "mandatory_course_ids": ["course-data-engineer-foundations"],
        "available_hours_per_week": 6,
        "analytics": {
            "completion_rate": 32,
            "average_engagement_score": 41,
            "average_sentiment": -0.1,
            "trend_direction": "down",
        },
        "skill_inference": [
            {"skill_id": "sql", "inferred_level": 0.25, "confidence": 0.9},
            {"skill_id": "python", "inferred_level": 0.52, "confidence": 0.7},
        ],
        "progress": {
            "completed_course_ids": ["course-data-engineer-sql-foundation-1"],
            "in_progress_course_ids": ["course-data-engineer-python-intermediate-2"],
            "learning_path_completion_rate": 18,
            "weekly_active_minutes": 95,
        },
    }
    response = client.post("/recommendations/integrated", headers=_headers(), json=payload)
    assert response.status_code == 200
    body = response.json()

    assert len(body["personalized_courses"]) >= 2
    assert all("data-engineer" in item["course_id"] for item in body["personalized_courses"])
    assert all(item["course_id"] not in payload["progress"]["in_progress_course_ids"] for item in body["personalized_courses"])
    assert all(item["course_id"] not in payload["progress"]["completed_course_ids"] for item in body["personalized_courses"])
    assert body["learning_paths"][0]["ordered_course_ids"][0] == "course-data-engineer-foundations"
    assert any(
        tag.startswith("trend:") for tag in body["learning_paths"][0]["rationale"]["tags"]
    )
