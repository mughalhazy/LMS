from __future__ import annotations

from backend.services.shared.models.tenant import TenantContract
from backend.services.shared.utils.entitlements import resolve_capabilities


def is_capability_enabled(tenant: TenantContract, capability: str) -> bool:
    return capability in resolve_capabilities(tenant).capabilities
