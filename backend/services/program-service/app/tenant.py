from __future__ import annotations

from fastapi import Header, HTTPException, status


def tenant_context(x_tenant_id: str = Header(..., alias="X-Tenant-Id")) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_context_missing")
    return x_tenant_id
