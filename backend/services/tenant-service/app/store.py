from __future__ import annotations

from typing import Protocol

from app.models import Tenant, TenantNamespace


class TenantStore(Protocol):
    def add(self, tenant: Tenant, namespace: TenantNamespace) -> None: ...

    def update(self, tenant: Tenant) -> None: ...

    def get(self, tenant_id: str) -> Tenant | None: ...

    def by_code(self, tenant_code: str) -> Tenant | None: ...


    def namespace_for(self, tenant_id: str) -> TenantNamespace | None: ...
