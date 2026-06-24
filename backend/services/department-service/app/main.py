"""Service entrypoint — department-service REST API."""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import Response

from .security import apply_security_headers, require_jwt

# Add service root so src/ is importable as a package
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from .service import DepartmentManagementService, NotFoundError, ValidationError  # noqa: E402
from .schemas import (  # noqa: E402
    CreateDepartmentRequest,
    DeactivateDepartmentRequest,
    MapMembershipRequest,
    ReparentDepartmentRequest,
    UpdateDepartmentRequest,
)

app = FastAPI(title="department-service", version="1.0.0", dependencies=[Depends(require_jwt)])


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

_SERVICE = DepartmentManagementService()


def _tenant_context(
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_actor_id: Annotated[str | None, Header()] = None,
) -> tuple[str, str]:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_tenant_id")
    return x_tenant_id, x_actor_id or "system"


def _to_dict(obj) -> dict:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return obj


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "department-service"}


@app.get("/metrics")
def metrics() -> dict:
    return {"service": "department-service", "service_up": 1}


# ── Departments ───────────────────────────────────────────────────────────────

@app.post("/api/v1/departments", status_code=status.HTTP_201_CREATED)
def create_department(
    request: CreateDepartmentRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        dept = _SERVICE.create_department(
            tenant_id=tenant_id,
            organization_id=request.organization_id,
            name=request.name,
            code=request.code,
            parent_department_id=request.parent_department_id,
            department_head_user_id=request.department_head_user_id,
            cost_center=request.cost_center,
        )
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return _to_dict(dept)


@app.get("/api/v1/departments")
def list_departments(
    organization_id: Optional[str] = Query(default=None),
    dept_status: Optional[str] = Query(default=None, alias="status"),
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    departments = _SERVICE.list_departments(tenant_id=tenant_id, organization_id=organization_id, status=dept_status)
    return {"departments": [_to_dict(d) for d in departments], "total": len(departments)}


@app.get("/api/v1/departments/{department_id}")
def get_department(department_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        return _to_dict(_SERVICE.get_department(tenant_id=tenant_id, department_id=department_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.patch("/api/v1/departments/{department_id}")
def update_department(
    department_id: str,
    request: UpdateDepartmentRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        return _to_dict(_SERVICE.update_department(
            tenant_id=tenant_id,
            department_id=department_id,
            name=request.name,
            code=request.code,
            department_head_user_id=request.department_head_user_id,
            cost_center=request.cost_center,
        ))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@app.post("/api/v1/departments/{department_id}:deactivate")
def deactivate_department(
    department_id: str,
    request: DeactivateDepartmentRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    try:
        return _to_dict(_SERVICE.deactivate_department(
            tenant_id=tenant_id, department_id=department_id,
            actor_id=actor_id, cascade=request.cascade,
        ))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@app.post("/api/v1/departments/{department_id}:reactivate")
def reactivate_department(department_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, actor_id = ctx
    try:
        return _to_dict(_SERVICE.reactivate_department(
            tenant_id=tenant_id, department_id=department_id, actor_id=actor_id,
        ))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@app.post("/api/v1/departments/{department_id}:reparent")
def reparent_department(
    department_id: str,
    request: ReparentDepartmentRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    try:
        return _to_dict(_SERVICE.reparent_department(
            tenant_id=tenant_id,
            department_id=department_id,
            new_parent_department_id=request.new_parent_department_id,
            actor_id=actor_id,
        ))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@app.get("/api/v1/departments/{department_id}/children")
def list_children(department_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        children = _SERVICE.list_children(tenant_id=tenant_id, parent_department_id=department_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"departments": [_to_dict(d) for d in children], "total": len(children)}


# ── Membership ────────────────────────────────────────────────────────────────

@app.post("/api/v1/departments/{department_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(
    department_id: str,
    request: MapMembershipRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    """Spec §API — add member to department."""
    tenant_id, _ = ctx
    try:
        membership = _SERVICE.map_membership(
            tenant_id=tenant_id,
            organization_id=request.organization_id,
            department_id=department_id,
            user_id=request.user_id,
            role=request.role,
        )
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return _to_dict(membership)


@app.get("/api/v1/departments/{department_id}/members")
def list_members(department_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    """Spec §API — list department members."""
    tenant_id, _ = ctx
    try:
        members = _SERVICE.list_memberships(tenant_id=tenant_id, department_id=department_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"members": [_to_dict(m) for m in members], "total": len(members)}


# ── Audit log ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/department/audit-log")
def get_audit_log(ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    """Spec §API — tenant-scoped deactivation and reparenting audit log."""
    tenant_id, _ = ctx
    entries = _SERVICE.get_audit_log(tenant_id=tenant_id)
    return {"audit_log": entries, "total": len(entries)}
