import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unittest

from src.models import ExpirationPolicy
from src.service import CertificateService


class CertificateServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = CertificateService()

    def test_issue_and_get_certificate(self) -> None:
        cert = self.service.issue_certificate(
            tenant_id="tenant-a",
            user_id="user-1",
            course_id="course-1",
            enrollment_id="enroll-1",
            metadata={"score": 96},
            artifact_uri="s3://certificates/tenant-a/cert-1.pdf",
        )

        fetched = self.service.get_certificate(tenant_id="tenant-a", certificate_id=cert.certificate_id)
        self.assertEqual(fetched["tenant_id"], "tenant-a")
        self.assertEqual(fetched["user_id"], "user-1")
        self.assertEqual(fetched["status"], "active")
        self.assertEqual(fetched["metadata"]["score"], 96)

    def test_validation_requires_matching_verification_code(self) -> None:
        cert = self.service.issue_certificate(
            tenant_id="tenant-a",
            user_id="user-2",
            course_id="course-2",
        )

        failed = self.service.validate_certificate(
            tenant_id="tenant-a",
            certificate_id=cert.certificate_id,
            verification_code="wrong-code",
        )
        self.assertFalse(failed["is_valid"])
        self.assertFalse(failed["is_verification_code_valid"])

        passed = self.service.validate_certificate(
            tenant_id="tenant-a",
            certificate_id=cert.certificate_id,
            verification_code=cert.verification_code,
        )
        self.assertTrue(passed["is_valid"])
        self.assertTrue(passed["is_verification_code_valid"])

    def test_expiration_management_marks_expired(self) -> None:
        cert = self.service.issue_certificate(
            tenant_id="tenant-a",
            user_id="user-3",
            course_id="course-3",
            expiration_policy=ExpirationPolicy(validity_days=1, never_expires=False),
        )

        expired_count = self.service.manage_expirations(
            tenant_id="tenant-a",
            now=cert.issued_at + timedelta(days=2),
        )
        self.assertEqual(expired_count, 1)

        result = self.service.validate_certificate(
            tenant_id="tenant-a",
            certificate_id=cert.certificate_id,
            at_time=cert.issued_at + timedelta(days=2),
        )
        self.assertEqual(result["status"], "expired")
        self.assertFalse(result["is_valid"])

    def test_list_filters_and_tenant_isolation(self) -> None:
        first = self.service.issue_certificate(
            tenant_id="tenant-a",
            user_id="user-1",
            course_id="course-a",
        )
        self.service.issue_certificate(
            tenant_id="tenant-a",
            user_id="user-1",
            course_id="course-b",
        )
        self.service.issue_certificate(
            tenant_id="tenant-b",
            user_id="user-1",
            course_id="course-a",
        )

        self.service.revoke_certificate(
            tenant_id="tenant-a",
            certificate_id=first.certificate_id,
            reason="policy-violation",
        )

        tenant_a_all = self.service.list_certificates(tenant_id="tenant-a")
        self.assertEqual(len(tenant_a_all), 2)

        tenant_a_revoked = self.service.list_certificates(tenant_id="tenant-a", status="revoked")
        self.assertEqual(len(tenant_a_revoked), 1)

        tenant_b_all = self.service.list_certificates(tenant_id="tenant-b")
        self.assertEqual(len(tenant_b_all), 1)

    def test_unique_user_course_constraint_per_tenant(self) -> None:
        self.service.issue_certificate(
            tenant_id="tenant-a",
            user_id="user-5",
            course_id="course-5",
        )

        with self.assertRaises(ValueError):
            self.service.issue_certificate(
                tenant_id="tenant-a",
                user_id="user-5",
                course_id="course-5",
            )

    def test_revoked_certificate_is_not_valid(self) -> None:
        cert = self.service.issue_certificate(
            tenant_id="tenant-a",
            user_id="user-6",
            course_id="course-6",
            expiration_policy=ExpirationPolicy(validity_days=30, never_expires=False),
        )

        self.service.revoke_certificate(
            tenant_id="tenant-a",
            certificate_id=cert.certificate_id,
            reason="manual-revocation",
        )

        result = self.service.validate_certificate(
            tenant_id="tenant-a",
            certificate_id=cert.certificate_id,
            verification_code=cert.verification_code,
            at_time=datetime.utcnow() + timedelta(days=1),
        )
        self.assertEqual(result["status"], "revoked")
        self.assertFalse(result["is_valid"])


if __name__ == "__main__":
    unittest.main()
