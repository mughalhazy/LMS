from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response

from .schemas import (
    ApiMeta,
    ApiResponse,
    ArchiveCourseRequest,
    CourseResponse,
    CreateCourseRequest,
    ProgramLink,
    PublishCourseRequest,
    SessionLink,
    UpdateCourseRequest,
    UpsertProgramLinksRequest,
    UpsertSessionLinksRequest,
)
from .security import apply_security_headers, require_jwt
from .service import CourseService
from .store_db import SQLiteCourseStorage

# AUD-048: JWT applied per-route on API paths only; /health and /metrics are unauthenticated
app = FastAPI(title="Course Service", version="1.0.0")


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
service = CourseService(storage=SQLiteCourseStorage())


def tenant_context(
    request: Request,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
) -> dict[str, str]:
    request_id = x_request_id or str(uuid4())
    request.state.request_id = request_id
    request.state.tenant_id = x_tenant_id
    return {"tenant_id": x_tenant_id, "request_id": request_id}


def _assert_tenant_match(expected: str, actual: str) -> None:
    if expected != actual:
        raise HTTPException(status_code=400, detail="Tenant header does not match payload tenant_id")


def _wrap(data: object, ctx: dict[str, str]) -> ApiResponse:
    return ApiResponse(data=data, meta=ApiMeta(request_id=ctx["request_id"], tenant_id=ctx["tenant_id"], timestamp=datetime.now(timezone.utc)), errors=[])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "course-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "course-service", "service_up": 1, **service.metrics}


@app.post("/api/v1/courses", status_code=201, dependencies=[Depends(require_jwt)])
def create_course(request: CreateCourseRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    return _wrap(service.create_course(request).model_dump(), ctx)


@app.get("/api/v1/courses", dependencies=[Depends(require_jwt)])
def list_courses(
    ctx: dict[str, str] = Depends(tenant_context),
    status: str | None = None,
    language_code: str | None = None,
    category_id: str | None = None,
    delivery_mode: str | None = None,
    publish_status: str | None = None,
) -> ApiResponse:
    courses = service.list_courses(ctx["tenant_id"])
    if status:
        courses = [c for c in courses if c.status.value == status]
    if publish_status:
        courses = [c for c in courses if c.publish_status.value == publish_status]
    if language_code:
        courses = [c for c in courses if c.language_code == language_code]
    if category_id:
        courses = [c for c in courses if c.metadata.category_id == category_id]
    if delivery_mode:
        courses = [c for c in courses if c.metadata.delivery_mode and c.metadata.delivery_mode.value == delivery_mode]
    data = [course.model_dump() for course in courses]
    return _wrap(data, ctx)


@app.get("/api/v1/courses/{course_id}", dependencies=[Depends(require_jwt)])
def get_course(course_id: str, ctx: dict[str, str] = Depends(tenant_context), response: Response = None) -> ApiResponse:
    course = service.get_course(ctx["tenant_id"], course_id)
    if response is not None:
        response.headers["ETag"] = f'"{course.version}"'
    return _wrap(course.model_dump(), ctx)


@app.patch("/api/v1/courses/{course_id}", dependencies=[Depends(require_jwt)])
def update_course(
    course_id: str,
    request: UpdateCourseRequest,
    ctx: dict[str, str] = Depends(tenant_context),
    if_match: str | None = Header(None, alias="If-Match"),
) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    expected_version: int | None = None
    if if_match:
        try:
            expected_version = int(if_match.strip('"'))
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid_if_match_header")
    return _wrap(service.update_course(course_id, request, expected_version=expected_version).model_dump(), ctx)


@app.post("/api/v1/courses/{course_id}/publish", dependencies=[Depends(require_jwt)])
def publish_course(course_id: str, request: PublishCourseRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    return _wrap(service.publish_course(course_id, request).model_dump(), ctx)


@app.post("/api/v1/courses/{course_id}/archive", dependencies=[Depends(require_jwt)])
def archive_course(course_id: str, request: ArchiveCourseRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    return _wrap(service.archive_course(course_id, request).model_dump(), ctx)


@app.put("/api/v1/courses/{course_id}/program-links", dependencies=[Depends(require_jwt)])
def upsert_program_links(course_id: str, request: UpsertProgramLinksRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    links = service.upsert_program_links(course_id, request)
    return _wrap([ProgramLink.model_validate(link).model_dump() for link in links], ctx)


@app.get("/api/v1/courses/{course_id}/program-links", dependencies=[Depends(require_jwt)])
def get_program_links(course_id: str, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    course: CourseResponse = service.get_course(ctx["tenant_id"], course_id)
    return _wrap([link.model_dump() for link in course.program_links], ctx)


@app.put("/api/v1/courses/{course_id}/session-links", dependencies=[Depends(require_jwt)])
def upsert_session_links(course_id: str, request: UpsertSessionLinksRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    links = service.upsert_session_links(course_id, request)
    return _wrap([SessionLink.model_validate(link).model_dump() for link in links], ctx)


@app.get("/api/v1/courses/{course_id}/session-links", dependencies=[Depends(require_jwt)])
def get_session_links(course_id: str, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    course: CourseResponse = service.get_course(ctx["tenant_id"], course_id)
    return _wrap([link.model_dump() for link in course.session_links], ctx)


@app.delete("/api/v1/courses/{course_id}", status_code=204, response_class=Response, dependencies=[Depends(require_jwt)])
def delete_course(course_id: str, ctx: dict[str, str] = Depends(tenant_context)) -> Response:
    service.delete_course(ctx["tenant_id"], course_id)
    return Response(status_code=204)
