from __future__ import annotations

from fastapi import Depends, FastAPI, Header, Response

from .schemas import (
    AddMembershipRequest,
    CohortKind,
    CohortResponse,
    CohortWithMembershipsResponse,
    CreateCohortRequest,
    HealthResponse,
    LinkProgramRequest,
    MembershipResponse,
    MetricsResponse,
    UpdateCohortRequest,
)
from .security import TenantContext, apply_security_headers, get_tenant_context, require_jwt
from .service import CohortService

app = FastAPI(title="Cohort Service", version="0.1.0", dependencies=[Depends(require_jwt)])
apply_security_headers(app)
service = CohortService()


@app.post("/api/v1/cohorts", response_model=CohortResponse, status_code=201)
def create_cohort(request: CreateCohortRequest, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    return service.create_cohort(tenant.tenant_id, request)


@app.post("/api/v1/batches", response_model=CohortResponse, status_code=201)
def create_batch(request: CreateCohortRequest, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    request.kind = CohortKind.ACADEMY_BATCH
    return service.create_cohort(tenant.tenant_id, request)


@app.get("/api/v1/cohorts", response_model=list[CohortResponse])
def list_cohorts(tenant: TenantContext = Depends(get_tenant_context)) -> list[CohortResponse]:
    return service.list_cohorts(tenant.tenant_id)


@app.get("/api/v1/cohorts/{cohort_id}", response_model=CohortWithMembershipsResponse)
def get_cohort(cohort_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> CohortWithMembershipsResponse:
    return service.get_cohort(tenant.tenant_id, cohort_id)


@app.patch("/api/v1/cohorts/{cohort_id}", response_model=CohortResponse)
def update_cohort(
    cohort_id: str,
    request: UpdateCohortRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> CohortResponse:
    return service.update_cohort(tenant.tenant_id, cohort_id, request)


@app.post("/api/v1/cohorts/{cohort_id}/program-link", response_model=CohortResponse)
def link_program(
    cohort_id: str,
    request: LinkProgramRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> CohortResponse:
    return service.link_program(tenant.tenant_id, cohort_id, request)


@app.post("/api/v1/cohorts/{cohort_id}/memberships", response_model=MembershipResponse, status_code=201)
def add_membership(
    cohort_id: str,
    request: AddMembershipRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MembershipResponse:
    return service.add_membership(tenant.tenant_id, cohort_id, request)


@app.delete("/api/v1/cohorts/{cohort_id}/memberships/{membership_id}", status_code=204)
def remove_membership(
    cohort_id: str,
    membership_id: str,
    removed_by: str = Header(..., alias="X-Actor-ID"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Response:
    service.remove_membership(tenant.tenant_id, cohort_id, membership_id, removed_by)
    return Response(status_code=204)


@app.delete("/api/v1/cohorts/{cohort_id}", status_code=204)
def delete_cohort(
    cohort_id: str,
    deleted_by: str = Header(..., alias="X-Actor-ID"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Response:
    service.delete_cohort(tenant.tenant_id, cohort_id, deleted_by)
    return Response(status_code=204)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="cohort-service")


@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    return MetricsResponse(service="cohort-service", counters=service.observability.counters)
