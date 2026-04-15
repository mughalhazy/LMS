"""FastAPI entrypoint for progress-service."""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Query

from .schemas import (
    LearningPathAssignmentRequest,
    LearningPathAssignmentResponse,
    LearnerProgressSummaryResponse,
    LessonCompleteResponse,
    LessonProgressCompleteRequest,
    LessonProgressUpsertRequest,
    ProgressRecordResponse,
)
from .service import EnrollmentInactiveError, InMemoryEventPublisher, NoopMetricsHook, ProgressService
from .store import InMemoryIdempotencyStore, InMemoryProgressStore

app = FastAPI(title="progress-service", version="v1")

store = InMemoryProgressStore()
idempotency = InMemoryIdempotencyStore()
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
