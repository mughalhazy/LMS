from __future__ import annotations

from app.models import Tenant, TenantNamespace
from app.store import TenantStore


class InMemoryTenantStore(TenantStore):
    """Reference store for local runs/tests; production store should implement TenantStore."""

    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}
        self._namespace_by_tenant: dict[str, TenantNamespace] = {}

    def add(self, tenant: Tenant, namespace: TenantNamespace) -> None:
        self._tenants[tenant.tenant_id] = tenant
        self._namespace_by_tenant[tenant.tenant_id] = namespace

    def update(self, tenant: Tenant) -> None:
        self._tenants[tenant.tenant_id] = tenant

    def get(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def by_code(self, tenant_code: str) -> Tenant | None:
        return next((t for t in self._tenants.values() if t.tenant_code == tenant_code), None)

    def by_domain(self, primary_domain: str) -> Tenant | None:
        return next((t for t in self._tenants.values() if t.primary_domain == primary_domain), None)

    def namespace_for(self, tenant_id: str) -> TenantNamespace | None:
        return self._namespace_by_tenant.get(tenant_id)
