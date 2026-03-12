from __future__ import annotations

from fastapi import Header, HTTPException

from .models import ScopeType, SubjectType
from .store import InMemoryRBACStore


def build_authorization_dependency(
    store: InMemoryRBACStore,
    required_permission: str,
):
    async def authorize_request(
        x_principal_id: str = Header(..., alias="X-Principal-Id"),
        x_principal_type: SubjectType = Header(SubjectType.USER, alias="X-Principal-Type"),
        x_scope_type: ScopeType = Header(..., alias="X-Scope-Type"),
        x_scope_id: str = Header(..., alias="X-Scope-Id"),
        x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
    ) -> None:
        decision = store.authorize(
            principal_id=x_principal_id,
            principal_type=x_principal_type,
            permission=required_permission,
            scope_type=x_scope_type,
            scope_id=x_scope_id,
            correlation_id=x_correlation_id,
        )
        if decision.decision != "ALLOW":
            raise HTTPException(status_code=403, detail={"reason": decision.reason})

    return authorize_request
