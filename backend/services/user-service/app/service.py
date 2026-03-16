from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from fastapi import HTTPException

from .models import (
    AuditLogEntry,
    IdentityAttributes,
    RoleLink,
    UserAggregate,
    UserLifecycleEvent,
    UserLifecycleEventType,
    UserProfile,
    UserStatus,
)
from .schemas import CreateUserRequest, RoleLinkRequest, RoleUnlinkRequest, UpdateStatusRequest, UpdateUserRequest
from .store import AuditLogStore, InMemoryAuditLogStore, InMemoryUserStore, UserStore


class EventPublisher(Protocol):
    def publish(self, event: UserLifecycleEvent) -> None: ...


class ObservabilityHook(Protocol):
    def increment(self, name: str) -> None: ...


@dataclass
class InMemoryEventPublisher(EventPublisher):
    events: list[UserLifecycleEvent] = field(default_factory=list)

    def publish(self, event: UserLifecycleEvent) -> None:
        self.events.append(event)


@dataclass
class InMemoryObservability(ObservabilityHook):
    counters: dict[str, int] = field(default_factory=dict)

    def increment(self, name: str) -> None:
        self.counters[name] = self.counters.get(name, 0) + 1


class UserService:
    def __init__(
        self,
        user_store: UserStore | None = None,
        audit_store: AuditLogStore | None = None,
        event_publisher: EventPublisher | None = None,
        observability: ObservabilityHook | None = None,
    ) -> None:
        self.user_store = user_store or InMemoryUserStore()
        self.audit_store = audit_store or InMemoryAuditLogStore()
        self.event_publisher = event_publisher or InMemoryEventPublisher()
        self.observability = observability or InMemoryObservability()

    def _assert_tenant(self, context_tenant_id: str, target_tenant_id: str) -> None:
        if context_tenant_id != target_tenant_id:
            raise HTTPException(status_code=403, detail="cross_tenant_access_denied")

    def _load_user(self, tenant_id: str, user_id: str) -> UserAggregate:
        user = self.user_store.get(tenant_id, user_id)
        if user is None or user.deleted_at is not None:
            raise HTTPException(status_code=404, detail="user_not_found")
        return user

    def _emit(self, event_type: UserLifecycleEventType, user: UserAggregate, actor_id: str, payload: dict[str, Any]) -> None:
        event = UserLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            actor_id=actor_id,
            payload=payload,
        )
        self.event_publisher.publish(event)
        self.observability.increment(f"event.{event_type.value}")

    def _audit(self, user: UserAggregate, action: str, actor_id: str, changes: dict[str, Any]) -> None:
        self.audit_store.append(
            AuditLogEntry(
                audit_id=str(uuid4()),
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                action=action,
                actor_id=actor_id,
                changes=changes,
            )
        )
        self.observability.increment(f"audit.{action}")

    def create_user(self, request: CreateUserRequest, context_tenant_id: str) -> UserAggregate:
        self._assert_tenant(context_tenant_id, request.tenant_id)
        user = UserAggregate(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            status=UserStatus.PROVISIONED,
            identity=IdentityAttributes(
                email=request.email,
                username=request.username,
                external_subject_id=request.external_subject_id,
            ),
            profile=UserProfile(
                first_name=request.first_name,
                last_name=request.last_name,
                display_name=request.display_name,
                locale=request.locale,
                timezone=request.timezone,
                title=request.title,
                department=request.department,
            ),
        )
        try:
            self.user_store.create(user)
        except ValueError:
            raise HTTPException(status_code=409, detail="user_exists")
        self._audit(user, "user.created", request.actor_id, {"status": user.status.value})
        self._emit(UserLifecycleEventType.CREATED, user, request.actor_id, {"status": user.status.value})
        self.observability.increment("user.create")
        return user

    def list_users(self, tenant_id: str, context_tenant_id: str) -> list[UserAggregate]:
        self._assert_tenant(context_tenant_id, tenant_id)
        self.observability.increment("user.list")
        return [u for u in self.user_store.list(tenant_id) if u.deleted_at is None]

    def get_user(self, tenant_id: str, user_id: str, context_tenant_id: str) -> UserAggregate:
        self._assert_tenant(context_tenant_id, tenant_id)
        self.observability.increment("user.get")
        return self._load_user(tenant_id, user_id)

    def update_user(self, tenant_id: str, user_id: str, request: UpdateUserRequest, context_tenant_id: str) -> UserAggregate:
        self._assert_tenant(context_tenant_id, tenant_id)
        self._assert_tenant(context_tenant_id, request.tenant_id)
        user = self._load_user(tenant_id, user_id)

        changed: dict[str, Any] = {}
        for field in ("email", "username"):
            value = getattr(request, field)
            if value is not None:
                setattr(user.identity, field, value)
                changed[f"identity.{field}"] = value

        profile_fields = (
            "first_name",
            "last_name",
            "display_name",
            "locale",
            "timezone",
            "title",
            "department",
            "phone_number",
            "avatar_url",
        )
        for field in profile_fields:
            value = getattr(request, field)
            if value is not None:
                setattr(user.profile, field, value)
                changed[f"profile.{field}"] = value

        user.version += 1
        user.updated_at = datetime.now(timezone.utc)
        self.user_store.update(user)
        self._audit(user, "user.profile.updated", request.actor_id, changed)
        self._emit(UserLifecycleEventType.PROFILE_UPDATED, user, request.actor_id, changed)
        self.observability.increment("user.update")
        return user

    def update_status(self, tenant_id: str, user_id: str, request: UpdateStatusRequest, context_tenant_id: str) -> UserAggregate:
        self._assert_tenant(context_tenant_id, tenant_id)
        self._assert_tenant(context_tenant_id, request.tenant_id)
        user = self._load_user(tenant_id, user_id)
        prev_status = user.status
        user.status = request.status
        user.version += 1
        user.updated_at = datetime.now(timezone.utc)
        self.user_store.update(user)
        payload = {"from": prev_status.value, "to": user.status.value, "reason": request.reason}
        self._audit(user, "user.status.updated", request.actor_id, payload)
        self._emit(UserLifecycleEventType.STATUS_CHANGED, user, request.actor_id, payload)
        self.observability.increment("user.status")
        return user

    def link_role(self, tenant_id: str, user_id: str, request: RoleLinkRequest, context_tenant_id: str) -> UserAggregate:
        self._assert_tenant(context_tenant_id, tenant_id)
        self._assert_tenant(context_tenant_id, request.tenant_id)
        user = self._load_user(tenant_id, user_id)
        if request.role_id not in [link.role_id for link in user.role_links]:
            user.role_links.append(RoleLink(role_id=request.role_id, linked_by=request.actor_id))
            user.version += 1
            self.user_store.update(user)
            payload = {"role_id": request.role_id}
            self._audit(user, "user.role.linked", request.actor_id, payload)
            self._emit(UserLifecycleEventType.ROLE_LINKED, user, request.actor_id, payload)
        self.observability.increment("user.role.link")
        return user

    def unlink_role(self, tenant_id: str, user_id: str, request: RoleUnlinkRequest, context_tenant_id: str) -> UserAggregate:
        self._assert_tenant(context_tenant_id, tenant_id)
        self._assert_tenant(context_tenant_id, request.tenant_id)
        user = self._load_user(tenant_id, user_id)
        before = len(user.role_links)
        user.role_links = [link for link in user.role_links if link.role_id != request.role_id]
        if len(user.role_links) == before:
            raise HTTPException(status_code=404, detail="role_link_not_found")
        user.version += 1
        self.user_store.update(user)
        payload = {"role_id": request.role_id}
        self._audit(user, "user.role.unlinked", request.actor_id, payload)
        self._emit(UserLifecycleEventType.ROLE_UNLINKED, user, request.actor_id, payload)
        self.observability.increment("user.role.unlink")
        return user

    def delete_user(self, tenant_id: str, user_id: str, actor_id: str, context_tenant_id: str) -> None:
        self._assert_tenant(context_tenant_id, tenant_id)
        user = self._load_user(tenant_id, user_id)
        user.deleted_at = datetime.now(timezone.utc)
        user.status = UserStatus.DEACTIVATED
        user.version += 1
        self.user_store.update(user)
        self._audit(user, "user.deleted", actor_id, {"deleted": True})
        self._emit(UserLifecycleEventType.DELETED, user, actor_id, {"deleted": True})
        self.observability.increment("user.delete")

    def list_audit_entries(self, tenant_id: str, user_id: str, context_tenant_id: str) -> list[AuditLogEntry]:
        self._assert_tenant(context_tenant_id, tenant_id)
        self._load_user(tenant_id, user_id)
        return self.audit_store.list_for_user(tenant_id, user_id)

    def list_emitted_events(self, tenant_id: str) -> list[UserLifecycleEvent]:
        events = getattr(self.event_publisher, "events", [])
        return [event for event in events if event.tenant_id == tenant_id]
