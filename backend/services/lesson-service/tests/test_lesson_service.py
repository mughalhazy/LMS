import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import base64
import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient

os.environ["JWT_SHARED_SECRET"] = "test-secret"

from app.main import app, _store  # noqa: E402


client = TestClient(app)


def _jwt(roles=None):
    roles = roles or ["admin"]
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": "tester", "roles": roles, "exp": time.time() + 3600}

    def enc(value):
        raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    header_b64 = enc(header)
    payload_b64 = enc(payload)
    signed = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(os.environ["JWT_SHARED_SECRET"].encode("utf-8"), signed, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def _headers(tenant_id="tenant-a"):
    return {
        "Authorization": f"Bearer {_jwt()}",
        "X-Tenant-Id": tenant_id,
        "X-Actor-Id": "author-1",
    }


def setup_function():
    _store._lessons.clear()
    _store.audit_log.clear()
    _store.events.clear()


def test_lesson_crud_and_lifecycle_flow():
    create = client.post(
        "/api/v1/lessons",
        headers=_headers(),
        json={
            "course_id": "course-1",
            "title": "Intro",
            "description": "Welcome",
            "lesson_type": "video",
            "order_index": 1,
        },
    )
    assert create.status_code == 201
    lesson_id = create.json()["lesson_id"]

    update = client.patch(
        f"/api/v1/lessons/{lesson_id}",
        headers=_headers(),
        json={"title": "Intro updated", "metadata": {"difficulty": "easy"}},
    )
    assert update.status_code == 200
    assert update.json()["title"] == "Intro updated"

    publish = client.post(f"/api/v1/lessons/{lesson_id}:publish", headers=_headers())
    assert publish.status_code == 200
    assert publish.json()["status"] == "published"

    archive = client.post(f"/api/v1/lessons/{lesson_id}:archive", headers=_headers())
    assert archive.status_code == 200
    assert archive.json()["status"] == "archived"

    readonly = client.patch(f"/api/v1/lessons/{lesson_id}", headers=_headers(), json={"title": "blocked"})
    assert readonly.status_code == 409


def test_course_linkage_tenant_isolation_and_hooks():
    for tenant in ["tenant-a", "tenant-b"]:
        for i in [1, 2]:
            client.post(
                "/api/v1/lessons",
                headers=_headers(tenant),
                json={"course_id": f"course-{i}", "title": f"L{i}", "lesson_type": "text"},
            )

    tenant_a_course_1 = client.get("/api/v1/lessons?course_id=course-1", headers=_headers("tenant-a"))
    assert tenant_a_course_1.status_code == 200
    data = tenant_a_course_1.json()["lessons"]
    assert len(data) == 1
    lesson_id = data[0]["lesson_id"]

    hook = client.post(
        f"/api/v1/lessons/{lesson_id}:progression-hooks",
        headers=_headers("tenant-a"),
        json={"hook_type": "lesson_viewed", "payload": {"learner_id": "u-1"}},
    )
    assert hook.status_code == 202

    # ensure outbox and audit were populated for lifecycle + hooks
    assert any(evt.event_type == "lesson_progression_hook_triggered" for evt in _store.events)
    assert any(record.action.value == "progression_hook" for record in _store.audit_log)


def test_health_and_metrics():
    health = client.get("/health")
    assert health.status_code == 200
    metrics = client.get("/metrics", headers={"Authorization": f"Bearer {_jwt()}"})
    assert metrics.status_code == 200
    assert "events_emitted" in metrics.json()
