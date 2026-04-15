from __future__ import annotations

from fastapi import Header, HTTPException

from .models import ScopeType, SubjectType
from .service import RBACService


def build_authorization_dependency(service: RBACService, required_permission: str):
    async def authorize_request(
        x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
        x_principal_id: str = Header(..., alias="X-Principal-Id"),
        x_principal_type: SubjectType = Header(SubjectType.USER, alias="X-Principal-Type"),
        x_scope_type: ScopeType = Header(ScopeType.TENANT, alias="X-Scope-Type"),
        x_scope_id: str = Header(..., alias="X-Scope-Id"),
        x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
    ) -> None:
        from .schemas import AuthorizeRequest, ResourceRef, SubjectRef

        decision = service.authorize(
            x_tenant_id,
            AuthorizeRequest(
                subject=SubjectRef(type=x_principal_type, id=x_principal_id),
                permission_key=required_permission,
                resource=ResourceRef(type=x_scope_type.value, id=x_scope_id),
                scope_type=x_scope_type,
                scope_id=x_scope_id,
                context={},
            ),
            correlation_id=x_correlation_id,
        )
        if decision.decision != "allow":
            raise HTTPException(status_code=403, detail={"reason_codes": decision.reason_codes})

    return authorize_request
