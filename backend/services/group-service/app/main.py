"""Service entrypoint — group-service REST API."""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import Response

# Add service root so src/ is importable as a package
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.models import GroupStatus  # noqa: E402
from .service import GroupManagementService, NotFoundError, ValidationError  # noqa: E402
from .schemas import (  # noqa: E402
    AddMemberRequest,
    AssignLearningRequest,
    CreateGroupRequest,
    UpdateGroupRequest,
)
from .security import apply_security_headers, require_jwt  # noqa: E402

# B02-008: multi-tenant-isolation-model §2 — JWT required
app = FastAPI(title="group-service", version="1.0.0", dependencies=[Depends(require_jwt)])


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
_SERVICE = GroupManagementService()


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
    return {"status": "ok", "service": "group-service"}


@app.get("/metrics")
def metrics() -> dict:
    return {"service": "group-service", "service_up": 1}


# ── Groups ────────────────────────────────────────────────────────────────────

@app.post("/api/v1/groups", status_code=status.HTTP_201_CREATED)
def create_group(
    request: CreateGroupRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    try:
        group = _SERVICE.create_group(
            tenant_id=tenant_id,
            organization_id=request.organization_id,
            name=request.name,
            code=request.code,
            created_by=actor_id,
            description=request.description,
            metadata=request.metadata,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _to_dict(group)


@app.get("/api/v1/groups")
def list_groups(
    organization_id: Optional[str] = Query(default=None),
    group_status: Optional[str] = Query(default=None, alias="status"),
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    status_filter = GroupStatus(group_status) if group_status else None
    groups = _SERVICE.list_groups(tenant_id=tenant_id, organization_id=organization_id, status=status_filter)
    return {"groups": [_to_dict(g) for g in groups], "total": len(groups)}


@app.get("/api/v1/groups/{group_id}")
def get_group(group_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        return _to_dict(_SERVICE.get_group(tenant_id=tenant_id, group_id=group_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.patch("/api/v1/groups/{group_id}")
def update_group(
    group_id: str,
    request: UpdateGroupRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        return _to_dict(_SERVICE.update_group(
            tenant_id=tenant_id,
            group_id=group_id,
            name=request.name,
            description=request.description,
            metadata=request.metadata,
        ))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@app.post("/api/v1/groups/{group_id}:activate")
def activate_group(group_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        return _to_dict(_SERVICE.activate_group(tenant_id=tenant_id, group_id=group_id))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@app.post("/api/v1/groups/{group_id}:deactivate")
def deactivate_group(group_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        return _to_dict(_SERVICE.deactivate_group(tenant_id=tenant_id, group_id=group_id))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@app.post("/api/v1/groups/{group_id}:archive")
def archive_group(group_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        return _to_dict(_SERVICE.archive_group(tenant_id=tenant_id, group_id=group_id))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc)) from exc


# ── Membership ────────────────────────────────────────────────────────────────

@app.post("/api/v1/groups/{group_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(
    group_id: str,
    request: AddMemberRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    try:
        return _to_dict(_SERVICE.add_member(
            tenant_id=tenant_id,
            group_id=group_id,
            user_id=request.user_id,
            role=request.role,
            added_by=actor_id,
        ))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@app.get("/api/v1/groups/{group_id}/members")
def list_members(group_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        members = _SERVICE.list_members(tenant_id=tenant_id, group_id=group_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"members": [_to_dict(m) for m in members], "total": len(members)}


@app.delete("/api/v1/groups/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(group_id: str, user_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> Response:
    tenant_id, _ = ctx
    try:
        _SERVICE.remove_member(tenant_id=tenant_id, group_id=group_id, user_id=user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Learning assignments ──────────────────────────────────────────────────────

@app.post("/api/v1/groups/{group_id}/assignments", status_code=status.HTTP_201_CREATED)
def assign_learning(
    group_id: str,
    request: AssignLearningRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    try:
        return _to_dict(_SERVICE.assign_learning(
            tenant_id=tenant_id,
            group_id=group_id,
            assignment_type=request.assignment_type,
            learning_object_id=request.learning_object_id,
            target=request.target,
            assigned_by=actor_id,
            due_at=request.due_at,
            metadata=request.metadata,
        ))
    except (NotFoundError, ValidationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@app.get("/api/v1/groups/{group_id}/assignments")
def list_assignments(group_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        assignments = _SERVICE.list_assignments(tenant_id=tenant_id, group_id=group_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"assignments": [_to_dict(a) for a in assignments], "total": len(assignments)}


# B02-006: spec uses singular base path /api/v1/group — alias all routes for compatibility
# B02-007: spec uses slash lifecycle paths /{id}/activate — alias colon-style routes
app.add_api_route("/api/v1/group", create_group, methods=["POST"], status_code=status.HTTP_201_CREATED)
app.add_api_route("/api/v1/group", list_groups, methods=["GET"])
app.add_api_route("/api/v1/group/{group_id}", get_group, methods=["GET"])
app.add_api_route("/api/v1/group/{group_id}", update_group, methods=["PATCH"])
app.add_api_route("/api/v1/group/{group_id}/activate", activate_group, methods=["POST"])
app.add_api_route("/api/v1/group/{group_id}/deactivate", deactivate_group, methods=["POST"])
app.add_api_route("/api/v1/group/{group_id}/archive", archive_group, methods=["POST"])
app.add_api_route("/api/v1/group/{group_id}/members", add_member, methods=["POST"], status_code=status.HTTP_201_CREATED)
app.add_api_route("/api/v1/group/{group_id}/members", list_members, methods=["GET"])
app.add_api_route("/api/v1/group/{group_id}/members/{user_id}", remove_member, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT)
app.add_api_route("/api/v1/group/{group_id}/assignments", assign_learning, methods=["POST"], status_code=status.HTTP_201_CREATED)
app.add_api_route("/api/v1/group/{group_id}/assignments", list_assignments, methods=["GET"])
# slash-style aliases on /groups path
app.add_api_route("/api/v1/groups/{group_id}/activate", activate_group, methods=["POST"])
app.add_api_route("/api/v1/groups/{group_id}/deactivate", deactivate_group, methods=["POST"])
app.add_api_route("/api/v1/groups/{group_id}/archive", archive_group, methods=["POST"])
