from __future__ import annotations

from fastapi import FastAPI, Depends
from .security import apply_security_headers, require_jwt

from .schemas import (
    CourseResponse,
    CreateCourseRequest,
    CreateCourseVersionRequest,
    PublishCourseRequest,
    UpdateCourseRequest,
    VersionResponse,
)
from .service import CourseService

app = FastAPI(title="Course Service", version="0.1.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)
service = CourseService()


@app.post("/courses", response_model=CourseResponse)
def create_course(request: CreateCourseRequest) -> CourseResponse:
    return service.create_course(request)


@app.get("/courses", response_model=list[CourseResponse])
def list_courses(tenant_id: str) -> list[CourseResponse]:
    return service.list_courses(tenant_id)


@app.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: str, tenant_id: str) -> CourseResponse:
    return service.get_course(tenant_id, course_id)


@app.patch("/courses/{course_id}", response_model=CourseResponse)
def update_course(course_id: str, request: UpdateCourseRequest) -> CourseResponse:
    return service.update_course(course_id, request)


@app.post("/courses/{course_id}/publish", response_model=CourseResponse)
def publish_course(course_id: str, request: PublishCourseRequest) -> CourseResponse:
    return service.publish_course(course_id, request)


@app.post("/courses/{course_id}/versions", response_model=VersionResponse)
def create_course_version(course_id: str, request: CreateCourseVersionRequest) -> VersionResponse:
    return service.create_course_version(course_id, request)
