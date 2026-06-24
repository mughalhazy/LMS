"""Service entrypoint for scorm-service.

Stub implementation — spec-aligned routes, 501 bodies.
Full SCORM 1.2/2004 runtime deferred to MO-044 build sprint.
Governing spec: scorm-service-spec.md (when written); aligns to SCORM Cloud API contract.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException

from .schemas import (
    CmiDataResponse,
    CmiDataUpdateRequest,
    ScormCompletionStatus,
    ScormLaunchRequest,
    ScormLaunchResponse,
    ScormPackageResponse,
    ScormPackageUploadRequest,
)

app = FastAPI(title="scorm-service", version="0.1.0")


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()


def _stub_package(package_id: str, title: str, tenant_id: str, scorm_version: str = "2004") -> ScormPackageResponse:
    return ScormPackageResponse(
        package_id=package_id,
        title=title,
        scorm_version=scorm_version,
        course_id=None,
        tenant_id=tenant_id,
        status="registered",
        created_at=datetime.now(timezone.utc),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "scorm-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "scorm-service", "service_up": 1}


# ── Package management ────────────────────────────────────────────────────────

@app.post("/api/v1/scorm/packages", response_model=ScormPackageResponse, status_code=201)
def register_package(
    request: ScormPackageUploadRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
) -> ScormPackageResponse:
    """Spec §2 — register a SCORM package (stub: returns 201 with generated package_id)."""
    # AUD-053: validate body tenant_id matches header when provided
    from fastapi import HTTPException as _HTTPException
    if request.tenant_id and request.tenant_id != x_tenant_id:
        raise _HTTPException(status_code=400, detail="tenant_id body field must match X-Tenant-Id header")
    return _stub_package(
        package_id=str(uuid4()),
        title=request.title,
        tenant_id=x_tenant_id,
        scorm_version=request.scorm_version,
    )


@app.get("/api/v1/scorm/packages", response_model=list[ScormPackageResponse])
def list_packages(x_tenant_id: str = Header(..., alias="X-Tenant-Id")) -> list[ScormPackageResponse]:
    """Spec §2 — list SCORM packages for tenant (stub: empty list)."""
    return []


@app.get("/api/v1/scorm/packages/{package_id}", response_model=ScormPackageResponse)
def get_package(package_id: str, x_tenant_id: str = Header(..., alias="X-Tenant-Id")) -> ScormPackageResponse:
    """Spec §2 — get SCORM package (stub: returns placeholder)."""
    return _stub_package(package_id=package_id, title="stub-package", tenant_id=x_tenant_id)


@app.delete("/api/v1/scorm/packages/{package_id}", status_code=204)
def delete_package(package_id: str, x_tenant_id: str = Header(..., alias="X-Tenant-Id")) -> None:
    """Spec §2 — delete SCORM package (stub: 204 no-content)."""
    return None


# ── Launch + completion ───────────────────────────────────────────────────────

@app.post("/api/v1/scorm/packages/{package_id}/launch", response_model=ScormLaunchResponse, status_code=201)
def launch_package(
    package_id: str,
    request: ScormLaunchRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
) -> ScormLaunchResponse:
    """Spec §3 — launch SCORM package for learner (stub: returns placeholder launch URL)."""
    attempt_id = str(uuid4())
    return ScormLaunchResponse(
        launch_url=f"/scorm/runtime/{attempt_id}",
        attempt_id=attempt_id,
        package_id=package_id,
        learner_id=request.learner_id,
    )


@app.get("/api/v1/scorm/packages/{package_id}/status/{learner_id}", response_model=ScormCompletionStatus)
def get_completion_status(
    package_id: str,
    learner_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
) -> ScormCompletionStatus:
    """Spec §3 — get learner completion status (stub: unknown)."""
    return ScormCompletionStatus(
        package_id=package_id,
        learner_id=learner_id,
        completion_status="unknown",
        success_status="unknown",
        score=None,
        total_time=None,
        last_accessed_at=None,
    )


# ── CMI runtime data ──────────────────────────────────────────────────────────

@app.put("/api/v1/scorm/runtime/cmi-data", response_model=CmiDataResponse)
def set_cmi_data(
    request: CmiDataUpdateRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
) -> CmiDataResponse:
    """Spec §4 — persist CMI data from SCORM runtime (stub: echo back)."""
    return CmiDataResponse(
        attempt_id=request.attempt_id,
        learner_id=request.learner_id,
        cmi_data=request.cmi_data,
        updated_at=datetime.now(timezone.utc),
    )


@app.get("/api/v1/scorm/runtime/cmi-data/{attempt_id}", response_model=CmiDataResponse)
def get_cmi_data(
    attempt_id: str,
    learner_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
) -> CmiDataResponse:
    """Spec §4 — retrieve CMI data for an attempt (stub: empty cmi_data)."""
    return CmiDataResponse(
        attempt_id=attempt_id,
        learner_id=learner_id,
        cmi_data={},
        updated_at=datetime.now(timezone.utc),
    )
