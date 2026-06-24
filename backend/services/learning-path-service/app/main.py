"""Service entrypoint — learning-path-service REST API."""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import Response

from .security import apply_security_headers, require_jwt

# Add service root so src/ is importable as a package (preserves relative imports in src/)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.models import CompletionRules, ElectiveGroup, PathEdge, PathNode  # noqa: E402
from .service import LearningPathManagementService, NotFoundError, ValidationError  # noqa: E402
from .schemas import (  # noqa: E402
    AssignPathRequest,
    ConfigureCompletionRulesRequest,
    CreateElectiveGroupRequest,
    CreateLearningPathRequest,
    EvaluateCompletionRequest,
    PublishPathRequest,
    SetEdgesRequest,
    SetNodesRequest,
)

app = FastAPI(title="learning-path-service", version="1.0.0", dependencies=[Depends(require_jwt)])


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

_SERVICE = LearningPathManagementService()


def _tenant_context(
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_actor_id: Annotated[str | None, Header()] = None,
) -> tuple[str, str]:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_tenant_id")
    return x_tenant_id, x_actor_id or "system"


def _to_dict(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return obj


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "learning-path-service"}


@app.get("/metrics")
def metrics() -> dict:
    return {"service": "learning-path-service", "service_up": 1}


# ── Path lifecycle ────────────────────────────────────────────────────────────

@app.post("/api/v1/learning-paths", status_code=status.HTTP_201_CREATED)
def create_learning_path(
    request: CreateLearningPathRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    rules = None
    if request.completion_rules:
        r = request.completion_rules
        rules = CompletionRules(
            mode=r.mode,
            required_plus_n_electives=r.required_plus_n_electives,
            strict_due_date=r.strict_due_date,
            due_date=r.due_date,
            recertification_interval_days=r.recertification_interval_days,
            grace_window_days=r.grace_window_days,
        )
    try:
        path = _SERVICE.create_learning_path(
            tenant_id=tenant_id,
            title=request.title,
            owner_id=request.owner_id,
            description=request.description,
            audience=request.audience,
            completion_rules=rules,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _to_dict(path)


@app.get("/api/v1/learning-paths")
def list_learning_paths(
    status_filter: str | None = Query(default=None, alias="status"),
    owner_id: str | None = Query(default=None),
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    paths = _SERVICE.list_learning_paths(tenant_id=tenant_id, status=status_filter, owner_id=owner_id)
    return {"learning_paths": [_to_dict(p) for p in paths], "total": len(paths)}


@app.get("/api/v1/learning-paths/{path_id}")
def get_learning_path(
    path_id: str,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        return _to_dict(_SERVICE.get_learning_path(tenant_id=tenant_id, path_id=path_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/api/v1/learning-paths/{path_id}:publish")
def publish_learning_path(
    path_id: str,
    request: PublishPathRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    try:
        return _to_dict(
            _SERVICE.publish_learning_path(
                tenant_id=tenant_id,
                path_id=path_id,
                actor_id=actor_id,
                change_reason=request.change_reason,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.post("/api/v1/learning-paths/{path_id}:archive")
def archive_learning_path(
    path_id: str,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    try:
        return _to_dict(_SERVICE.archive_learning_path(tenant_id=tenant_id, path_id=path_id, actor_id=actor_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Completion rules ──────────────────────────────────────────────────────────

@app.put("/api/v1/learning-paths/{path_id}/completion-rules")
def configure_completion_rules(
    path_id: str,
    request: ConfigureCompletionRulesRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    r = request.rules
    rules = CompletionRules(
        mode=r.mode,
        required_plus_n_electives=r.required_plus_n_electives,
        strict_due_date=r.strict_due_date,
        due_date=r.due_date,
        recertification_interval_days=r.recertification_interval_days,
        grace_window_days=r.grace_window_days,
    )
    try:
        return _to_dict(
            _SERVICE.configure_completion_rules(
                tenant_id=tenant_id,
                path_id=path_id,
                rules=rules,
                actor_id=actor_id,
                change_reason=request.change_reason,
            )
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


# ── Nodes and edges ───────────────────────────────────────────────────────────

@app.put("/api/v1/learning-paths/{path_id}/nodes")
def set_nodes(
    path_id: str,
    request: SetNodesRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    nodes = [
        PathNode(
            path_id=path_id,
            node_type=n.node_type,
            ref_id=n.ref_id,
            sequence_index=n.sequence_index,
            is_required=n.is_required,
            min_score=n.min_score,
            estimated_duration_mins=n.estimated_duration_mins,
            elective_group_id=n.elective_group_id,
        )
        for n in request.nodes
    ]
    try:
        result = _SERVICE.set_nodes(tenant_id=tenant_id, path_id=path_id, nodes=nodes, actor_id=actor_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"nodes": [_to_dict(n) for n in result]}


@app.get("/api/v1/learning-paths/{path_id}/nodes")
def get_nodes(
    path_id: str,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        nodes = _SERVICE.get_nodes(tenant_id=tenant_id, path_id=path_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"nodes": [_to_dict(n) for n in nodes]}


@app.put("/api/v1/learning-paths/{path_id}/edges")
def set_edges(
    path_id: str,
    request: SetEdgesRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    edges = [
        PathEdge(
            path_id=path_id,
            from_node_id=e.from_node_id,
            to_node_id=e.to_node_id,
            relation=e.relation,
            condition=e.condition,
        )
        for e in request.edges
    ]
    try:
        result = _SERVICE.set_edges(tenant_id=tenant_id, path_id=path_id, edges=edges, actor_id=actor_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"edges": [_to_dict(e) for e in result]}


@app.get("/api/v1/learning-paths/{path_id}/edges")
def get_edges(
    path_id: str,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        edges = _SERVICE.get_edges(tenant_id=tenant_id, path_id=path_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"edges": [_to_dict(e) for e in edges]}


# ── Assignments ───────────────────────────────────────────────────────────────

@app.post("/api/v1/learning-paths/{path_id}/assignments", status_code=status.HTTP_201_CREATED)
def assign_path(
    path_id: str,
    request: AssignPathRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, actor_id = ctx
    try:
        return _SERVICE.assign_path(
            tenant_id=tenant_id,
            path_id=path_id,
            assignment_type=request.assignment_type,
            target_ref=request.target_ref,
            effective_from=request.effective_from,
            effective_to=request.effective_to,
            assigned_by=request.assigned_by or actor_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@app.get("/api/v1/learning-paths/{path_id}/assignments")
def list_assignments(
    path_id: str,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        scopes = _SERVICE.list_assignments(tenant_id=tenant_id, path_id=path_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"assignments": scopes, "total": len(scopes)}


# ── Completion evaluation ─────────────────────────────────────────────────────

@app.post("/api/v1/learning-paths/{path_id}:evaluate-completion")
def evaluate_completion(
    path_id: str,
    request: EvaluateCompletionRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        progress = _SERVICE.evaluate_completion(
            tenant_id=tenant_id,
            path_id=path_id,
            progress_by_node_id=request.progress_by_node_id,
            completed_at=request.completed_at,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _to_dict(progress)


# ── Audit log ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/learning-paths/{path_id}/audit-log")
def get_audit_log(
    path_id: str,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        entries = _SERVICE.get_audit_log(tenant_id=tenant_id, path_id=path_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"audit_log": entries, "total": len(entries)}


# ── Elective groups (B04-002) ─────────────────────────────────────────────────
# learning-path-spec.md data model defines elective_group entity with CRUD obligations

_ELECTIVE_GROUPS: dict[str, list[ElectiveGroup]] = {}  # path_id → groups (in-memory)


@app.post("/api/v1/learning-paths/{path_id}/elective-groups", status_code=status.HTTP_201_CREATED)
def create_elective_group(
    path_id: str,
    request: CreateElectiveGroupRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    # B04-002: learning-path-spec.md — elective_group entity management
    tenant_id, _ = ctx
    try:
        _SERVICE.get_learning_path(tenant_id=tenant_id, path_id=path_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if request.max_select < request.min_select:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="max_select must be >= min_select")
    group = ElectiveGroup(
        path_id=path_id,
        name=request.name,
        min_select=request.min_select,
        max_select=request.max_select,
        node_ids=list(request.node_ids),
    )
    _ELECTIVE_GROUPS.setdefault(path_id, []).append(group)
    return _to_dict(group)


@app.get("/api/v1/learning-paths/{path_id}/elective-groups")
def list_elective_groups(
    path_id: str,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    # B04-002: learning-path-spec.md — elective_group entity management
    tenant_id, _ = ctx
    try:
        _SERVICE.get_learning_path(tenant_id=tenant_id, path_id=path_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    groups = _ELECTIVE_GROUPS.get(path_id, [])
    return {"elective_groups": [_to_dict(g) for g in groups], "total": len(groups)}
