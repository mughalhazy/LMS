"""Service entrypoint for lesson-service."""

from __future__ import annotations

import time
from collections import Counter
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status

from .schemas import (
    DeliveryStateUpdateRequest,
    ErrorResponse,
    HealthResponse,
    LessonCreateRequest,
    LessonListResponse,
    LessonResponse,
    LessonUpdateRequest,
    MetricsResponse,
    ProgressionHookRequest,
)
from .security import apply_security_headers, require_jwt
from .service import LessonService, NotFoundError, ValidationError
from .store import InMemoryLessonStore

app = FastAPI(title="lesson-service", version="2.0.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)
_store = InMemoryLessonStore()
_service = LessonService(_store)
_metrics = Counter()


def _tenant_context(
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_actor_id: Annotated[str | None, Header()] = None,
) -> tuple[str, str]:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_tenant_id")
    return x_tenant_id, x_actor_id or "system"


@app.middleware("http")
async def observe_request(request: Request, call_next):
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    _metrics["http_requests_total"] += 1
    _metrics[f"http_status_{response.status_code}"] += 1
    response.headers["X-Elapsed-Ms"] = f"{elapsed_ms:.2f}"
    return response


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="lesson-service")


@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    return MetricsResponse(
        service="lesson-service",
        service_up=1,
        lessons_total=sum(len(v) for v in _store._lessons.values()),
        events_emitted=len(_store.events),
    )


@app.post("/api/v1/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(request: LessonCreateRequest, ctx: tuple[str, str] = Depends(_tenant_context)) -> LessonResponse:
    tenant_id, actor_id = ctx
    return LessonResponse.model_validate(_service.create_lesson(tenant_id, actor_id, request.model_dump()))


@app.get("/api/v1/lessons/{lesson_id}", response_model=LessonResponse, responses={404: {"model": ErrorResponse}})
def get_lesson(lesson_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> LessonResponse:
    tenant_id, _ = ctx
    try:
        return LessonResponse.model_validate(_service.get_lesson(tenant_id, lesson_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/lessons", response_model=LessonListResponse)
def list_lessons(
    course_id: str | None = Query(default=None),
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> LessonListResponse:
    tenant_id, _ = ctx
    lessons = _service.list_lessons(tenant_id, course_id)
    return LessonListResponse(lessons=[LessonResponse.model_validate(item) for item in lessons])


@app.patch("/api/v1/lessons/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: str,
    request: LessonUpdateRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> LessonResponse:
    tenant_id, actor_id = ctx
    payload = {k: v for k, v in request.model_dump().items() if v is not None}
    try:
        lesson = _service.update_lesson(tenant_id, actor_id, lesson_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return LessonResponse.model_validate(lesson)


@app.post("/api/v1/lessons/{lesson_id}:publish", response_model=LessonResponse)
def publish_lesson(lesson_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> LessonResponse:
    tenant_id, actor_id = ctx
    try:
        return LessonResponse.model_validate(_service.publish_lesson(tenant_id, actor_id, lesson_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/v1/lessons/{lesson_id}:unpublish", response_model=LessonResponse)
def unpublish_lesson(lesson_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> LessonResponse:
    tenant_id, actor_id = ctx
    try:
        return LessonResponse.model_validate(_service.unpublish_lesson(tenant_id, actor_id, lesson_id))
    except (NotFoundError, ValidationError) as exc:
        raise HTTPException(status_code=409 if isinstance(exc, ValidationError) else 404, detail=str(exc)) from exc


@app.post("/api/v1/lessons/{lesson_id}:archive", response_model=LessonResponse)
def archive_lesson(lesson_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> LessonResponse:
    tenant_id, actor_id = ctx
    try:
        return LessonResponse.model_validate(_service.archive_lesson(tenant_id, actor_id, lesson_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/v1/lessons/{lesson_id}:delivery-state", response_model=LessonResponse)
def delivery_state(
    lesson_id: str,
    request: DeliveryStateUpdateRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> LessonResponse:
    tenant_id, actor_id = ctx
    try:
        lesson = _service.set_delivery_state(tenant_id, actor_id, lesson_id, request.state)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LessonResponse.model_validate(lesson)


@app.post("/api/v1/lessons/{lesson_id}:progression-hooks", status_code=status.HTTP_202_ACCEPTED)
def progression_hook(
    lesson_id: str,
    request: ProgressionHookRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict[str, str]:
    tenant_id, actor_id = ctx
    try:
        _service.trigger_progression_hook(tenant_id, actor_id, lesson_id, request.hook_type, request.payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "accepted"}


@app.delete("/api/v1/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(lesson_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> Response:
    tenant_id, actor_id = ctx
    try:
        _service.delete_lesson(tenant_id, actor_id, lesson_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
