from __future__ import annotations

from fastapi import Header, HTTPException, Query


def tenant_context(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    tenant_id: str | None = Query(default=None),
) -> str:
    resolved = x_tenant_id or tenant_id
    if not resolved:
        raise HTTPException(status_code=400, detail="tenant context is required")
    return resolved
