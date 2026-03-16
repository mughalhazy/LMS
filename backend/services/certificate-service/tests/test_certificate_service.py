import base64
import hashlib
import hmac
import json
import os
import time
import unittest

from fastapi.testclient import TestClient

from app.main import app


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _jwt(secret: str) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({"sub": "tester", "exp": time.time() + 3600}).encode())
    sig = _b64url(hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


class CertificateApiTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["JWT_SHARED_SECRET"] = "test-secret"
        self.token = _jwt("test-secret")
        self.client = TestClient(app)

    def _issue(self) -> dict:
        response = self.client.post(
            "/api/v1/certificates",
            headers={"Authorization": f"Bearer {self.token}", "X-Tenant-Id": "tenant-z"},
            json={
                "user_id": "user-1",
                "course_id": "course-1",
                "template_id": "tpl-main",
                "completion_ref": {
                    "source_event": "lms.progress.course_completed.v1",
                    "source_event_id": "evt-2",
                    "completed_at": "2026-01-01T00:00:00Z",
                },
                "issued_by": "system",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_issue_and_verify_and_revoke_flow(self) -> None:
        cert = self._issue()

        verify = self.client.get(f"/api/v1/certificates/verify/{cert['verification_code']}")
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.json()["is_valid"])

        revoke = self.client.post(
            f"/api/v1/certificates/{cert['certificate_id']}/revoke",
            headers={"Authorization": f"Bearer {self.token}", "X-Tenant-Id": "tenant-z"},
            json={"reason": "policy_violation", "revoked_by": "admin-1"},
        )
        self.assertEqual(revoke.status_code, 200)
        self.assertEqual(revoke.json()["status"], "revoked")

    def test_template_create_and_patch(self) -> None:
        create = self.client.post(
            "/api/v1/certificate-templates",
            headers={"Authorization": f"Bearer {self.token}", "X-Tenant-Id": "tenant-z"},
            json={"template_id": "tpl-v", "name": "Base", "body": "<html/>", "metadata": {"brand": "acme"}},
        )
        self.assertEqual(create.status_code, 200)
        self.assertEqual(create.json()["version"], 1)

        patch = self.client.patch(
            "/api/v1/certificate-templates/tpl-v",
            headers={"Authorization": f"Bearer {self.token}", "X-Tenant-Id": "tenant-z"},
            json={"name": "Base2"},
        )
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.json()["version"], 2)


if __name__ == "__main__":
    unittest.main()
