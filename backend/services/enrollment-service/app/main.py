"""FastAPI entrypoint for enrollment service."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from .models import TenantContext
from .schemas import (
    AuditLogResponse,
    EnrollmentCreateRequest,
    EnrollmentListResponse,
    EnrollmentResponse,
    ErrorResponse,
    StatusTransitionRequest,
)
from .security import apply_security_headers, require_jwt
from .service import (
    ConflictError,
    EnrollmentService,
    InMemoryEventPublisher,
    InMemoryObservabilityHook,
    NotFoundError,
    ValidationError,
)
from .store import InMemoryAuditLogStore, InMemoryEnrollmentStore

app = FastAPI(title="Enrollment Service", version="1.0.0", dependencies=[Depends(require_jwt)])

store = InMemoryEnrollmentStore()
audit_store = InMemoryAuditLogStore()
event_publisher = InMemoryEventPublisher()
observability = InMemoryObservabilityHook()
service = EnrollmentService(store, audit_store, event_publisher, observability)

apply_security_headers(app)


def tenant_context(
    x_tenant_id: str = Header(..., min_length=1),
    x_actor_id: str = Header(..., min_length=1),
) -> TenantContext:
    return TenantContext(tenant_id=x_tenant_id, actor_id=x_actor_id)


def to_response(item) -> EnrollmentResponse:
    return EnrollmentResponse(
        id=item.id,
        tenant_id=item.tenant_id,
        learner_id=item.learner_id,
        course_id=item.course_id,
        assignment_source=item.assignment_source,
        cohort_id=item.cohort_id,
        session_id=item.session_id,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> dict[str, float | str]:
    response: dict[str, float | str] = {"service": "enrollment-service", "service_up": 1.0}
    response.update(observability.metrics)
    return response


@app.post(
    "/api/v1/enrollments",
    response_model=EnrollmentResponse,
    status_code=201,
    responses={409: {"model": ErrorResponse}},
)
def create_enrollment(payload: EnrollmentCreateRequest, context: TenantContext = Depends(tenant_context)) -> EnrollmentResponse:
    try:
        return to_response(service.create_enrollment(context, payload))
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/v1/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
def get_enrollment(enrollment_id: str, context: TenantContext = Depends(tenant_context)) -> EnrollmentResponse:
    try:
        return to_response(service.get_enrollment(context, enrollment_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/enrollments", response_model=EnrollmentListResponse)
def list_enrollments(
    learner_id: str | None = Query(default=None),
    course_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    context: TenantContext = Depends(tenant_context),
) -> EnrollmentListResponse:
    items = service.list_enrollments(context, learner_id=learner_id, course_id=course_id, status=status)
    return EnrollmentListResponse(items=[to_response(item) for item in items])


@app.post("/api/v1/enrollments/{enrollment_id}/status-transitions", response_model=EnrollmentResponse)
def transition_status(
    enrollment_id: str,
    payload: StatusTransitionRequest,
    context: TenantContext = Depends(tenant_context),
) -> EnrollmentResponse:
    try:
        updated = service.transition_status(context, enrollment_id, payload.to_status, payload.reason)
        return to_response(updated)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(context: TenantContext = Depends(tenant_context)) -> list[AuditLogResponse]:
    rows = service.list_audit_logs(context)
    return [
        AuditLogResponse(
            actor_id=row.actor_id,
            action=row.action,
            enrollment_id=row.enrollment_id,
            metadata=row.metadata,
            created_at=row.created_at,
        )
        for row in rows
    ]
