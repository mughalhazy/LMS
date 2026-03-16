from __future__ import annotations

from fastapi import APIRouter, Depends, FastAPI, Header, Response

from .events import InMemoryEventPublisher, InMemoryObservabilityHook
from .middleware import build_authorization_dependency
from .schemas import (
    AssignmentCreateRequest,
    AssignmentUpdateRequest,
    AuthorizeBatchRequest,
    AuthorizeRequest,
    PolicyRuleCreateRequest,
    PolicyRuleUpdateRequest,
    ReplaceRolePermissionsRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)
from .security import apply_security_headers, require_jwt, require_tenant_scope
from .service import RBACService
from .store import InMemoryRBACStore

app = FastAPI(
    title="RBAC Authorization Service",
    version="2.0.0",
    dependencies=[Depends(require_jwt), Depends(require_tenant_scope)],
)

store = InMemoryRBACStore()
publisher = InMemoryEventPublisher()
observability = InMemoryObservabilityHook()
service = RBACService(store, publisher, observability)
apply_security_headers(app)

router = APIRouter(prefix="/api/v1/rbac", tags=["rbac"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "rbac-service", "version": "v1"}


@router.post("/roles", status_code=201)
def create_role(payload: RoleCreateRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.create_role(x_tenant_id, payload)


@router.get("/roles")
def list_roles(x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.list_roles(x_tenant_id)


@router.patch("/roles/{role_id}")
def update_role(role_id: str, payload: RoleUpdateRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.update_role(x_tenant_id, role_id, payload)


@router.put("/roles/{role_id}/permissions", status_code=204)
def replace_permissions(role_id: str, payload: ReplaceRolePermissionsRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    service.replace_role_permissions(x_tenant_id, role_id, payload.permissions)
    return Response(status_code=204)


@router.get("/permissions")
def list_permissions():
    return store.list_permissions()


@router.post("/assignments", status_code=201)
def create_assignment(payload: AssignmentCreateRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.create_assignment(x_tenant_id, payload)


@router.get("/assignments")
def list_assignments(x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.list_assignments(x_tenant_id)


@router.patch("/assignments/{assignment_id}")
def update_assignment(assignment_id: str, payload: AssignmentUpdateRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.update_assignment(x_tenant_id, assignment_id, payload)


@router.delete("/assignments/{assignment_id}", status_code=204)
def revoke_assignment(assignment_id: str, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    service.revoke_assignment(x_tenant_id, assignment_id)
    return Response(status_code=204)


@router.get("/subjects/{subject_type}/{subject_id}/effective-permissions")
def effective_permissions(subject_type: str, subject_id: str, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return {"permissions": service.effective_permissions(x_tenant_id, subject_type, subject_id)}


@router.post("/authorize")
def authorize(payload: AuthorizeRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id"), x_correlation_id: str | None = Header(None, alias="X-Correlation-Id")):
    return service.authorize(x_tenant_id, payload, x_correlation_id)


@router.post("/authorize/batch")
def authorize_batch(payload: AuthorizeBatchRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return {"results": [service.authorize(x_tenant_id, check).model_dump() for check in payload.checks]}


@router.post("/policy-rules", status_code=201)
def create_policy_rule(payload: PolicyRuleCreateRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.create_policy_rule(x_tenant_id, payload)


@router.get("/policy-rules")
def list_policy_rules(x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.list_policy_rules(x_tenant_id)


@router.patch("/policy-rules/{policy_rule_id}")
def update_policy_rule(policy_rule_id: str, payload: PolicyRuleUpdateRequest, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    return service.update_policy_rule(x_tenant_id, policy_rule_id, payload)


@router.delete("/policy-rules/{policy_rule_id}", status_code=204)
def disable_policy_rule(policy_rule_id: str, x_tenant_id: str = Header(..., alias="X-Tenant-Id")):
    service.disable_policy_rule(x_tenant_id, policy_rule_id)
    return Response(status_code=204)


@router.get("/audit-log")
def list_audit_log(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    _: None = Depends(build_authorization_dependency(service, "audit.view_tenant")),
):
    return [event.model_dump(mode="json") for event in store.list_decision_logs(x_tenant_id)]


@router.get("/metrics")
def metrics() -> dict:
    return {"service": "rbac-service", "service_up": 1, "counters": observability.counters}


app.include_router(router)


@app.get("/health")
def root_health() -> dict[str, str]:
    return {"status": "ok"}
