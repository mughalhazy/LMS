from __future__ import annotations

from fastapi import HTTPException, Request, status


class TenantContextMiddleware:
    """Adds tenant context for versioned API routes and blocks missing headers on tenant-scoped requests."""

    TENANT_SCOPED_WRITE_PREFIXES = (
        "/api/v1/tenants/",
    )

    async def __call__(self, request: Request, call_next):
        tenant_header = request.headers.get("x-tenant-id")
        request.state.tenant_id = tenant_header

        is_tenant_scoped = request.url.path.startswith(self.TENANT_SCOPED_WRITE_PREFIXES)
        is_mutation = request.method in {"POST", "PUT", "PATCH", "DELETE"}
        if is_tenant_scoped and is_mutation and request.url.path.count("/") > 4 and not tenant_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "tenant_context_missing", "detail": "x-tenant-id header is required"},
            )

        return await call_next(request)
