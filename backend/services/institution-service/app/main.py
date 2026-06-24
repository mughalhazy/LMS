from __future__ import annotations

from fastapi import Depends, FastAPI

from app.errors import InstitutionServiceError
from app.models import InstitutionStatus
from app.store_db import SQLiteInstitutionRepository
from app.schemas import (
    CreateHierarchyEdgeRequest,
    CreateInstitutionRequest,
    CreateInstitutionTypeRequest,
    CreateTenantLinkRequest,
    HealthResponse,
    InstitutionResponse,
    MetricsResponse,
    ReparentInstitutionRequest,
    TransitionInstitutionRequest,
    UpdateInstitutionRequest,
    UpdateInstitutionTypeRequest,
)
from app.security import apply_security_headers, require_jwt
from app.service import InstitutionService

# B01-017: spec §11 — authorization context required on every mutable operation
app = FastAPI(title="institution-service", version="2.0.0", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()

apply_security_headers(app)


class InstitutionAPI:
    def __init__(self) -> None:
        self.service = InstitutionService(SQLiteInstitutionRepository())

    def create_institution(self, request: CreateInstitutionRequest) -> InstitutionResponse:
        created = self.service.create_institution(request)
        return InstitutionResponse(
            institution_id=created.institution_id,
            institution_type=created.institution_type,
            legal_name=created.legal_name,
            display_name=created.display_name,
            tenant_id=created.tenant_id,
            status=created.status.value,
        )

    def get_institution(self, institution_id: str) -> InstitutionResponse:
        found = self.service.get_institution(institution_id)
        return InstitutionResponse(
            institution_id=found.institution_id,
            institution_type=found.institution_type,
            legal_name=found.legal_name,
            display_name=found.display_name,
            tenant_id=found.tenant_id,
            status=found.status.value,
        )

    def update_institution(self, institution_id: str, request: UpdateInstitutionRequest) -> InstitutionResponse:
        updated = self.service.update_institution(institution_id, request)
        return InstitutionResponse(
            institution_id=updated.institution_id,
            institution_type=updated.institution_type,
            legal_name=updated.legal_name,
            display_name=updated.display_name,
            tenant_id=updated.tenant_id,
            status=updated.status.value,
        )

    def activate_institution(self, institution_id: str, request: TransitionInstitutionRequest) -> InstitutionResponse:
        updated = self.service.transition_status(institution_id, InstitutionStatus.ACTIVE, request.actor_id, request.reason)
        return self.get_institution(updated.institution_id)

    def suspend_institution(self, institution_id: str, request: TransitionInstitutionRequest) -> InstitutionResponse:
        updated = self.service.transition_status(institution_id, InstitutionStatus.SUSPENDED, request.actor_id, request.reason)
        return self.get_institution(updated.institution_id)

    def archive_institution(self, institution_id: str, request: TransitionInstitutionRequest) -> InstitutionResponse:
        updated = self.service.transition_status(institution_id, InstitutionStatus.ARCHIVED, request.actor_id, request.reason)
        return self.get_institution(updated.institution_id)

    def add_parent(self, institution_id: str, request: CreateHierarchyEdgeRequest) -> dict:
        edge = self.service.add_parent_edge(institution_id, request)
        return edge.__dict__

    def remove_parent(self, institution_id: str, parent_id: str, actor_id: str) -> dict:
        edge = self.service.remove_parent_edge(institution_id, parent_id, actor_id)
        return edge.__dict__

    def get_hierarchy(self, institution_id: str) -> dict:
        return self.service.get_hierarchy(institution_id)

    def reparent(self, institution_id: str, request: ReparentInstitutionRequest) -> dict:
        edge = self.service.reparent_institution(institution_id, request)
        return edge.__dict__

    def list_institution_types(self) -> list[dict]:
        return [row.__dict__ for row in self.service.list_types()]

    def create_institution_type(self, request: CreateInstitutionTypeRequest) -> dict:
        created = self.service.create_type(request)
        return created.__dict__

    def create_tenant_link(self, institution_id: str, request: CreateTenantLinkRequest) -> dict:
        link = self.service.create_tenant_link(institution_id, request)
        return link.__dict__

    def list_tenant_links(self, institution_id: str) -> list[dict]:
        return [row.__dict__ for row in self.service.list_tenant_links(institution_id)]

    def get_tenant_institution_context(self, tenant_id: str) -> dict:
        return self.service.resolve_tenant_context(tenant_id)

    def health(self) -> HealthResponse:
        return HealthResponse(status="ok", service="institution-service")

    def metrics(self) -> MetricsResponse:
        institutions_total = len(self.service.repository.store.institutions)
        active_links_total = len([link for link in self.service.repository.store.tenant_links.values() if link.status == "active"])
        return MetricsResponse(
            service="institution-service",
            service_up=1,
            institutions_total=institutions_total,
            active_links_total=active_links_total,
        )


__all__ = ["InstitutionAPI", "InstitutionServiceError"]


_api = InstitutionAPI()


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return _api.health()


@app.get("/metrics", response_model=MetricsResponse, tags=["health"])
def metrics() -> MetricsResponse:
    return _api.metrics()


# ── Institution lifecycle ─────────────────────────────────────────────────────

@app.post("/api/v1/institutions", response_model=InstitutionResponse, status_code=201)
def create_institution(request: CreateInstitutionRequest) -> InstitutionResponse:
    try:
        return _api.create_institution(request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/api/v1/institutions/{institution_id}", response_model=InstitutionResponse)
def get_institution(institution_id: str) -> InstitutionResponse:
    try:
        return _api.get_institution(institution_id)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.patch("/api/v1/institutions/{institution_id}", response_model=InstitutionResponse)
def update_institution(institution_id: str, request: UpdateInstitutionRequest) -> InstitutionResponse:
    try:
        return _api.update_institution(institution_id, request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/api/v1/institutions/{institution_id}/activate", response_model=InstitutionResponse)
def activate_institution(institution_id: str, request: TransitionInstitutionRequest) -> InstitutionResponse:
    try:
        return _api.activate_institution(institution_id, request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/api/v1/institutions/{institution_id}/suspend", response_model=InstitutionResponse)
def suspend_institution(institution_id: str, request: TransitionInstitutionRequest) -> InstitutionResponse:
    try:
        return _api.suspend_institution(institution_id, request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/api/v1/institutions/{institution_id}/archive", response_model=InstitutionResponse)
def archive_institution(institution_id: str, request: TransitionInstitutionRequest) -> InstitutionResponse:
    try:
        return _api.archive_institution(institution_id, request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


# ── Hierarchy management ──────────────────────────────────────────────────────

@app.post("/api/v1/institutions/{institution_id}/parents/{parent_id}")
def add_parent(institution_id: str, parent_id: str, request: CreateHierarchyEdgeRequest) -> dict:
    # parent_id path param is provided for REST consistency; canonical parent is in request body.
    try:
        return _api.add_parent(institution_id, request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.delete("/api/v1/institutions/{institution_id}/parents/{parent_id}")
def remove_parent(
    institution_id: str,
    parent_id: str,
    actor_id: str = "system",
) -> dict:
    try:
        return _api.remove_parent(institution_id, parent_id, actor_id)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/api/v1/institutions/{institution_id}/hierarchy")
def get_hierarchy(institution_id: str) -> dict:
    try:
        return _api.get_hierarchy(institution_id)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/api/v1/institutions/{institution_id}/reparent")
def reparent_institution(institution_id: str, request: ReparentInstitutionRequest) -> dict:
    try:
        return _api.reparent(institution_id, request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


# ── Institution types ─────────────────────────────────────────────────────────

@app.get("/api/v1/institution-types")
def list_institution_types() -> list[dict]:
    return _api.list_institution_types()


@app.post("/api/v1/institution-types", status_code=201)
def create_institution_type(request: CreateInstitutionTypeRequest) -> dict:
    try:
        return _api.create_institution_type(request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.patch("/api/v1/institution-types/{type_code}")
def update_institution_type(type_code: str, request: UpdateInstitutionTypeRequest) -> dict:
    # B01-018: typed Pydantic schema replaces raw dict — enables request validation + OpenAPI docs
    try:
        updated = _api.service.update_type(type_code, governance_profile=request.governance_profile)
        return updated.__dict__
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


# ── Tenant linkage ────────────────────────────────────────────────────────────

@app.post("/api/v1/institutions/{institution_id}/tenant-links", status_code=201)
def create_tenant_link(institution_id: str, request: CreateTenantLinkRequest) -> dict:
    try:
        return _api.create_tenant_link(institution_id, request)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/api/v1/institutions/{institution_id}/tenant-links")
def list_tenant_links(institution_id: str) -> list[dict]:
    return _api.list_tenant_links(institution_id)


@app.delete("/api/v1/institutions/{institution_id}/tenant-links/{link_id}", status_code=204)
def deactivate_tenant_link(institution_id: str, link_id: str) -> None:
    try:
        _api.service.deactivate_tenant_link(institution_id, link_id)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/api/v1/tenants/{tenant_id}/institution-context")
def get_tenant_institution_context(tenant_id: str) -> dict:
    try:
        return _api.get_tenant_institution_context(tenant_id)
    except InstitutionServiceError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
