from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

ALLOWED_ROLES = {"platform_admin", "tenant_admin", "instructor", "learner"}


@dataclass(frozen=True)
class AuthorizationContext:
    principal_id: str
    role: str
    permissions: set[str]
    tenant_id: str


def _parse_permissions(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {perm.strip() for perm in raw.split(",") if perm.strip()}


def get_authorization_context(
    x_principal_id: str = Header(..., alias="X-Principal-Id"),
    x_role: str = Header(..., alias="X-Role"),
    x_permissions: str | None = Header(None, alias="X-Permissions"),
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
) -> AuthorizationContext:
    if x_role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Unsupported role")
    return AuthorizationContext(
        principal_id=x_principal_id,
        role=x_role,
        permissions=_parse_permissions(x_permissions),
        tenant_id=x_tenant_id,
    )


def require_roles(*allowed_roles: str):
    def _dependency(ctx: AuthorizationContext = Depends(get_authorization_context)) -> AuthorizationContext:
        if ctx.role not in set(allowed_roles):
            raise HTTPException(status_code=403, detail="Role not allowed")
        return ctx

    return _dependency
