from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from fastapi import HTTPException

from .models import AccountStatus, IdentityMapping, LifecycleEvent, LifecycleEventType, User, UserPreferences
from .security import AuthorizationContext
from .schemas import (
    ActivateUserRequest,
    ChangeStatusRequest,
    CreateUserRequest,
    LockUnlockRequest,
    ManagePreferencesRequest,
    MapIdentityRequest,
    TerminateReinstateRequest,
    UnmapIdentityRequest,
    UpdateProfileRequest,
    UpdateUserRequest,
)


class UserService:
    def __init__(self) -> None:
        self.users: Dict[str, User] = {}

    def _get_tenant_user(self, tenant_id: str, user_id: str) -> User:
        user = self.users.get(user_id)
        if not user or user.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="User not found in tenant")
        return user

    def _add_event(self, user: User, event_type: LifecycleEventType, actor: str, detail: Dict[str, str]) -> None:
        user.lifecycle_timeline.append(LifecycleEvent(event_type=event_type, actor=actor, detail=detail))

    def _enforce_permission(self, actor: AuthorizationContext, required_permission: str) -> None:
        if actor.role == "platform_admin":
            return
        if required_permission not in actor.permissions:
            raise HTTPException(status_code=403, detail=f"Missing permission: {required_permission}")

    def _enforce_tenant(self, actor: AuthorizationContext, tenant_id: str) -> None:
        if actor.role != "platform_admin" and actor.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Cross-tenant access is not allowed")

    def _enforce_self_or_admin(self, actor: AuthorizationContext, user_id: str) -> None:
        if actor.role in {"platform_admin", "tenant_admin"}:
            return
        if actor.principal_id != user_id:
            raise HTTPException(status_code=403, detail="Only self-service access is allowed")

    def create_user(self, req: CreateUserRequest, actor: AuthorizationContext) -> User:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_permission(actor, "org.user.invite")
        user = User(
            tenant_id=req.tenant_id,
            email=req.email,
            username=req.username,
            role_set=req.role_set,
            auth_provider=req.auth_provider,
            external_subject_id=req.external_subject_id,
            profile={"first_name": req.first_name, "last_name": req.last_name},
            status=AccountStatus.ACTIVE if req.start_active else AccountStatus.PENDING_ACTIVATION,
            created_by=req.created_by,
        )
        self._add_event(
            user,
            LifecycleEventType.CREATED,
            req.created_by,
            {"status": user.status.value, "username": user.username},
        )
        self.users[user.user_id] = user
        return user

    def list_users(self, tenant_id: str, actor: AuthorizationContext, status: AccountStatus | None = None) -> List[User]:
        self._enforce_tenant(actor, tenant_id)
        self._enforce_permission(actor, "org.user.view")
        items = [u for u in self.users.values() if u.tenant_id == tenant_id]
        if status:
            items = [u for u in items if u.status == status]
        return items

    def get_user(self, tenant_id: str, user_id: str, actor: AuthorizationContext) -> User:
        self._enforce_tenant(actor, tenant_id)
        self._enforce_self_or_admin(actor, user_id)
        return self._get_tenant_user(tenant_id, user_id)

    def activate_user(self, user_id: str, req: ActivateUserRequest, actor: AuthorizationContext) -> User:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_permission(actor, "org.user.disable")
        user = self._get_tenant_user(req.tenant_id, user_id)
        if user.status != AccountStatus.PENDING_ACTIVATION:
            raise HTTPException(status_code=409, detail="Only pending users can be activated")
        if not req.activation_token and not req.admin_override_reason:
            raise HTTPException(status_code=400, detail="Activation token or admin override reason required")

        user.status = AccountStatus.ACTIVE
        user.activated_at = datetime.now(timezone.utc)
        self._add_event(user, LifecycleEventType.ACTIVATED, req.activated_by, {"status": user.status.value})
        return user

    def update_profile(self, user_id: str, req: UpdateProfileRequest, actor: AuthorizationContext) -> User:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_self_or_admin(actor, user_id)
        user = self._get_tenant_user(req.tenant_id, user_id)
        fields = req.model_dump(exclude_none=True)
        fields.pop("tenant_id", None)
        actor = fields.pop("updated_by")
        for key, value in fields.items():
            setattr(user.profile, key, value)
        user.profile_version += 1
        self._add_event(user, LifecycleEventType.PROFILE_UPDATED, actor, {"version": str(user.profile_version)})
        return user

    def manage_preferences(self, user_id: str, req: ManagePreferencesRequest, actor: AuthorizationContext) -> UserPreferences:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_self_or_admin(actor, user_id)
        user = self._get_tenant_user(req.tenant_id, user_id)
        user.preferences = UserPreferences(
            notification_preferences=req.notification_preferences,
            accessibility_preferences=req.accessibility_preferences,
            language_preference=req.language_preference,
        )
        self._add_event(
            user,
            LifecycleEventType.PREFERENCES_UPDATED,
            req.updated_by,
            {"language": req.language_preference or ""},
        )
        return user.preferences

    def change_account_status(self, user_id: str, req: ChangeStatusRequest, actor: AuthorizationContext) -> User:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_permission(actor, "org.user.disable")
        user = self._get_tenant_user(req.tenant_id, user_id)
        if user.status == AccountStatus.TERMINATED and req.target_status != AccountStatus.ACTIVE:
            raise HTTPException(status_code=409, detail="Terminated users can only be reinstated to active")

        user.status = req.target_status
        self._add_event(
            user,
            LifecycleEventType.STATUS_CHANGED,
            req.changed_by,
            {"reason_code": req.reason_code, "target_status": req.target_status.value},
        )
        return user

    def lock_or_unlock(self, user_id: str, req: LockUnlockRequest, actor: AuthorizationContext) -> User:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_permission(actor, "org.user.disable")
        user = self._get_tenant_user(req.tenant_id, user_id)
        if req.action not in {"lock", "unlock"}:
            raise HTTPException(status_code=400, detail="Invalid action")

        user.status = AccountStatus.LOCKED if req.action == "lock" else AccountStatus.ACTIVE
        self._add_event(
            user,
            LifecycleEventType.STATUS_CHANGED,
            req.performed_by,
            {"action": req.action, "reason_code": req.reason_code},
        )
        return user

    def terminate_or_reinstate(self, user_id: str, req: TerminateReinstateRequest, actor: AuthorizationContext) -> User:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_permission(actor, "org.user.disable")
        user = self._get_tenant_user(req.tenant_id, user_id)
        if req.action not in {"terminate", "reinstate"}:
            raise HTTPException(status_code=400, detail="Invalid action")

        user.status = AccountStatus.TERMINATED if req.action == "terminate" else AccountStatus.ACTIVE
        self._add_event(
            user,
            LifecycleEventType.STATUS_CHANGED,
            req.performed_by,
            {
                "action": req.action,
                "data_retention_policy_id": req.data_retention_policy_id or "",
            },
        )
        return user

    def map_external_identity(self, user_id: str, req: MapIdentityRequest, actor: AuthorizationContext) -> List[IdentityMapping]:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_permission(actor, "org.role.assign")
        user = self._get_tenant_user(req.tenant_id, user_id)

        for existing_user in self.users.values():
            if existing_user.tenant_id != req.tenant_id:
                continue
            for mapping in existing_user.identity_links:
                if (
                    mapping.identity_provider == req.identity_provider
                    and mapping.external_subject_id == req.external_subject_id
                    and existing_user.user_id != user.user_id
                ):
                    raise HTTPException(status_code=409, detail="Identity mapping already used by another user")

        mapping = next(
            (
                link
                for link in user.identity_links
                if link.identity_provider == req.identity_provider
                and link.external_subject_id == req.external_subject_id
            ),
            None,
        )

        if mapping:
            mapping.external_username = req.external_username
            mapping.mapping_attributes = req.mapping_attributes
            mapping.mapped_by = req.mapped_by
            mapping.mapped_at = datetime.now(timezone.utc)
        else:
            user.identity_links.append(
                IdentityMapping(
                    identity_provider=req.identity_provider,
                    external_subject_id=req.external_subject_id,
                    external_username=req.external_username,
                    mapping_attributes=req.mapping_attributes,
                    mapped_by=req.mapped_by,
                )
            )

        self._add_event(
            user,
            LifecycleEventType.IDENTITY_MAPPED,
            req.mapped_by,
            {"provider": req.identity_provider, "subject": req.external_subject_id},
        )
        return user.identity_links

    def unmap_external_identity(self, user_id: str, req: UnmapIdentityRequest, actor: AuthorizationContext) -> List[IdentityMapping]:
        self._enforce_tenant(actor, req.tenant_id)
        self._enforce_permission(actor, "org.role.assign")
        user = self._get_tenant_user(req.tenant_id, user_id)
        before = len(user.identity_links)
        user.identity_links = [
            link
            for link in user.identity_links
            if not (
                link.identity_provider == req.identity_provider
                and link.external_subject_id == req.external_subject_id
            )
        ]
        if before == len(user.identity_links):
            raise HTTPException(status_code=404, detail="Identity mapping not found")

        self._add_event(
            user,
            LifecycleEventType.IDENTITY_UNMAPPED,
            req.unmapped_by,
            {"provider": req.identity_provider, "subject": req.external_subject_id, "reason": req.reason},
        )
        return user.identity_links

    def get_identity_links(self, tenant_id: str, user_id: str, actor: AuthorizationContext) -> List[IdentityMapping]:
        self._enforce_tenant(actor, tenant_id)
        self._enforce_self_or_admin(actor, user_id)
        return self._get_tenant_user(tenant_id, user_id).identity_links

    def get_lifecycle_timeline(self, tenant_id: str, user_id: str, actor: AuthorizationContext) -> List[LifecycleEvent]:
        self._enforce_tenant(actor, tenant_id)
        self._enforce_permission(actor, "org.user.view")
        return self._get_tenant_user(tenant_id, user_id).lifecycle_timeline
