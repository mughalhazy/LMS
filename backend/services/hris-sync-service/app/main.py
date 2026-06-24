"""Service entrypoint — hris-sync-service REST API."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status

from .schemas import (
    CompleteSessionRequest,
    FullSyncRequest,
    StartSessionRequest,
    SyncDepartmentsRequest,
    SyncEmployeesRequest,
    SyncRolesRequest,
    UpsertJobRequest,
)
from .security import apply_security_headers, require_jwt
from .service import HRISSyncManagementService

# B02-009: spec §2 — all routes require tenant identity; JWT validates caller
app = FastAPI(title="hris-sync-service", version="1.0.0", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()

apply_security_headers(app)
_SERVICE = HRISSyncManagementService()


def _tenant(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_tenant_id")
    return x_tenant_id


# ── Utility ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hris-sync-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "hris-sync-service", "service_up": 1}


# ── Sync operations ───────────────────────────────────────────────────────────

@app.post("/api/v1/hris/sync/roles", status_code=status.HTTP_200_OK)
def sync_roles(
    request: SyncRolesRequest,
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> dict[str, Any]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SERVICE.sync_roles(
            tenant_id=tenant_id,
            role_records=request.role_records,
            actor=request.actor,
            session_id=request.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/hris/sync/departments", status_code=status.HTTP_200_OK)
def sync_departments(
    request: SyncDepartmentsRequest,
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> dict[str, Any]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SERVICE.sync_org_hierarchy(
            tenant_id=tenant_id,
            department_records=request.department_records,
            actor=request.actor,
            session_id=request.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/hris/sync/employees", status_code=status.HTTP_200_OK)
def sync_employees(
    request: SyncEmployeesRequest,
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> dict[str, Any]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SERVICE.sync_employees(
            tenant_id=tenant_id,
            employee_records=request.employee_records,
            actor=request.actor,
            session_id=request.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/hris/sync/full", status_code=status.HTTP_200_OK)
def full_sync(
    request: FullSyncRequest,
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> dict[str, Any]:
    """Run all three sync operations in dependency order: roles → departments → employees."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SERVICE.run_full_sync(
            tenant_id=tenant_id,
            role_records=request.role_records,
            department_records=request.department_records,
            employee_records=request.employee_records,
            actor=request.actor,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ── Sync sessions ─────────────────────────────────────────────────────────────

@app.post("/api/v1/hris/sessions", status_code=status.HTTP_201_CREATED)
def start_session(
    request: StartSessionRequest,
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> dict[str, Any]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.start_sync_session(
        tenant_id=tenant_id,
        triggered_by=request.triggered_by,
        sync_mode=request.sync_mode,
    )


@app.get("/api/v1/hris/sessions")
def list_sessions(
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> list[dict[str, Any]]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.list_sync_sessions(tenant_id=tenant_id)


@app.get("/api/v1/hris/sessions/{session_id}")
def get_session(
    session_id: str,
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> dict[str, Any]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SERVICE.get_sync_session(tenant_id=tenant_id, session_id=session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/v1/hris/sessions/{session_id}/complete")
def complete_session(
    session_id: str,
    request: CompleteSessionRequest,
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> dict[str, Any]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    try:
        return _SERVICE.complete_sync_session(
            tenant_id=tenant_id,
            session_id=session_id,
            status=request.status,
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Job management ────────────────────────────────────────────────────────────

@app.put("/api/v1/hris/jobs/{job_name}")
def upsert_job(
    job_name: str,
    request: UpsertJobRequest,
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> dict[str, Any]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.upsert_sync_job(
        tenant_id=tenant_id,
        job_name=job_name,
        interval_minutes=request.interval_minutes,
        enabled=request.enabled,
    )


@app.get("/api/v1/hris/jobs")
def list_jobs(
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> list[dict[str, Any]]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.list_sync_jobs(tenant_id=tenant_id)


@app.post("/api/v1/hris/jobs/run-due")
def run_due_jobs(
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> list[dict[str, Any]]:
    """Execute all sync jobs whose next_run_at is in the past."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.run_due_sync_jobs(tenant_id=tenant_id)


# ── Data reads ────────────────────────────────────────────────────────────────

@app.get("/api/v1/hris/users")
def list_users(
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> list[dict[str, Any]]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.list_users(tenant_id=tenant_id)


@app.get("/api/v1/hris/departments")
def list_departments(
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> list[dict[str, Any]]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.list_departments(tenant_id=tenant_id)


@app.get("/api/v1/hris/roles")
def list_roles(
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> list[dict[str, Any]]:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.list_roles(tenant_id=tenant_id)


# ── Audit log ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/hris/audit")
def get_audit_log(
    operation: Optional[str] = Query(default=None),
    tenant_id: str = Header(alias="x-tenant-id", default=None),
) -> list[dict[str, Any]]:
    """Return sync audit log, optionally filtered by operation type.

    Operation values: ``role_mapping``, ``department_mapping``, ``employee_sync``.
    """
    if not tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return _SERVICE.get_audit_log(tenant_id=tenant_id, operation=operation)
