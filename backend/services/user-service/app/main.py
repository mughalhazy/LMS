from __future__ import annotations

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Response, status

from .schemas import (
    AuditLogResponse,
    CreateUserRequest,
    EventsResponse,
    HealthResponse,
    IdentityLinkRequest,
    IdentityLinksResponse,
    IdentityUnlinkRequest,
    LifecycleCommand,
    MetricsResponse,
    RoleLinkRequest,
    RoleUnlinkRequest,
    UpdateStatusRequest,
    UpdateUserRequest,
    UserListResponse,
    UserPreferencesRequest,
    UserPreferencesResponse,
    UserResponse,
)
from .service import InMemoryObservability, UserService
from .store_db import SQLiteAuditLogStore, SQLiteUserStore

app = FastAPI(title="Enterprise LMS V2 User Service", version="2.0.0")


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()

api_v1 = APIRouter(prefix="/api/v1", tags=["users"])

service = UserService(
    user_store=SQLiteUserStore(),
    audit_store=SQLiteAuditLogStore(),
    observability=InMemoryObservability(),
)


def tenant_context(x_tenant_id: str = Header(..., alias="X-Tenant-Id")) -> str:
    if not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="tenant_context_missing")
    return x_tenant_id


@api_v1.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUserRequest, context_tenant_id: str = Depends(tenant_context)) -> UserResponse:
    return UserResponse(user=service.create_user(request, context_tenant_id=context_tenant_id))


@api_v1.get("/users", response_model=UserListResponse)
def list_users(tenant_id: str = Query(...), context_tenant_id: str = Depends(tenant_context)) -> UserListResponse:
    return UserListResponse(users=service.list_users(tenant_id=tenant_id, context_tenant_id=context_tenant_id))


@api_v1.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, tenant_id: str = Query(...), context_tenant_id: str = Depends(tenant_context)) -> UserResponse:
    return UserResponse(user=service.get_user(tenant_id=tenant_id, user_id=user_id, context_tenant_id=context_tenant_id))


@api_v1.put("/users/{user_id}", response_model=UserResponse)
@api_v1.patch("/users/{user_id}", response_model=UserResponse)  # AUD-004: spec §4 uses PATCH
def update_user(
    user_id: str,
    request: UpdateUserRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    return UserResponse(
        user=service.update_user(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id)
    )


@api_v1.patch("/users/{user_id}/status", response_model=UserResponse)
def update_status(
    user_id: str,
    request: UpdateStatusRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    return UserResponse(
        user=service.update_status(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id)
    )


@api_v1.post("/users/{user_id}/role-links", response_model=UserResponse)
def link_role(
    user_id: str,
    request: RoleLinkRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    return UserResponse(
        user=service.link_role(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id)
    )


@api_v1.delete("/users/{user_id}/role-links", response_model=UserResponse)
def unlink_role(
    user_id: str,
    request: RoleUnlinkRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    return UserResponse(
        user=service.unlink_role(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id)
    )


@api_v1.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    tenant_id: str = Query(...),
    actor_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> Response:
    service.delete_user(tenant_id=tenant_id, user_id=user_id, actor_id=actor_id, context_tenant_id=context_tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_v1.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: str,
    tenant_id: str = Query(...),
    actor_id: str = Query(default="system"),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    """Spec §4 — activate user account lifecycle state."""
    from .models import UserStatus
    from .schemas import UpdateStatusRequest
    request = UpdateStatusRequest(tenant_id=tenant_id, actor_id=actor_id, status=UserStatus.ACTIVE, reason="user_activated")
    return UserResponse(user=service.update_status(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id))


@api_v1.patch("/users/{user_id}/profile", response_model=UserResponse)
def patch_user_profile(
    user_id: str,
    request: UpdateUserRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    """Spec §4 — update profile fields with optimistic concurrency."""
    return UserResponse(user=service.update_user(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id))


@api_v1.post("/users/{user_id}/status", response_model=UserResponse)
def update_status_post(
    user_id: str,
    request: UpdateStatusRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    """Spec §4 — POST alias for status transition (spec uses POST, code uses PATCH)."""
    return UserResponse(user=service.update_status(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id))


@api_v1.post("/users/{user_id}/lock", response_model=UserResponse)
def lock_user(
    user_id: str,
    tenant_id: str = Query(...),
    actor_id: str = Query(default="system"),
    reason: str = Query(default="admin_lock"),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    """Spec §4 — lock user account."""
    from .models import UserStatus
    from .schemas import UpdateStatusRequest
    request = UpdateStatusRequest(tenant_id=tenant_id, actor_id=actor_id, status=UserStatus.LOCKED, reason=reason)
    return UserResponse(user=service.update_status(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id))


@api_v1.get("/users/{user_id}/timeline", response_model=AuditLogResponse)
def get_user_timeline(
    user_id: str,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> AuditLogResponse:
    """Spec §4 — retrieve lifecycle timeline (audit-backed)."""
    return AuditLogResponse(entries=service.list_audit_entries(tenant_id=tenant_id, user_id=user_id, context_tenant_id=context_tenant_id))


@api_v1.get("/users/{user_id}/audit", response_model=AuditLogResponse)
def list_user_audit(
    user_id: str,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> AuditLogResponse:
    return AuditLogResponse(entries=service.list_audit_entries(tenant_id=tenant_id, user_id=user_id, context_tenant_id=context_tenant_id))


# ── Spec §4 — Identity links (FA-011 remaining: POST/DELETE/GET) ─────────────

@api_v1.post("/users/{user_id}/identity-links", response_model=UserResponse, status_code=201)
def create_identity_link(
    user_id: str,
    request: IdentityLinkRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    return UserResponse(user=service.create_identity_link(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id))


@api_v1.delete("/users/{user_id}/identity-links", response_model=UserResponse)
def delete_identity_link(
    user_id: str,
    request: IdentityUnlinkRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    return UserResponse(user=service.delete_identity_link(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id))


@api_v1.get("/users/{user_id}/identity-links", response_model=IdentityLinksResponse)
def list_identity_links(
    user_id: str,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> IdentityLinksResponse:
    return IdentityLinksResponse(identity_links=service.list_identity_links(tenant_id=tenant_id, user_id=user_id, context_tenant_id=context_tenant_id))


# ── Spec §4 — Preferences (PUT replaces full document) ───────────────────────

@api_v1.put("/users/{user_id}/preferences", response_model=UserPreferencesResponse)
def update_preferences(
    user_id: str,
    request: UserPreferencesRequest,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserPreferencesResponse:
    return UserPreferencesResponse(preferences=service.update_preferences(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id))


# ── Spec §4 — Lifecycle command (terminate / reinstate) ──────────────────────

@api_v1.post("/users/{user_id}/lifecycle", response_model=UserResponse)
def lifecycle_command(
    user_id: str,
    request: LifecycleCommand,
    tenant_id: str = Query(...),
    context_tenant_id: str = Depends(tenant_context),
) -> UserResponse:
    return UserResponse(user=service.lifecycle_command(tenant_id=tenant_id, user_id=user_id, request=request, context_tenant_id=context_tenant_id))


@api_v1.get("/events/users", response_model=EventsResponse)
def list_user_events(tenant_id: str = Query(...), context_tenant_id: str = Depends(tenant_context)) -> EventsResponse:
    if context_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="cross_tenant_access_denied")
    return EventsResponse(events=service.list_emitted_events(tenant_id=tenant_id))


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="user-service")


@app.get("/metrics", response_model=MetricsResponse, tags=["health"])
def metrics() -> MetricsResponse:
    obs = service.observability
    counters = getattr(obs, "counters", {})
    return MetricsResponse(service="user-service", counters=counters, attributes={"api_version": "v1"})


app.include_router(api_v1)
