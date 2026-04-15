"""Storage contract and in-memory adapter for certificate_service."""

from __future__ import annotations

from typing import Protocol

from .models import BadgeExtensionProfile, Certificate, CertificateTemplate


class CertificateStore(Protocol):
    def create_certificate(self, certificate: Certificate) -> None: ...
    def get_certificate(self, *, tenant_id: str, certificate_id: str) -> Certificate | None: ...
    def find_by_verification_code(self, verification_code: str) -> Certificate | None: ...
    def list_certificates(self, *, tenant_id: str) -> list[Certificate]: ...
    def upsert_template(self, template: CertificateTemplate) -> CertificateTemplate: ...
    def get_template(self, *, tenant_id: str, template_id: str) -> CertificateTemplate | None: ...
    def attach_badge_extension(self, extension: BadgeExtensionProfile) -> None: ...
    def has_active_certificate(self, *, tenant_id: str, user_id: str, course_id: str) -> bool: ...


class InMemoryCertificateStore:
    def __init__(self) -> None:
        self._certs: dict[str, dict[str, Certificate]] = {}
        self._verify_index: dict[str, tuple[str, str]] = {}
        self._templates: dict[str, dict[str, CertificateTemplate]] = {}
        self._badge_extensions: dict[str, BadgeExtensionProfile] = {}

    def create_certificate(self, certificate: Certificate) -> None:
        self._certs.setdefault(certificate.tenant_id, {})[certificate.certificate_id] = certificate
        self._verify_index[certificate.verification_code] = (certificate.tenant_id, certificate.certificate_id)

    def get_certificate(self, *, tenant_id: str, certificate_id: str) -> Certificate | None:
        return self._certs.get(tenant_id, {}).get(certificate_id)

    def find_by_verification_code(self, verification_code: str) -> Certificate | None:
        reference = self._verify_index.get(verification_code)
        if reference is None:
            return None
        tenant_id, cert_id = reference
        return self.get_certificate(tenant_id=tenant_id, certificate_id=cert_id)

    def list_certificates(self, *, tenant_id: str) -> list[Certificate]:
        return list(self._certs.get(tenant_id, {}).values())

    def upsert_template(self, template: CertificateTemplate) -> CertificateTemplate:
        bucket = self._templates.setdefault(template.tenant_id, {})
        existing = bucket.get(template.template_id)
        if existing:
            template.version = existing.version + 1
        bucket[template.template_id] = template
        return template

    def get_template(self, *, tenant_id: str, template_id: str) -> CertificateTemplate | None:
        return self._templates.get(tenant_id, {}).get(template_id)

    def attach_badge_extension(self, extension: BadgeExtensionProfile) -> None:
        self._badge_extensions[extension.certificate_id] = extension

    def has_active_certificate(self, *, tenant_id: str, user_id: str, course_id: str) -> bool:
        for cert in self._certs.get(tenant_id, {}).values():
            if cert.user_id == user_id and cert.course_id == course_id and cert.status == "active":
                return True
        return False
