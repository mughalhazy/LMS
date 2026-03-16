"""Storage contracts and an in-memory adapter for user-service.

The service treats Rails User as source-of-truth identity and stores only service-owned profile projection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Protocol

from .models import AuditLogEntry, UserAggregate


class UserStore(Protocol):
    def create(self, user: UserAggregate) -> UserAggregate: ...

    def update(self, user: UserAggregate) -> UserAggregate: ...

    def get(self, tenant_id: str, user_id: str) -> UserAggregate | None: ...

    def list(self, tenant_id: str) -> list[UserAggregate]: ...


class AuditLogStore(Protocol):
    def append(self, entry: AuditLogEntry) -> None: ...

    def list_for_user(self, tenant_id: str, user_id: str) -> list[AuditLogEntry]: ...


@dataclass
class InMemoryUserStore(UserStore):
    _items: dict[tuple[str, str], UserAggregate] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)

    def create(self, user: UserAggregate) -> UserAggregate:
        key = (user.tenant_id, user.user_id)
        with self._lock:
            if key in self._items:
                raise ValueError("user_exists")
            self._items[key] = user
        return user

    def update(self, user: UserAggregate) -> UserAggregate:
        key = (user.tenant_id, user.user_id)
        with self._lock:
            if key not in self._items:
                raise ValueError("user_not_found")
            self._items[key] = user
        return user

    def get(self, tenant_id: str, user_id: str) -> UserAggregate | None:
        return self._items.get((tenant_id, user_id))

    def list(self, tenant_id: str) -> list[UserAggregate]:
        return [user for (stored_tenant, _), user in self._items.items() if stored_tenant == tenant_id]


@dataclass
class InMemoryAuditLogStore(AuditLogStore):
    _items: list[AuditLogEntry] = field(default_factory=list)

    def append(self, entry: AuditLogEntry) -> None:
        self._items.append(entry)

    def list_for_user(self, tenant_id: str, user_id: str) -> list[AuditLogEntry]:
        return [e for e in self._items if e.tenant_id == tenant_id and e.user_id == user_id]
