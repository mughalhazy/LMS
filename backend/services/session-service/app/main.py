from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from app.schemas import (
    CreateSessionRequest,
    LinkCohortsRequest,
    LinkCourseRequest,
    LinkLessonRequest,
    ScheduleSessionRequest,
    TransitionRequest,
    UpdateSessionRequest,
)
from src.repository import InMemorySessionRepository
from src.service import (
    InvalidSessionTransitionError,
    SessionNotFoundError,
    SessionService,
    SessionServiceError,
    TenantBoundaryError,
)

app = FastAPI(title="session-service", version="2.0.0")
service = SessionService(InMemorySessionRepository())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "session-service"}


@app.get("/metrics")
def metrics() -> dict[str, int]:
    snapshot = service.observability_snapshot()
    snapshot["service_up"] = 1
    return snapshot


@app.post("/api/v2/sessions", status_code=201)
def create_session(request: CreateSessionRequest) -> dict:
    try:
        session = service.create_session(**request.model_dump())
        return service.session_to_dict(session)
    except SessionServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v2/sessions/{session_id}")
def get_session(session_id: str, tenant_id: str = Query(...)) -> dict:
    try:
        session = service.get_session(tenant_id=tenant_id, session_id=session_id)
        return service.session_to_dict(session)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TenantBoundaryError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.patch("/api/v2/sessions/{session_id}")
def update_session(session_id: str, request: UpdateSessionRequest) -> dict:
    try:
        session = service.update_session(session_id=session_id, **request.model_dump())
        return service.session_to_dict(session)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TenantBoundaryError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except SessionServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v2/sessions/{session_id}/schedule")
def schedule_session(session_id: str, request: ScheduleSessionRequest) -> dict:
    try:
        session = service.schedule_session(
            tenant_id=request.tenant_id,
            session_id=session_id,
            scheduled_by=request.scheduled_by,
            timezone_name=request.timezone,
            start_at=request.start_at,
            end_at=request.end_at,
            recurrence_rule=request.recurrence_rule,
            reason=request.reason,
            force=request.force,
        )
        return service.session_to_dict(session)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TenantBoundaryError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except SessionServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v2/sessions/{session_id}/publish")
def publish_session(session_id: str, request: TransitionRequest) -> dict:
    return _transition(session_id, request, service.publish_session)


@app.post("/api/v2/sessions/{session_id}/start")
def start_session(session_id: str, request: TransitionRequest) -> dict:
    return _transition(session_id, request, service.start_session)


@app.post("/api/v2/sessions/{session_id}/complete")
def complete_session(session_id: str, request: TransitionRequest) -> dict:
    return _transition(session_id, request, service.complete_session)


@app.post("/api/v2/sessions/{session_id}/cancel")
def cancel_session(session_id: str, request: TransitionRequest) -> dict:
    try:
        session = service.cancel_session(
            tenant_id=request.tenant_id,
            session_id=session_id,
            actor_id=request.actor_id,
            reason=request.reason or "canceled",
        )
        return service.session_to_dict(session)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TenantBoundaryError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (InvalidSessionTransitionError, SessionServiceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v2/sessions/{session_id}/archive")
def archive_session(session_id: str, request: TransitionRequest) -> dict:
    return _transition(session_id, request, service.archive_session)


@app.put("/api/v2/sessions/{session_id}/course-link")
def link_course(session_id: str, request: LinkCourseRequest) -> dict:
    return _link(session_id, request.tenant_id, lambda: service.link_course(
        tenant_id=request.tenant_id,
        session_id=session_id,
        actor_id=request.actor_id,
        course_id=request.course_id,
    ))


@app.put("/api/v2/sessions/{session_id}/lesson-link")
def link_lesson(session_id: str, request: LinkLessonRequest) -> dict:
    return _link(session_id, request.tenant_id, lambda: service.link_lesson(
        tenant_id=request.tenant_id,
        session_id=session_id,
        actor_id=request.actor_id,
        lesson_id=request.lesson_id,
    ))


@app.put("/api/v2/sessions/{session_id}/cohorts")
def link_cohorts(session_id: str, request: LinkCohortsRequest) -> dict:
    return _link(session_id, request.tenant_id, lambda: service.link_cohorts(
        tenant_id=request.tenant_id,
        session_id=session_id,
        actor_id=request.actor_id,
        cohort_ids=request.cohort_ids,
    ))


@app.get("/api/v2/sessions")
def list_sessions(
    tenant_id: str = Query(...),
    status: str | None = Query(None),
    delivery_mode: str | None = Query(None),
    course_id: str | None = Query(None),
    cohort_id: str | None = Query(None),
    instructor_id: str | None = Query(None),
) -> list[dict]:
    sessions = service.list_sessions(
        tenant_id=tenant_id,
        status=status,
        delivery_mode=delivery_mode,
        course_id=course_id,
        cohort_id=cohort_id,
        instructor_id=instructor_id,
    )
    return [service.session_to_dict(s) for s in sessions]


@app.get("/api/v2/sessions/calendar")
def list_calendar(tenant_id: str = Query(...)) -> list[dict]:
    return service.list_calendar(tenant_id=tenant_id)


@app.get("/api/v2/sessions/by-course/{course_id}")
def list_by_course(course_id: str, tenant_id: str = Query(...)) -> list[dict]:
    sessions = service.list_sessions(tenant_id=tenant_id, course_id=course_id)
    return [service.session_to_dict(s) for s in sessions]


@app.get("/api/v2/sessions/by-cohort/{cohort_id}")
def list_by_cohort(cohort_id: str, tenant_id: str = Query(...)) -> list[dict]:
    sessions = service.list_sessions(tenant_id=tenant_id, cohort_id=cohort_id)
    return [service.session_to_dict(s) for s in sessions]


def _transition(session_id: str, request: TransitionRequest, callback) -> dict:
    try:
        session = callback(tenant_id=request.tenant_id, session_id=session_id, actor_id=request.actor_id)
        return service.session_to_dict(session)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TenantBoundaryError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (InvalidSessionTransitionError, SessionServiceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _link(session_id: str, tenant_id: str, callback) -> dict:
    try:
        session = callback()
        return service.session_to_dict(session)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TenantBoundaryError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except SessionServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
