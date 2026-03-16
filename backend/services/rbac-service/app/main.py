from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from .security import apply_security_headers, require_jwt

from .middleware import build_authorization_dependency
from .models import Assignment, AssignmentCreate, AuthorizeDecision, AuthorizeRequest, Permission, Role
from .store import InMemoryRBACStore

app = FastAPI(title="RBAC Authorization Service", version="1.0.0", dependencies=[Depends(require_jwt)])
store = InMemoryRBACStore()

apply_security_headers(app)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/roles", response_model=list[Role])
def list_roles() -> list[Role]:
    return store.list_roles()


@app.get("/permissions", response_model=list[Permission])
def list_permissions() -> list[Permission]:
    return store.list_permissions()


@app.get("/assignments", response_model=list[Assignment])
def list_assignments() -> list[Assignment]:
    return store.list_assignments()


@app.post("/assignments", response_model=Assignment, status_code=201)
def create_assignment(payload: AssignmentCreate) -> Assignment:
    try:
        return store.create_assignment(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authorize", response_model=AuthorizeDecision)
def authorize(payload: AuthorizeRequest) -> AuthorizeDecision:
    return store.authorize(
        principal_id=payload.principal_id,
        principal_type=payload.principal_type,
        permission=payload.permission,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
    )


@app.get("/audit-log")
def list_audit_log(
    _: None = Depends(build_authorization_dependency(store, "audit.view_tenant")),
) -> list[dict]:
    return [event.model_dump(mode="json") for event in store.list_audit_events()]

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "rbac-service", "service_up": 1}

