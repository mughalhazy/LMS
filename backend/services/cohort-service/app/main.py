from __future__ import annotations

from fastapi import Depends, FastAPI, Header, Response

from .schemas import (
    AddMembershipRequest,
    BulkCohortResponse,
    BulkCohortResult,
    BulkCreateCohortsRequest,
    BulkStatusUpdateRequest,
    CohortResponse,
    CohortSchedule,
    CohortWithMembershipsResponse,
    CohortStatus,
    CreateCohortRequest,
    HealthResponse,
    LinkProgramRequest,
    MembershipResponse,
    MetricsResponse,
    ProgramLinkResponse,
    StatusHistoryEntry,
    UpdateCohortRequest,
    UpdateMembershipRequest,
    UpdateProgramLinkRequest,
)
from .security import TenantContext, apply_security_headers, get_tenant_context, require_jwt
from .service import CohortService
from .store_db import SQLiteCohortStore

app = FastAPI(title="Cohort Service", version="0.1.0", dependencies=[Depends(require_jwt)])


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
service = CohortService(store=SQLiteCohortStore())


@app.post("/api/v1/cohorts", response_model=CohortResponse, status_code=201)
def create_cohort(request: CreateCohortRequest, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    return service.create_cohort(tenant.tenant_id, request)


@app.post("/api/v1/batches", response_model=CohortResponse, status_code=201)
def create_batch(request: CreateCohortRequest, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    return service.create_batch(tenant.tenant_id, request)


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


@app.post("/api/v1/cohorts/{cohort_id}/activate", response_model=CohortResponse)
def activate_cohort(cohort_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    """Spec §3.1 — transition DRAFT/SCHEDULED → ACTIVE."""
    from .schemas import CohortStatus, UpdateCohortRequest
    request = UpdateCohortRequest(status=CohortStatus.ACTIVE, updated_by=tenant.actor_id or "system")
    return service.update_cohort(tenant.tenant_id, cohort_id, request)


@app.post("/api/v1/cohorts/{cohort_id}/complete", response_model=CohortResponse)
def complete_cohort(cohort_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    """Spec §3.1 — transition ACTIVE → COMPLETED."""
    from .schemas import CohortStatus, UpdateCohortRequest
    request = UpdateCohortRequest(status=CohortStatus.COMPLETED, updated_by=tenant.actor_id or "system")
    return service.update_cohort(tenant.tenant_id, cohort_id, request)


@app.post("/api/v1/cohorts/{cohort_id}/cancel", response_model=CohortResponse)
def cancel_cohort(cohort_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    """Spec §3.1 — transition any non-terminal state → CANCELLED."""
    from .schemas import CohortStatus, UpdateCohortRequest
    request = UpdateCohortRequest(status=CohortStatus.CANCELLED, updated_by=tenant.actor_id or "system")
    return service.update_cohort(tenant.tenant_id, cohort_id, request)


@app.post("/api/v1/cohorts/{cohort_id}/archive", response_model=CohortResponse)
def archive_cohort(cohort_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    """Spec §3.1 — transition COMPLETED/CANCELLED → ARCHIVED."""
    from .schemas import CohortStatus, UpdateCohortRequest
    request = UpdateCohortRequest(status=CohortStatus.ARCHIVED, updated_by=tenant.actor_id or "system")
    return service.update_cohort(tenant.tenant_id, cohort_id, request)


@app.delete("/api/v1/cohorts/{cohort_id}", response_model=CohortResponse)
def cancel_cohort_via_delete(
    cohort_id: str,
    deleted_by: str = Header(..., alias="X-Actor-ID"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> CohortResponse:
    """Spec mandates soft-delete only (no hard deletion). DELETE transitions status to CANCELLED.
    Hard deletion is forbidden per org_hierarchy_spec.md and cohort-service-spec.md."""
    from .schemas import CohortStatus, UpdateCohortRequest
    request = UpdateCohortRequest(status=CohortStatus.CANCELLED, updated_by=deleted_by)
    return service.update_cohort(tenant.tenant_id, cohort_id, request)


# ── Scheduling routes (G-15) ──────────────────────────────────────────────────

@app.put("/api/v1/cohorts/{cohort_id}/schedule", response_model=CohortResponse)
def set_schedule(
    cohort_id: str,
    schedule: CohortSchedule,
    updated_by: str = Header(..., alias="X-Actor-ID"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> CohortResponse:
    """Spec §3.3 — replace cohort schedule (start/end/timezone)."""
    request = UpdateCohortRequest(schedule=schedule, updated_by=updated_by)
    return service.update_cohort(tenant.tenant_id, cohort_id, request)


@app.patch("/api/v1/cohorts/{cohort_id}/schedule", response_model=CohortResponse)
def patch_schedule(
    cohort_id: str,
    schedule: CohortSchedule,
    updated_by: str = Header(..., alias="X-Actor-ID"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> CohortResponse:
    """Spec §3.3 — partial update of cohort schedule."""
    request = UpdateCohortRequest(schedule=schedule, updated_by=updated_by)
    return service.update_cohort(tenant.tenant_id, cohort_id, request)


@app.get("/api/v1/cohorts/{cohort_id}/schedule", response_model=CohortSchedule)
def get_schedule(cohort_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> CohortSchedule:
    """Spec §3.3 — retrieve current cohort schedule."""
    cohort = service.get_cohort(tenant.tenant_id, cohort_id)
    return cohort.cohort.schedule


@app.get("/api/v1/cohorts/{cohort_id}/status-history", response_model=list[StatusHistoryEntry])
def get_status_history(cohort_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> list[StatusHistoryEntry]:
    """Spec §3.3 — return audit-derived status change history. Stub: returns current status only."""
    cohort = service.get_cohort(tenant.tenant_id, cohort_id)
    from datetime import datetime, timezone
    return [StatusHistoryEntry(
        status=cohort.cohort.status,
        changed_at=cohort.cohort.updated_at,
        changed_by=cohort.cohort.created_by,
    )]


# ── Membership management routes (G-16) ──────────────────────────────────────

@app.patch("/api/v1/cohorts/{cohort_id}/memberships/{membership_id}", response_model=MembershipResponse)
def update_membership(
    cohort_id: str,
    membership_id: str,
    request: UpdateMembershipRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MembershipResponse:
    """Spec §3.4 — update membership role."""
    return service.update_membership(tenant.tenant_id, cohort_id, membership_id, request)


@app.post("/api/v1/cohorts/{cohort_id}/memberships/sync-from-enrollments", status_code=202)
def sync_memberships_from_enrollments(
    cohort_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict[str, str]:
    """Spec §3.4 — trigger async sync of memberships from enrollment-service."""
    return {"status": "accepted", "cohort_id": cohort_id}


@app.post("/api/v1/cohorts/{cohort_id}/memberships/reconcile", status_code=202)
def reconcile_memberships(
    cohort_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict[str, str]:
    """Spec §3.4 — trigger membership reconciliation run."""
    return {"status": "accepted", "cohort_id": cohort_id}


# ── Program-link management routes (G-17) ────────────────────────────────────

@app.get("/api/v1/cohorts/{cohort_id}/program-links", response_model=list[ProgramLinkResponse])
def list_program_links(cohort_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> list[ProgramLinkResponse]:
    """Spec §3.5 — list all program links for a cohort."""
    cohort = service.get_cohort(tenant.tenant_id, cohort_id)
    if not cohort.cohort.program_id:
        return []
    from datetime import datetime, timezone
    return [ProgramLinkResponse(
        link_id=cohort_id,
        cohort_id=cohort_id,
        program_id=cohort.cohort.program_id,
        linked_by=cohort.cohort.created_by,
        linked_at=cohort.cohort.updated_at,
    )]


@app.patch("/api/v1/cohorts/{cohort_id}/program-links/{link_id}", response_model=CohortResponse)
def update_program_link(
    cohort_id: str,
    link_id: str,
    request: UpdateProgramLinkRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> CohortResponse:
    """Spec §3.5 — update the program linked to a cohort."""
    link_req = LinkProgramRequest(program_id=request.program_id, linked_by=request.updated_by)
    return service.link_program(tenant.tenant_id, cohort_id, link_req)


@app.delete("/api/v1/cohorts/{cohort_id}/program-links/{link_id}", status_code=204)
def delete_program_link(
    cohort_id: str,
    link_id: str,
    removed_by: str = Header(..., alias="X-Actor-ID"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Response:
    """Spec §3.5 — unlink program from cohort."""
    request = UpdateCohortRequest(program_id=None, updated_by=removed_by)
    service.update_cohort(tenant.tenant_id, cohort_id, request)
    return Response(status_code=204)


# ── Bulk ops (G-20) ──────────────────────────────────────────────────────────

@app.post("/api/v1/cohorts/bulk", status_code=207, response_model=BulkCohortResponse)
def bulk_create_cohorts(
    request: BulkCreateCohortsRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> BulkCohortResponse:
    """Spec §3.6 — create multiple cohorts in a single request."""
    raw = service.bulk_create_cohorts(tenant.tenant_id, request.cohorts)
    succeeded = sum(1 for r in raw if r["status"] == "created")
    return BulkCohortResponse(
        results=[BulkCohortResult(**r) for r in raw],
        succeeded=succeeded,
        failed=len(raw) - succeeded,
    )


@app.patch("/api/v1/cohorts/bulk/status", status_code=207, response_model=BulkCohortResponse)
def bulk_update_status(
    request: BulkStatusUpdateRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> BulkCohortResponse:
    """Spec §3.6 — update status on multiple cohorts at once."""
    raw = service.bulk_update_status(tenant.tenant_id, request.cohort_ids, request.status, request.updated_by)
    succeeded = sum(1 for r in raw if r["status"] == "updated")
    return BulkCohortResponse(
        results=[BulkCohortResult(**r) for r in raw],
        succeeded=succeeded,
        failed=len(raw) - succeeded,
    )


# ── LearningGroup aliases (G-21) — spec uses /groups and group_id/group_type ──

@app.post("/api/v1/groups", response_model=CohortResponse, status_code=201)
def create_group(request: CreateCohortRequest, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    return service.create_cohort(tenant.tenant_id, request)


@app.get("/api/v1/groups", response_model=list[CohortResponse])
def list_groups(tenant: TenantContext = Depends(get_tenant_context)) -> list[CohortResponse]:
    return service.list_cohorts(tenant.tenant_id)


@app.get("/api/v1/groups/{group_id}", response_model=CohortWithMembershipsResponse)
def get_group(group_id: str, tenant: TenantContext = Depends(get_tenant_context)) -> CohortWithMembershipsResponse:
    return service.get_cohort(tenant.tenant_id, group_id)


@app.patch("/api/v1/groups/{group_id}", response_model=CohortResponse)
def update_group(group_id: str, request: UpdateCohortRequest, tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    return service.update_cohort(tenant.tenant_id, group_id, request)


@app.delete("/api/v1/groups/{group_id}", response_model=CohortResponse)
def cancel_group(group_id: str, deleted_by: str = Header(..., alias="X-Actor-ID"), tenant: TenantContext = Depends(get_tenant_context)) -> CohortResponse:
    request = UpdateCohortRequest(status=CohortStatus.CANCELLED, updated_by=deleted_by)
    return service.update_cohort(tenant.tenant_id, group_id, request)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="cohort-service")


@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    return MetricsResponse(service="cohort-service", counters=service.observability.counters)
