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
os.environ["TENANT_CAPABILITY_CONTEXT_JSON"] = json.dumps(
    {
        "tenant-a": {"plan_type": "pro", "addon_flags": ["ai_tutor_pack"]},
        "tenant-x": {"plan_type": "pro", "addon_flags": ["ai_tutor_pack"]},
        "tenant-ai": {"plan_type": "pro", "addon_flags": ["ai_tutor_pack"]},
    }
)

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


_MAIN = _load_main("ai_tutor_service_app")
app = _MAIN.app
service = _MAIN.service


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
        headers=_headers(),
        json={**base_payload, "concept": "Loop Invariants", "learner_goal": "debug loops"},
    )
    assert explanation.status_code == 200
    explanation_data = explanation.json()
    assert explanation_data["interaction_type"] == "explanation"
    assert "Python Foundations" in explanation_data["message"]

    question = client.post(
        "/ai-tutor/questions",
        headers=_headers(),
        json={**base_payload, "question": "How do loop invariants prevent bugs?"},
    )
    assert question.status_code == 200
    assert question.json()["session_id"] == explanation_data["session_id"]

    tutoring = client.post(
        "/ai-tutor/contextual-tutoring",
        headers=_headers(),
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
        headers=_headers(),
        json={
            **base_payload,
            "current_progress": 35,
            "time_available_minutes": 45,
        },
    )
    assert guidance.status_code == 200
    assert guidance.json()["interaction_type"] == "guidance"

    summary = client.get(f"/ai-tutor/sessions/{explanation_data['session_id']}?tenant_id=tenant-a", headers=_headers())
    assert summary.status_code == 200
    summary_json = summary.json()
    assert len(summary_json["interactions"]) == 4
    assert summary_json["context"]["course_id"] == "course-python"


def test_session_scoped_by_tenant() -> None:
    service._data_provider = StubProvider()
    response = client.post(
        "/ai-tutor/explanations",
        headers=_headers(),
        json={
            "tenant_id": "tenant-x",
            "learner_id": "learner-z",
            "context": {"course_id": "course-1"},
            "concept": "Functions",
        },
    )
    session_id = response.json()["session_id"]

    unauthorized = client.get(f"/ai-tutor/sessions/{session_id}?tenant_id=tenant-y", headers=_headers())
    assert unauthorized.status_code == 404


def test_learning_insight_guidance_endpoint() -> None:
    service._data_provider = StubProvider()
    response = client.post(
        "/ai-tutor/learning-insight-guidance",
        headers=_headers(),
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
