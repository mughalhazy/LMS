"""Service entrypoint for lesson-service."""

from __future__ import annotations

import time
from collections import Counter
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status

from .schemas import (
    DeliveryStateResponse,
    DeliveryStateUpdateRequest,
    ErrorResponse,
    HealthResponse,
    LessonCreateRequest,
    LessonListResponse,
    LessonReorderRequest,
    LessonResponse,
    LessonUpdateRequest,
    MetricsResponse,
    ProgressionHookRequest,
)
from .security import apply_security_headers, require_jwt
from .service import LessonService, NotFoundError, ValidationError
from .store_db import SQLiteLessonStore

app = FastAPI(title="lesson-service", version="2.0.0", dependencies=[Depends(require_jwt)])


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
_store = SQLiteLessonStore()
_service = LessonService(_store)
_metrics = Counter()


def _tenant_context(
    request: Request,
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_actor_id: Annotated[str | None, Header()] = None,
) -> tuple[str, str]:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_tenant_id")
    # CAT-022: validate X-Tenant-Id against JWT tenant_id claim to prevent tenant spoofing
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import base64, json as _json
            token = auth_header[7:]
            parts = token.split(".")
            if len(parts) == 3:
                padded = parts[1] + "=" * (-len(parts[1]) % 4)
                jwt_payload = _json.loads(base64.urlsafe_b64decode(padded))
                jwt_tenant = jwt_payload.get("tenant_id") or jwt_payload.get("tid", "")
                if jwt_tenant and jwt_tenant != x_tenant_id:
                    raise HTTPException(status_code=401, detail="tenant_header_jwt_mismatch")
        except HTTPException:
            raise
        except Exception:
            pass  # malformed token — let downstream JWT middleware handle it
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


@app.post("/api/v1/courses/{course_id}/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson_nested(course_id: str, request: LessonCreateRequest, ctx: tuple[str, str] = Depends(_tenant_context)) -> LessonResponse:
    tenant_id, actor_id = ctx
    payload = request.model_dump()
    payload["course_id"] = course_id
    return LessonResponse.model_validate(_service.create_lesson(tenant_id, actor_id, payload))


@app.put("/api/v1/courses/{course_id}/lessons:reorder", status_code=200)
def reorder_lessons(course_id: str, request: LessonReorderRequest, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict[str, object]:
    tenant_id, actor_id = ctx
    try:
        results = _service.reorder_lessons(tenant_id, actor_id, course_id, request.ordered_lesson_ids)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"course_id": course_id, "reordered": results}


@app.post("/api/v1/lessons/{lesson_id}:versions", status_code=201)
def snapshot_lesson_version(lesson_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict[str, object]:
    tenant_id, actor_id = ctx
    try:
        return _service.snapshot_version(tenant_id, actor_id, lesson_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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


@app.post("/api/v1/lessons/{lesson_id}:publish")
def publish_lesson(lesson_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, actor_id = ctx
    try:
        lesson = _service.publish_lesson(tenant_id, actor_id, lesson_id)
        # CAT-020: spec §4.4 publish response includes published_version + effective_from
        pub_at = lesson.published_at.isoformat() if lesson.published_at else None
        return {
            "lesson_id": lesson.lesson_id,
            "status": lesson.status.value if hasattr(lesson.status, "value") else str(lesson.status),
            "published_version": lesson.published_version,
            "published_at": pub_at,
            "effective_from": pub_at,  # immediate publish — effective_from == published_at
        }
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


@app.get("/api/v1/lessons/{lesson_id}/delivery-state", response_model=DeliveryStateResponse)
def get_delivery_state(
    lesson_id: str,
    learner_id: str | None = Query(default=None),
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> DeliveryStateResponse:
    # Spec: lesson-service-spec.md §4.7 — delivery state read endpoint
    tenant_id, _ = ctx
    try:
        lesson = _service.get_lesson(tenant_id, lesson_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    ds = lesson.delivery_state or {}
    launchable = ds.get("launchable", lesson.status == "published")
    blocked_reasons = ds.get("blocked_reasons", [])
    avail = lesson.availability_rules or {}
    availability_window = {
        "opens_at": avail.get("opens_at", None),
        "closes_at": avail.get("closes_at", None),
    }
    requires_enrollment = ds.get("requires_enrollment", True)
    prerequisite_state = ds.get(
        "prerequisite_state",
        {"is_satisfied": True, "unsatisfied_prerequisites": []},
    )
    return DeliveryStateResponse(
        lesson_id=lesson.lesson_id,
        course_id=lesson.course_id,
        status=lesson.status.value if hasattr(lesson.status, "value") else str(lesson.status),
        launchable=bool(launchable),
        blocked_reasons=list(blocked_reasons),
        availability_window=availability_window,
        requires_enrollment=bool(requires_enrollment),
        prerequisite_state=prerequisite_state,
    )


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
