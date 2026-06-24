"""FastAPI entrypoint for enrollment service."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request

from .models import TenantContext
from .schemas import (
    AuditLogResponse,
    BulkAssignRequest,
    BulkAssignResponse,
    BulkAssignResult,
    EnrollmentCreateRequest,
    EnrollmentLinksRequest,
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
from .store import InMemoryAuditLogStore
from .store_db import SQLiteEnrollmentStore

app = FastAPI(title="Enrollment Service", version="1.0.0", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response



# G-22: accept /api/v2/enrollments/* alongside /api/v1/enrollments/* (coordinated migration)
@app.middleware("http")
async def _v2_path_compat(request: Request, call_next):
    if request.url.path.startswith("/api/v2/"):
        scope = dict(request.scope)
        scope["path"] = scope["path"].replace("/api/v2/", "/api/v1/", 1)
        if scope.get("raw_path"):
            scope["raw_path"] = scope["raw_path"].replace(b"/api/v2/", b"/api/v1/", 1)
        request = Request(scope, request.receive)
    return await call_next(request)

# FA-024: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()

store = SQLiteEnrollmentStore()
audit_store = InMemoryAuditLogStore()
event_publisher = InMemoryEventPublisher()
observability = InMemoryObservabilityHook()
service = EnrollmentService(store, audit_store, event_publisher, observability)

apply_security_headers(app)


def tenant_context(
    request: Request,
    x_tenant_id: str = Header(..., min_length=1),
    x_actor_id: str = Header(default="system"),
) -> TenantContext:
    # CAT-023: multi-tenant-isolation-model §2 requires header + JWT claim validation.
    # Validate X-Tenant-Id against JWT tenant_id claim if token is present.
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            import base64, json as _j
            parts = auth[7:].split(".")
            if len(parts) == 3:
                padded = parts[1] + "=" * (-len(parts[1]) % 4)
                jwt_payload = _j.loads(base64.urlsafe_b64decode(padded))
                jwt_tenant = jwt_payload.get("tenant_id") or jwt_payload.get("tid", "")
                if jwt_tenant and jwt_tenant != x_tenant_id:
                    from fastapi import HTTPException as _H
                    raise _H(status_code=401, detail="tenant_header_jwt_mismatch")
        except (ImportError, ValueError, KeyError):
            pass  # malformed token handled by JWT middleware
    return TenantContext(tenant_id=x_tenant_id, actor_id=x_actor_id)


def to_response(item) -> EnrollmentResponse:
    return EnrollmentResponse(
        enrollment_id=item.id,
        tenant_id=item.tenant_id,
        user_id=item.learner_id,
        course_id=item.course_id,
        source_channel=item.assignment_source,
        cohort_id=item.cohort_id,
        session_id=item.session_id,
        enrollment_status=item.status,
        version=item.version,
        created_at=item.created_at,
        updated_at=item.updated_at,
        enrolled_at=item.enrolled_at,
        completed_at=item.completed_at,
        dropped_at=item.dropped_at,
        deferred_at=item.deferred_at,
        expired_at=item.expired_at,
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
    cohort_id: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    context: TenantContext = Depends(tenant_context),
) -> EnrollmentListResponse:
    items = service.list_enrollments(
        context,
        learner_id=learner_id,
        course_id=course_id,
        status=status,
        cohort_id=cohort_id,
        session_id=session_id,
        page=page,
        page_size=page_size,
    )
    # AUD-022: include pagination fields in response
    response_items = [to_response(item) for item in items]
    return EnrollmentListResponse(
        items=response_items,
        page=page,
        page_size=page_size,
        total=len(response_items),  # stub total; real impl would query count separately
    )


@app.patch("/api/v1/enrollments/{enrollment_id}/links", response_model=EnrollmentResponse)
def update_enrollment_links(
    enrollment_id: str,
    payload: EnrollmentLinksRequest,
    context: TenantContext = Depends(tenant_context),
) -> EnrollmentResponse:
    try:
        return to_response(service.update_links(context, enrollment_id, payload.cohort_id, payload.session_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# AUD-009: canonical path /transitions; /status-transitions kept as alias
@app.post("/api/v1/enrollments/{enrollment_id}/transitions", response_model=EnrollmentResponse)
@app.post("/api/v1/enrollments/{enrollment_id}/status-transitions", response_model=EnrollmentResponse)
def transition_status(
    enrollment_id: str,
    payload: StatusTransitionRequest,
    context: TenantContext = Depends(tenant_context),
) -> EnrollmentResponse:
    try:
        current = service.get_enrollment(context, enrollment_id)
        if payload.expected_version is not None and current.version != payload.expected_version:
            raise HTTPException(status_code=409, detail="version_conflict")
        # AUD-020: use resolved properties that accept both old and new field names
        resolved_status = payload.resolved_status
        resolved_reason = payload.resolved_reason
        updated = service.transition_status(context, enrollment_id, resolved_status, resolved_reason)
        return to_response(updated)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# AUD-023: spec §4.6 — 202 + {job_id, accepted_count, rejected_count, submitted_at}
@app.post("/api/v1/enrollments/bulk-assign", response_model=BulkAssignResponse, status_code=202)
def bulk_assign(
    payload: BulkAssignRequest,
    context: TenantContext = Depends(tenant_context),
) -> BulkAssignResponse:
    from uuid import uuid4
    from datetime import datetime, timezone
    results = []
    accepted = rejected = 0
    for user_id in payload.user_ids:
        create_req = EnrollmentCreateRequest(
            user_id=user_id,
            course_id=payload.course_id,
            source_channel=payload.source_channel,
            cohort_id=payload.cohort_id,
            session_id=payload.session_id,
            assigned_by=payload.assigned_by,
        )
        try:
            created = service.create_enrollment(context, create_req)
            results.append(BulkAssignResult(user_id=user_id, status="created", enrollment_id=created.id))
            accepted += 1
        except ConflictError:
            results.append(BulkAssignResult(user_id=user_id, status="skipped", error="already_enrolled"))
            rejected += 1
        except Exception as exc:
            results.append(BulkAssignResult(user_id=user_id, status="failed", error=str(exc)))
            rejected += 1
    return BulkAssignResponse(
        job_id=str(uuid4()),
        accepted_count=accepted,
        rejected_count=rejected,
        submitted_at=datetime.now(timezone.utc).isoformat(),
        results=results,
    )


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
