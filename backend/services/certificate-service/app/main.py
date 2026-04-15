"""FastAPI entrypoint for certificate_service."""

from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from src.audit import AuditLogger

from .schemas import (
    BadgeExtensionRequest,
    CertificateResponse,
    CertificateTemplatePatchRequest,
    CertificateTemplateRequest,
    ErrorResponse,
    IssueCertificateRequest,
    RevokeCertificateRequest,
    VerificationResponse,
)
from .security import apply_security_headers, require_jwt
from .service import CertificateApplicationService, DomainError, EventPublisher, ObservabilityHooks
from .store import InMemoryCertificateStore

app = FastAPI(title="Certificate Service", version="1.0.0", dependencies=[Depends(require_jwt)])
apply_security_headers(app)

STORE = InMemoryCertificateStore()
AUDIT_LOGGER = AuditLogger("certificate-service")
EVENT_PUBLISHER = EventPublisher()
OBS_HOOKS = ObservabilityHooks()
SERVICE = CertificateApplicationService(STORE, AUDIT_LOGGER, EVENT_PUBLISHER, OBS_HOOKS)


def require_tenant_context(x_tenant_id: str = Header(alias="X-Tenant-Id")) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_context")
    return x_tenant_id




def _payload(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()

def _map_error(exc: DomainError) -> HTTPException:
    return HTTPException(status_code=409 if exc.code == "CERTIFICATE_ALREADY_EXISTS" else 404, detail=ErrorResponse(error={"code": exc.code, "message": exc.message, "correlation_id": str(uuid4())}).dict())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "certificate-service"}


@app.get("/metrics")
def metrics() -> dict[str, int]:
    return OBS_HOOKS.counters


@app.post("/api/v1/certificates", response_model=CertificateResponse)
def issue_certificate(request: IssueCertificateRequest, tenant_id: str = Depends(require_tenant_context)) -> CertificateResponse:
    try:
        cert = SERVICE.issue_certificate(tenant_id=tenant_id, request=_payload(request))
    except DomainError as exc:
        raise _map_error(exc) from exc
    return CertificateResponse(**asdict(cert))


@app.get("/api/v1/certificates/{certificate_id}", response_model=CertificateResponse)
def get_certificate(certificate_id: str, tenant_id: str = Depends(require_tenant_context)) -> CertificateResponse:
    cert = STORE.get_certificate(tenant_id=tenant_id, certificate_id=certificate_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="certificate_not_found")
    return CertificateResponse(**asdict(cert))


@app.post("/api/v1/certificates/{certificate_id}/revoke", response_model=CertificateResponse)
def revoke_certificate(certificate_id: str, request: RevokeCertificateRequest, tenant_id: str = Depends(require_tenant_context)) -> CertificateResponse:
    try:
        cert = SERVICE.revoke_certificate(tenant_id=tenant_id, certificate_id=certificate_id, reason=request.reason, revoked_by=request.revoked_by)
    except DomainError as exc:
        raise _map_error(exc) from exc
    return CertificateResponse(**asdict(cert))


@app.post("/api/v1/certificate-templates")
def create_template(request: CertificateTemplateRequest, tenant_id: str = Depends(require_tenant_context)) -> dict:
    template = SERVICE.create_or_update_template(tenant_id=tenant_id, template_id=request.template_id, name=request.name, body=request.body, metadata=request.metadata)
    return asdict(template)


@app.patch("/api/v1/certificate-templates/{template_id}")
def patch_template(template_id: str, request: CertificateTemplatePatchRequest, tenant_id: str = Depends(require_tenant_context)) -> dict:
    existing = STORE.get_template(tenant_id=tenant_id, template_id=template_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="template_not_found")
    template = SERVICE.create_or_update_template(
        tenant_id=tenant_id,
        template_id=template_id,
        name=request.name or existing.name,
        body=request.body or existing.body,
        metadata=request.metadata if request.metadata is not None else existing.metadata,
    )
    return asdict(template)


@app.get("/api/v1/certificate-templates/{template_id}")
def get_template(template_id: str, tenant_id: str = Depends(require_tenant_context)) -> dict:
    template = STORE.get_template(tenant_id=tenant_id, template_id=template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template_not_found")
    return asdict(template)


@app.get("/api/v1/certificates/verify/{verification_code}", response_model=VerificationResponse, dependencies=[])
def verify_certificate(verification_code: str, request: Request) -> VerificationResponse:
    try:
        verification = SERVICE.verify(verification_code, verification_url_base=str(request.base_url) + "api/v1/certificates/verify")
    except DomainError as exc:
        raise _map_error(exc) from exc
    return VerificationResponse(**asdict(verification))


@app.post("/api/v1/certificates/{certificate_id}/badge-extension")
def attach_badge_extension(certificate_id: str, request: BadgeExtensionRequest, tenant_id: str = Depends(require_tenant_context)) -> dict[str, str]:
    try:
        SERVICE.attach_badge_extension(
            tenant_id=tenant_id,
            certificate_id=certificate_id,
            provider=request.provider,
            badge_class_id=request.badge_class_id,
            evidence_url=request.evidence_url,
            metadata=request.metadata,
        )
    except DomainError as exc:
        raise _map_error(exc) from exc
    return {"status": "ok"}
