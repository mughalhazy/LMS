from __future__ import annotations

from fastapi import Depends, FastAPI, Header, Query

from backend.services.shared.context.correlation import ensure_correlation_id

from .models import ProgramStatus
from .schemas import (
    CreateProgramRequest,
    InstitutionLinkResponse,
    ProgramCoursesMapResponse,
    ProgramDetailResponse,
    ProgramListResponse,
    ProgramResponse,
    ProgramUpdateResult,
    ReplaceProgramCoursesRequest,
    StatusTransitionResponse,
    TransitionProgramStatusRequest,
    UpdateProgramRequest,
    UpsertInstitutionLinkRequest,
)
from .service import ProgramService
from .store import InMemoryProgramStore
from .tenant import tenant_context

app = FastAPI(title="Program Service", version="1.0.0")
service = ProgramService(store=InMemoryProgramStore(), known_courses={"c-101", "c-205", "c-301"})


@app.post("/api/v1/programs", response_model=ProgramResponse, status_code=201)
def create_program(
    request: CreateProgramRequest,
    tenant_id: str = Depends(tenant_context),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> ProgramResponse:
    if request.tenant_id != tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.create_program(request, correlation_id=ensure_correlation_id(x_correlation_id))


@app.get("/api/v1/programs/{program_id}", response_model=ProgramDetailResponse)
def get_program(
    program_id: str,
    tenant_id: str = Depends(tenant_context),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> ProgramDetailResponse:
    return service.get_program(tenant_id, program_id, correlation_id=ensure_correlation_id(x_correlation_id))


@app.patch("/api/v1/programs/{program_id}", response_model=ProgramUpdateResult)
def update_program(
    program_id: str,
    request: UpdateProgramRequest,
    tenant_id: str = Depends(tenant_context),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> ProgramUpdateResult:
    if request.tenant_id != tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.update_program(program_id, request, correlation_id=ensure_correlation_id(x_correlation_id))


@app.post("/api/v1/programs/{program_id}/status", response_model=StatusTransitionResponse)
def transition_status(
    program_id: str,
    request: TransitionProgramStatusRequest,
    tenant_id: str = Depends(tenant_context),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> StatusTransitionResponse:
    if request.tenant_id != tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.transition_status(program_id, request, correlation_id=ensure_correlation_id(x_correlation_id))


@app.put("/api/v1/programs/{program_id}/institution-links", response_model=InstitutionLinkResponse)
def upsert_institution_link(
    program_id: str,
    request: UpsertInstitutionLinkRequest,
    tenant_id: str = Depends(tenant_context),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> InstitutionLinkResponse:
    if request.tenant_id != tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.upsert_institution_link(program_id, request, correlation_id=ensure_correlation_id(x_correlation_id))


@app.put("/api/v1/programs/{program_id}/courses", response_model=ProgramCoursesMapResponse)
def replace_program_courses(
    program_id: str,
    request: ReplaceProgramCoursesRequest,
    tenant_id: str = Depends(tenant_context),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> ProgramCoursesMapResponse:
    if request.tenant_id != tenant_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="tenant_context_mismatch")
    return service.replace_program_courses(program_id, request, correlation_id=ensure_correlation_id(x_correlation_id))


@app.delete("/api/v1/programs/{program_id}/courses/{course_id}", status_code=200)
def remove_program_course(
    program_id: str,
    course_id: str,
    updated_by: str = Query(...),
    tenant_id: str = Depends(tenant_context),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> None:
    service.remove_course(
        tenant_id=tenant_id,
        program_id=program_id,
        course_id=course_id,
        updated_by=updated_by,
        correlation_id=ensure_correlation_id(x_correlation_id),
    )


@app.get("/api/v1/programs", response_model=ProgramListResponse)
def list_programs(
    institution_id: str | None = None,
    status: ProgramStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    tenant_id: str = Depends(tenant_context),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
) -> ProgramListResponse:
    return service.list_programs(
        tenant_id=tenant_id,
        institution_id=institution_id,
        status=status,
        page=page,
        page_size=page_size,
        correlation_id=ensure_correlation_id(x_correlation_id),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "program-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    snapshot = service.observability.snapshot()
    return {"service": "program-service", "service_up": 1, **snapshot}
