from __future__ import annotations

from fastapi import FastAPI

from app.errors import InstitutionServiceError
from app.models import InstitutionStatus
from app.repository import InstitutionRepository
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
)
from app.service import InstitutionService

app = FastAPI(title="institution-service", version="2.0.0")


class InstitutionAPI:
    def __init__(self) -> None:
        self.service = InstitutionService(InstitutionRepository())

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
