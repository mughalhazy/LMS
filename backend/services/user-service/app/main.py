from fastapi import Depends, FastAPI, Query

from .models import AccountStatus
from .schemas import (
    ActivateUserRequest,
    ChangeStatusRequest,
    CreateUserRequest,
    IdentityLinksResponse,
    LockUnlockRequest,
    ManagePreferencesRequest,
    MapIdentityRequest,
    PreferencesResponse,
    TerminateReinstateRequest,
    TimelineResponse,
    UnmapIdentityRequest,
    UpdateProfileRequest,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from .security import AuthorizationContext, require_roles
from .service import UserService

app = FastAPI(title="User Management Service", version="1.0.0", dependencies=[Depends(require_jwt)])
service = UserService()

apply_security_headers(app)


@app.post("/users", response_model=UserResponse)
def create_user_account(
    request: CreateUserRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    return UserResponse(user=service.create_user(request, actor))


@app.get("/users", response_model=UserListResponse)
def list_users(
    tenant_id: str = Query(...),
    status: AccountStatus | None = Query(default=None),
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    return UserListResponse(items=service.list_users(tenant_id=tenant_id, actor=actor, status=status))


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    tenant_id: str = Query(...),
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin", "instructor", "learner")),
):
    return UserResponse(user=service.get_user(tenant_id=tenant_id, user_id=user_id, actor=actor))


@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, request: UpdateUserRequest):
    return UserResponse(user=service.update_user(user_id=user_id, req=request))


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, tenant_id: str = Query(...)):
    service.delete_user(tenant_id=tenant_id, user_id=user_id)


@app.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user_account(
    user_id: str,
    request: ActivateUserRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    return UserResponse(user=service.activate_user(user_id=user_id, req=request, actor=actor))


@app.patch("/users/{user_id}/profile", response_model=UserResponse)
def update_user_profile(
    user_id: str,
    request: UpdateProfileRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin", "instructor", "learner")),
):
    return UserResponse(user=service.update_profile(user_id=user_id, req=request, actor=actor))


@app.put("/users/{user_id}/preferences", response_model=PreferencesResponse)
def manage_profile_preferences(
    user_id: str,
    request: ManagePreferencesRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin", "instructor", "learner")),
):
    return PreferencesResponse(preferences=service.manage_preferences(user_id=user_id, req=request, actor=actor))


@app.post("/users/{user_id}/status", response_model=UserResponse)
def change_account_status(
    user_id: str,
    request: ChangeStatusRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    return UserResponse(user=service.change_account_status(user_id=user_id, req=request, actor=actor))


@app.post("/users/{user_id}/lock", response_model=UserResponse)
def lock_or_unlock_account(
    user_id: str,
    request: LockUnlockRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    return UserResponse(user=service.lock_or_unlock(user_id=user_id, req=request, actor=actor))


@app.post("/users/{user_id}/lifecycle", response_model=UserResponse)
def terminate_or_reinstate_user(
    user_id: str,
    request: TerminateReinstateRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    return UserResponse(user=service.terminate_or_reinstate(user_id=user_id, req=request, actor=actor))


@app.post("/users/{user_id}/identity-links", response_model=IdentityLinksResponse)
def map_external_identity(
    user_id: str,
    request: MapIdentityRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    return IdentityLinksResponse(identity_links=service.map_external_identity(user_id=user_id, req=request, actor=actor))


@app.delete("/users/{user_id}/identity-links", response_model=IdentityLinksResponse)
def unmap_external_identity(
    user_id: str,
    request: UnmapIdentityRequest,
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    return IdentityLinksResponse(identity_links=service.unmap_external_identity(user_id=user_id, req=request, actor=actor))


@app.get("/users/{user_id}/identity-links", response_model=IdentityLinksResponse)
def get_user_identity_links(
    user_id: str,
    tenant_id: str = Query(...),
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin", "instructor", "learner")),
):
    return IdentityLinksResponse(identity_links=service.get_identity_links(tenant_id=tenant_id, user_id=user_id, actor=actor))


@app.get("/users/{user_id}/timeline", response_model=TimelineResponse)
def get_user_lifecycle_timeline(
    user_id: str,
    tenant_id: str = Query(...),
    include_audit: bool = Query(default=False),
    actor: AuthorizationContext = Depends(require_roles("platform_admin", "tenant_admin")),
):
    _ = include_audit
    return TimelineResponse(lifecycle_timeline=service.get_lifecycle_timeline(tenant_id=tenant_id, user_id=user_id, actor=actor))
