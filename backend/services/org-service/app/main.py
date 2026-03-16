from __future__ import annotations

from fastapi import FastAPI, Header, Depends
from .security import apply_security_headers, require_jwt

from .repository import InMemoryOrgRepository
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

apply_security_headers(app)
repo = InMemoryOrgRepository()
service = OrganizationService(repo)


@app.post("/organizations", response_model=OrganizationOut, status_code=201)
def create_organization(payload: OrganizationCreate) -> OrganizationOut:
    return service.create_organization(payload.model_dump())


@app.patch("/organizations/{organization_id}", response_model=OrganizationOut)
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


@app.post("/organizations/{organization_id}/deactivate", response_model=OrganizationOut)
def deactivate_organization(organization_id: str, payload: LifecycleRequest) -> OrganizationOut:
    return service.deactivate_organization(organization_id, payload.cascade)


@app.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(payload: DepartmentCreate) -> DepartmentOut:
    return service.create_department(payload.model_dump())


@app.patch("/departments/{department_id}", response_model=DepartmentOut)
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


@app.post("/teams", response_model=TeamOut, status_code=201)
def create_team(payload: TeamCreate) -> TeamOut:
    return service.create_team(payload.model_dump())


@app.patch("/teams/{team_id}", response_model=TeamOut)
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


@app.get("/organizations/{organization_id}/hierarchy", response_model=HierarchyOut)
def get_hierarchy(organization_id: str) -> HierarchyOut:
    return service.hierarchy(organization_id)


@app.get("/audit/reparent-events")
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

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "org-service"}

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "org-service", "service_up": 1}

