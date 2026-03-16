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

app = FastAPI(title="Course Service", version="1.0.0", dependencies=[Depends(require_jwt)])
apply_security_headers(app)
service = CourseService()


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


@app.post("/api/v1/courses", status_code=201)
def create_course(request: CreateCourseRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    return _wrap(service.create_course(request).model_dump(), ctx)


@app.get("/api/v1/courses")
def list_courses(ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    data = [course.model_dump() for course in service.list_courses(ctx["tenant_id"])]
    return _wrap(data, ctx)


@app.get("/api/v1/courses/{course_id}")
def get_course(course_id: str, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    return _wrap(service.get_course(ctx["tenant_id"], course_id).model_dump(), ctx)


@app.patch("/api/v1/courses/{course_id}")
def update_course(course_id: str, request: UpdateCourseRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    return _wrap(service.update_course(course_id, request).model_dump(), ctx)


@app.post("/api/v1/courses/{course_id}/publish")
def publish_course(course_id: str, request: PublishCourseRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    return _wrap(service.publish_course(course_id, request).model_dump(), ctx)


@app.post("/api/v1/courses/{course_id}/archive")
def archive_course(course_id: str, request: ArchiveCourseRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    return _wrap(service.archive_course(course_id, request).model_dump(), ctx)


@app.put("/api/v1/courses/{course_id}/program-links")
def upsert_program_links(course_id: str, request: UpsertProgramLinksRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    links = service.upsert_program_links(course_id, request)
    return _wrap([ProgramLink.model_validate(link).model_dump() for link in links], ctx)


@app.get("/api/v1/courses/{course_id}/program-links")
def get_program_links(course_id: str, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    course: CourseResponse = service.get_course(ctx["tenant_id"], course_id)
    return _wrap([link.model_dump() for link in course.program_links], ctx)


@app.put("/api/v1/courses/{course_id}/session-links")
def upsert_session_links(course_id: str, request: UpsertSessionLinksRequest, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    _assert_tenant_match(ctx["tenant_id"], request.tenant_id)
    links = service.upsert_session_links(course_id, request)
    return _wrap([SessionLink.model_validate(link).model_dump() for link in links], ctx)


@app.get("/api/v1/courses/{course_id}/session-links")
def get_session_links(course_id: str, ctx: dict[str, str] = Depends(tenant_context)) -> ApiResponse:
    course: CourseResponse = service.get_course(ctx["tenant_id"], course_id)
    return _wrap([link.model_dump() for link in course.session_links], ctx)


@app.delete("/api/v1/courses/{course_id}", status_code=204, response_class=Response)
def delete_course(course_id: str, ctx: dict[str, str] = Depends(tenant_context)) -> Response:
    service.delete_course(ctx["tenant_id"], course_id)
    return Response(status_code=204)
