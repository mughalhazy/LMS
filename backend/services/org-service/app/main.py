from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, Header, Query
from fastapi.responses import Response

from .security import apply_security_headers, require_jwt

from .store_db import SQLiteOrgRepository
from .schemas import (
    DepartmentCreate,
    DepartmentOut,
    DepartmentPatch,
    HierarchyOut,
    LifecycleRequest,
    OrganizationCreate,
    OrganizationOut,
    OrganizationPatch,
    TeamCreate,
    TeamOut,
    TeamPatch,
)
from .service import OrganizationService

app = FastAPI(title="Organization Service", version="1.0.0", dependencies=[Depends(require_jwt)])


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
repo = SQLiteOrgRepository()
service = OrganizationService(repo)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "org-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "org-service", "service_up": 1}


@app.post("/api/v1/organizations", response_model=OrganizationOut, status_code=201)
def create_organization(payload: OrganizationCreate) -> OrganizationOut:
    return service.create_organization(payload.model_dump())


@app.patch("/api/v1/organizations/{organization_id}", response_model=OrganizationOut)
def patch_organization(
    organization_id: str,
    payload: OrganizationPatch,
    x_actor_user_id: str = Header(default="system"),
) -> OrganizationOut:
    return service.patch_organization(
        organization_id,
        {k: v for k, v in payload.model_dump().items() if v is not None},
        actor_user_id=x_actor_user_id,
    )


@app.post("/api/v1/organizations/{organization_id}/deactivate", response_model=OrganizationOut)
def deactivate_organization(organization_id: str, payload: LifecycleRequest) -> OrganizationOut:
    return service.deactivate_organization(organization_id, payload.cascade)


@app.get("/api/v1/organizations/{organization_id}/hierarchy", response_model=HierarchyOut)
def get_hierarchy(organization_id: str) -> HierarchyOut:
    return service.hierarchy(organization_id)


@app.post("/api/v1/departments", response_model=DepartmentOut, status_code=201)
def create_department(payload: DepartmentCreate) -> DepartmentOut:
    return service.create_department(payload.model_dump())


@app.patch("/api/v1/departments/{department_id}", response_model=DepartmentOut)
def patch_department(
    department_id: str,
    payload: DepartmentPatch,
    x_actor_user_id: str = Header(default="system"),
) -> DepartmentOut:
    return service.patch_department(
        department_id,
        {k: v for k, v in payload.model_dump().items() if v is not None},
        actor_user_id=x_actor_user_id,
    )


@app.post("/api/v1/teams", response_model=TeamOut, status_code=201)
def create_team(payload: TeamCreate) -> TeamOut:
    return service.create_team(payload.model_dump())


@app.patch("/api/v1/teams/{team_id}", response_model=TeamOut)
def patch_team(
    team_id: str,
    payload: TeamPatch,
    x_actor_user_id: str = Header(default="system"),
) -> TeamOut:
    return service.patch_team(
        team_id,
        {k: v for k, v in payload.model_dump().items() if v is not None},
        actor_user_id=x_actor_user_id,
    )


@app.get("/api/v1/audit/reparent-events")
def list_reparent_audit_events() -> list[dict]:
    return [
        {
            "actor_user_id": e.actor_user_id,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "old_parent_id": e.old_parent_id,
            "new_parent_id": e.new_parent_id,
            "changed_at": e.changed_at,
        }
        for e in repo.reparent_audit_logs
    ]


# ── Read routes ───────────────────────────────────────────────────────────────

@app.get("/api/v1/organizations", response_model=list[OrganizationOut])
def list_organizations(
    tenant_id: Optional[str] = Query(default=None),
) -> list[OrganizationOut]:
    return service.list_organizations(tenant_id=tenant_id)


@app.get("/api/v1/organizations/{organization_id}", response_model=OrganizationOut)
def get_organization(organization_id: str) -> OrganizationOut:
    return service.get_organization(organization_id)


@app.get("/api/v1/departments/{department_id}", response_model=DepartmentOut)
def get_department(department_id: str) -> DepartmentOut:
    return service.get_department(department_id)


@app.get("/api/v1/teams", response_model=list[TeamOut])
def list_teams(
    department_id: Optional[str] = Query(default=None),
) -> list[TeamOut]:
    return service.list_teams(department_id=department_id)


@app.get("/api/v1/teams/{team_id}", response_model=TeamOut)
def get_team(team_id: str) -> TeamOut:
    return service.get_team(team_id)


# ── Delete routes ─────────────────────────────────────────────────────────────

@app.delete("/api/v1/organizations/{organization_id}", status_code=204)
def delete_organization(organization_id: str) -> Response:
    service.delete_organization(organization_id)
    return Response(status_code=204)


@app.delete("/api/v1/departments/{department_id}", status_code=204)
def delete_department(department_id: str) -> Response:
    service.delete_department(department_id)
    return Response(status_code=204)


@app.delete("/api/v1/teams/{team_id}", status_code=204)
def delete_team(team_id: str) -> Response:
    service.delete_team(team_id)
    return Response(status_code=204)
