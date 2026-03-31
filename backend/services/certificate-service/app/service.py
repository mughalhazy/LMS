"""Certificate application service logic."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.audit import AuditLogger
from shared.models.university import UniversityCompletionPayload

from .models import BadgeExtensionProfile, Certificate, CertificateStatus, CertificateTemplate, CompletionRef, VerificationMetadata
from .store import CertificateStore


class DomainError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class EventPublisher:
    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        self.published.append({
            "event_id": str(uuid4()),
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": payload.get("tenant_id", "unknown"),
            "correlation_id": str(uuid4()),
            "payload": payload,
            "metadata": {"producer": "certificate-service"},
        })


class ObservabilityHooks:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def increment(self, key: str) -> None:
        self.counters[key] = self.counters.get(key, 0) + 1


class CertificateApplicationService:
    def __init__(self, store: CertificateStore, audit_logger: AuditLogger, publisher: EventPublisher, obs: ObservabilityHooks) -> None:
        self.store = store
        self.audit = audit_logger
        self.publisher = publisher
        self.obs = obs

    def issue_certificate(self, *, tenant_id: str, request: dict[str, Any]) -> Certificate:
        if self.store.has_active_certificate(tenant_id=tenant_id, user_id=request["user_id"], course_id=request["course_id"]):
            raise DomainError("CERTIFICATE_ALREADY_EXISTS", "A certificate already exists for tenant/user/course.")
        self._validate_completion_flow(tenant_id=tenant_id, request=request)

        now = datetime.utcnow()
        cert = Certificate(
            certificate_id=f"cert_{uuid4().hex[:12]}",
            verification_code=f"VRF-{uuid4().hex[:10].upper()}",
            tenant_id=tenant_id,
            user_id=request["user_id"],
            course_id=request["course_id"],
            enrollment_id=request.get("enrollment_id"),
            template_id=request["template_id"],
            status=CertificateStatus.ACTIVE,
            issued_at=now,
            expires_at=request.get("expires_at"),
            artifact_uri=request.get("artifact_uri"),
            metadata=request.get("metadata", {}),
            completion_ref=CompletionRef(**request["completion_ref"]),
        )
        self.store.create_certificate(cert)

        event_payload = {
            "certificate_id": cert.certificate_id,
            "verification_code": cert.verification_code,
            "tenant_id": cert.tenant_id,
            "user_id": cert.user_id,
            "course_id": cert.course_id,
            "enrollment_id": cert.enrollment_id,
            "issued_at": cert.issued_at.isoformat(),
            "expires_at": cert.expires_at.isoformat() if cert.expires_at else None,
            "status": cert.status,
            "template_id": cert.template_id,
            "completion_ref": asdict(cert.completion_ref),
        }
        self.publisher.publish("lms.certificate.issued.v1", event_payload)
        self.audit.log(event_type="certificate.issued", tenant_id=tenant_id, actor_id=request["issued_by"], details=event_payload)
        self.obs.increment("certificate_issued_total")
        return cert

    def revoke_certificate(self, *, tenant_id: str, certificate_id: str, reason: str, revoked_by: str) -> Certificate:
        cert = self._require_certificate(tenant_id, certificate_id)
        cert.status = CertificateStatus.REVOKED
        cert.revoked_at = datetime.utcnow()
        cert.revocation_reason = reason
        payload = {
            "certificate_id": cert.certificate_id,
            "tenant_id": tenant_id,
            "revoked_at": cert.revoked_at.isoformat(),
            "revocation_reason": reason,
            "revoked_by": revoked_by,
        }
        self.publisher.publish("lms.certificate.revoked.v1", payload)
        self.audit.log(event_type="certificate.revoked", tenant_id=tenant_id, actor_id=revoked_by, details=payload)
        self.obs.increment("certificate_revoked_total")
        return cert

    def verify(self, verification_code: str, verification_url_base: str) -> VerificationMetadata:
        cert = self.store.find_by_verification_code(verification_code)
        if cert is None:
            raise DomainError("CERTIFICATE_NOT_FOUND", "Verification code not found.")

        now = datetime.utcnow()
        if cert.status == CertificateStatus.ACTIVE and cert.expires_at and now >= cert.expires_at:
            cert.status = CertificateStatus.EXPIRED
            self.publisher.publish("lms.certificate.expired.v1", {"certificate_id": cert.certificate_id, "tenant_id": cert.tenant_id, "expired_at": now.isoformat()})
            self.obs.increment("certificate_expired_total")

        claims = {
            "tenant_id": cert.tenant_id,
            "user_id": cert.user_id,
            "course_id": cert.course_id,
            "template_id": cert.template_id,
        }
        return VerificationMetadata(
            verification_code=cert.verification_code,
            certificate_id=cert.certificate_id,
            status=cert.status,
            is_valid=cert.status == CertificateStatus.ACTIVE,
            issued_at=cert.issued_at,
            expires_at=cert.expires_at,
            revoked_at=cert.revoked_at,
            verification_url=f"{verification_url_base.rstrip('/')}/{cert.verification_code}",
            claims=claims,
        )

    def create_or_update_template(self, *, tenant_id: str, template_id: str, name: str, body: str, metadata: dict[str, Any]) -> CertificateTemplate:
        template = CertificateTemplate(template_id=template_id, tenant_id=tenant_id, name=name, version=1, body=body, metadata=metadata)
        template = self.store.upsert_template(template)
        evt = "lms.certificate.template_created.v1" if template.version == 1 else "lms.certificate.template_updated.v1"
        payload = {"template_id": template.template_id, "tenant_id": tenant_id, "name": template.name, "version": template.version}
        self.publisher.publish(evt, payload)
        self.obs.increment("certificate_template_mutation_total")
        return template

    def attach_badge_extension(self, *, tenant_id: str, certificate_id: str, provider: str, badge_class_id: str, evidence_url: str | None, metadata: dict[str, Any]) -> None:
        cert = self._require_certificate(tenant_id, certificate_id)
        extension = BadgeExtensionProfile(certificate_id=cert.certificate_id, provider=provider, badge_class_id=badge_class_id, evidence_url=evidence_url, metadata=metadata)
        self.store.attach_badge_extension(extension)
        payload = {"certificate_id": certificate_id, "tenant_id": tenant_id, "provider": provider, "badge_class_id": badge_class_id}
        self.publisher.publish("lms.certificate.badge_extension_attached.v1", payload)
        self.obs.increment("certificate_badge_extension_total")

    def _require_certificate(self, tenant_id: str, certificate_id: str) -> Certificate:
        cert = self.store.get_certificate(tenant_id=tenant_id, certificate_id=certificate_id)
        if cert is None:
            raise DomainError("CERTIFICATE_NOT_FOUND", "Certificate not found.")
        return cert


    def _validate_completion_flow(self, *, tenant_id: str, request: dict[str, Any]) -> None:
        completion_ref = request.get("completion_ref", {})
        source_event = completion_ref.get("source_event", "")
        if "completed" not in source_event:
            raise DomainError("INVALID_COMPLETION_EVENT", "completion_ref.source_event must indicate completion.")

        metadata = request.get("metadata", {})
        progress = metadata.get("assessment_progression")
        if progress:
            required = int(progress.get("required_assessment_count", 0))
            passed = int(progress.get("passed_assessment_count", 0))
            if passed < required:
                raise DomainError("ASSESSMENT_PROGRESSION_INCOMPLETE", "All required assessments must be passed before certificate issuance.")

        UniversityCompletionPayload(
            tenant_id=tenant_id,
            user_id=request["user_id"],
            course_id=request["course_id"],
            program_id=metadata.get("program_id"),
            completed_at=request["completion_ref"]["completed_at"],
            metadata=metadata,
        )
