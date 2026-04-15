from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .models import Certificate, ExpirationPolicy


class CertificateService:
    """Tenant-scoped certificate issuance and validation service."""

    def __init__(self) -> None:
        self._certificates_by_tenant: Dict[str, Dict[str, Certificate]] = {}
        self._certificates_by_tenant_user_course: Dict[str, Dict[tuple[str, str], str]] = {}

    def issue_certificate(
        self,
        *,
        tenant_id: str,
        user_id: str,
        course_id: str,
        enrollment_id: Optional[str] = None,
        expiration_policy: Optional[ExpirationPolicy] = None,
        metadata: Optional[Dict[str, Any]] = None,
        artifact_uri: Optional[str] = None,
    ) -> Certificate:
        tenant_bucket = self._certificates_by_tenant.setdefault(tenant_id, {})
        unique_index = self._certificates_by_tenant_user_course.setdefault(tenant_id, {})
        key = (user_id, course_id)

        if key in unique_index:
            existing_id = unique_index[key]
            existing = tenant_bucket[existing_id]
            if existing.status != "revoked":
                raise ValueError("Certificate already exists for user and course in this tenant")

        now = datetime.utcnow()
        policy = expiration_policy or ExpirationPolicy(never_expires=True)
        expires_at = None
        if not policy.never_expires and policy.validity_days is not None:
            expires_at = now + timedelta(days=policy.validity_days)

        certificate = Certificate(
            certificate_id=str(uuid4()),
            verification_code=uuid4().hex,
            tenant_id=tenant_id,
            user_id=user_id,
            course_id=course_id,
            enrollment_id=enrollment_id,
            issued_at=now,
            expires_at=expires_at,
            status="active",
            metadata=metadata or {},
            artifact_uri=artifact_uri,
        )

        tenant_bucket[certificate.certificate_id] = certificate
        unique_index[key] = certificate.certificate_id
        return certificate

    def validate_certificate(
        self,
        *,
        tenant_id: str,
        certificate_id: str,
        verification_code: Optional[str] = None,
        at_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        certificate = self._require_certificate(tenant_id=tenant_id, certificate_id=certificate_id)
        self._refresh_expiration(tenant_id=tenant_id, certificate_id=certificate_id, now=at_time)

        is_code_valid = verification_code is None or verification_code == certificate.verification_code
        is_active = certificate.status == "active"
        is_valid = bool(is_code_valid and is_active)

        return {
            "certificate_id": certificate.certificate_id,
            "tenant_id": certificate.tenant_id,
            "user_id": certificate.user_id,
            "course_id": certificate.course_id,
            "status": certificate.status,
            "issued_at": certificate.issued_at,
            "expires_at": certificate.expires_at,
            "is_verification_code_valid": is_code_valid,
            "is_valid": is_valid,
        }

    def revoke_certificate(
        self,
        *,
        tenant_id: str,
        certificate_id: str,
        reason: str,
    ) -> Certificate:
        certificate = self._require_certificate(tenant_id=tenant_id, certificate_id=certificate_id)
        certificate.status = "revoked"
        certificate.revoked_at = datetime.utcnow()
        certificate.revocation_reason = reason
        return certificate

    def get_certificate(self, *, tenant_id: str, certificate_id: str) -> Dict[str, Any]:
        certificate = self._require_certificate(tenant_id=tenant_id, certificate_id=certificate_id)
        self._refresh_expiration(tenant_id=tenant_id, certificate_id=certificate_id)
        return asdict(certificate)

    def list_certificates(
        self,
        *,
        tenant_id: str,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        tenant_bucket = self._certificates_by_tenant.get(tenant_id, {})
        results: List[Dict[str, Any]] = []

        for certificate in tenant_bucket.values():
            self._refresh_expiration(tenant_id=tenant_id, certificate_id=certificate.certificate_id)

            if user_id and certificate.user_id != user_id:
                continue
            if course_id and certificate.course_id != course_id:
                continue
            if status and certificate.status != status:
                continue
            results.append(asdict(certificate))

        results.sort(key=lambda item: item["issued_at"], reverse=True)
        return results

    def manage_expirations(self, *, tenant_id: str, now: Optional[datetime] = None) -> int:
        tenant_bucket = self._certificates_by_tenant.get(tenant_id, {})
        expired_count = 0

        for certificate_id in tenant_bucket:
            before = tenant_bucket[certificate_id].status
            self._refresh_expiration(tenant_id=tenant_id, certificate_id=certificate_id, now=now)
            after = tenant_bucket[certificate_id].status
            if before != "expired" and after == "expired":
                expired_count += 1

        return expired_count

    def _refresh_expiration(
        self,
        *,
        tenant_id: str,
        certificate_id: str,
        now: Optional[datetime] = None,
    ) -> None:
        certificate = self._require_certificate(tenant_id=tenant_id, certificate_id=certificate_id)
        effective_now = now or datetime.utcnow()

        if certificate.status == "revoked":
            return

        if certificate.expires_at is not None and effective_now >= certificate.expires_at:
            certificate.status = "expired"
        elif certificate.status == "expired" and (
            certificate.expires_at is None or effective_now < certificate.expires_at
        ):
            certificate.status = "active"

    def _require_certificate(self, *, tenant_id: str, certificate_id: str) -> Certificate:
        tenant_bucket = self._certificates_by_tenant.get(tenant_id, {})
        certificate = tenant_bucket.get(certificate_id)
        if not certificate:
            raise KeyError("Certificate not found")
        return certificate
