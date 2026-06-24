"""FastAPI entrypoint for progress-service."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from .schemas import (
    LearningPathAssignmentRequest,
    LearningPathAssignmentResponse,
    LearnerProgressSummaryResponse,
    LessonCompleteResponse,
    LessonProgressCompleteRequest,
    LessonProgressUpsertRequest,
    ProgressRecordResponse,
)
from .security import apply_security_headers, require_jwt
from .service import EnrollmentInactiveError, InMemoryEventPublisher, NoopMetricsHook, ProgressService
from .store_db import SQLiteIdempotencyStore, SQLiteProgressStore

# B01-006: multi-tenant-isolation-model §2 — JWT required on all non-exempt endpoints
app = FastAPI(title="progress-service", version="v1", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()

apply_security_headers(app)
store = SQLiteProgressStore()
idempotency = SQLiteIdempotencyStore()
publisher = InMemoryEventPublisher()
metrics = NoopMetricsHook()
service = ProgressService(store=store, idempotency=idempotency, publisher=publisher, metrics=metrics)


def enforce_tenant(request_tenant_id: str, header_tenant_id: str) -> None:
    if header_tenant_id != request_tenant_id:
        raise HTTPException(status_code=400, detail="tenant_mismatch")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "progress-service", "version": "v1"}


@app.get("/metrics")
def metrics_endpoint() -> dict[str, int]:
    return {"service_up": 1, **metrics.counters}


@app.post("/api/v1/progress/lessons/{lesson_id}/upsert", response_model=ProgressRecordResponse)
def upsert_lesson_progress(
    lesson_id: str,
    request: LessonProgressUpsertRequest,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
) -> ProgressRecordResponse:
    enforce_tenant(request.tenant_id, x_tenant_id)
    try:
        return service.upsert_lesson_progress(lesson_id=lesson_id, request=request, actor_id="api")
    except EnrollmentInactiveError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/v1/progress/lessons/{lesson_id}/complete", response_model=LessonCompleteResponse)
def complete_lesson_progress(
    lesson_id: str,
    request: LessonProgressCompleteRequest,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
) -> LessonCompleteResponse:
    enforce_tenant(request.tenant_id, x_tenant_id)
    try:
        return service.complete_lesson(lesson_id=lesson_id, request=request, actor_id="api")
    except EnrollmentInactiveError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/v1/progress/learners/{learner_id}", response_model=LearnerProgressSummaryResponse)
def get_learner_progress(
    learner_id: str,
    tenant_id: str = Query(...),
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
) -> LearnerProgressSummaryResponse:
    enforce_tenant(tenant_id, x_tenant_id)
    return service.get_learner_summary(tenant_id=tenant_id, learner_id=learner_id)


@app.get("/api/v1/progress/learners/{learner_id}/courses/{course_id}")
def get_course_progress(
    learner_id: str,
    course_id: str,
    tenant_id: str = Query(...),
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
):
    enforce_tenant(tenant_id, x_tenant_id)
    row = service.get_course_progress(tenant_id=tenant_id, learner_id=learner_id, course_id=course_id)
    if not row:
        raise HTTPException(status_code=404, detail="course_progress_not_found")
    return row


@app.post(
    "/api/v1/progress/learning-paths/{learning_path_id}/assignments",
    response_model=LearningPathAssignmentResponse,
    status_code=202,
)
def assign_learning_path(
    learning_path_id: str,
    request: LearningPathAssignmentRequest,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
) -> LearningPathAssignmentResponse:
    enforce_tenant(request.tenant_id, x_tenant_id)
    return service.assign_learning_path(learning_path_id=learning_path_id, request=request, actor_id="api")


@app.get("/api/v1/progress/eligibility/courses/{course_id}/users/{user_id}")
def get_completion_eligibility(
    course_id: str,
    user_id: str,
    tenant_id: str = Query(...),
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
) -> dict:
    # B01-002: spec §8.1 — read-only eligibility endpoint for certificate-service integration
    enforce_tenant(tenant_id, x_tenant_id)
    row = service.get_course_progress(tenant_id=tenant_id, learner_id=user_id, course_id=course_id)
    eligible = row is not None and row.completion_status in ("completed", "passed")
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "course_id": course_id,
        "eligible_for_certificate": eligible,
        "completion_status": row.completion_status if row else "not_started",
        "progress_percentage": row.progress_percentage if row else 0.0,
    }
