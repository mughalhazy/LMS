import base64
import hashlib
import hmac
import json
import os
import time
import unittest
from fastapi.testclient import TestClient

from app.main import AUDIT_LOGGER, EVENT_PUBLISHER, OBS_HOOKS, app


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _jwt(secret: str) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({"sub": "tester", "exp": time.time() + 3600}).encode())
    sig = _b64url(hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


class AuditAndEventsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = "test-secret"
        os.environ["JWT_SHARED_SECRET"] = self.secret
        self.client = TestClient(app)

    def test_issue_certificate_audits_and_publishes_event(self) -> None:
        token = _jwt(self.secret)
        response = self.client.post(
            "/api/v1/certificates",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-Id": "tenant-a"},
            json={
                "user_id": "user-1",
                "course_id": "course-1",
                "template_id": "tpl-1",
                "completion_ref": {
                    "source_event": "lms.progress.course_completed.v1",
                    "source_event_id": "evt-1",
                    "completed_at": "2026-01-01T00:00:00Z",
                },
                "issued_by": "system",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AUDIT_LOGGER.list_events()[-1].event_type, "certificate.issued")
        self.assertEqual(EVENT_PUBLISHER.published[-1]["event_name"], "lms.certificate.issued.v1")
        self.assertGreaterEqual(OBS_HOOKS.counters.get("certificate_issued_total", 0), 1)


if __name__ == "__main__":
    unittest.main()
