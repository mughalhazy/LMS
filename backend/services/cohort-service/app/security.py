from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException
from fastapi.responses import JSONResponse


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str


def require_jwt() -> None:
    """Placeholder JWT guard for consistency with other services."""
    return None


def get_tenant_context(x_tenant_id: str = Header(..., alias="X-Tenant-ID")) -> TenantContext:
    tenant_id = x_tenant_id.strip()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    return TenantContext(tenant_id=tenant_id)


def apply_security_headers(app) -> None:  # type: ignore[no-untyped-def]
    @app.middleware("http")
    async def add_security_headers(request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


async def tenant_error_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
