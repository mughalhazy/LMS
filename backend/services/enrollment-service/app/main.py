"""Enrollment service API entrypoint."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from .security import apply_security_headers, require_jwt

app = FastAPI(title="Enrollment Service", version="0.1.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)


class EnrollmentCreateRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    learner_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)


class EnrollmentResponse(BaseModel):
    enrollment_id: str
    tenant_id: str
    learner_id: str
    course_id: str
    status: Literal["enrolled"]


class ErrorResponse(BaseModel):
    error: str
    detail: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/enrollments",
    response_model=EnrollmentResponse,
    responses={400: {"model": ErrorResponse}},
)
def create_enrollment(request: EnrollmentCreateRequest) -> EnrollmentResponse:
    if not request.course_id.startswith("course-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_request", "detail": "course_id must start with 'course-'"},
        )

    return EnrollmentResponse(
        enrollment_id=f"enr-{uuid4().hex[:10]}",
        tenant_id=request.tenant_id,
        learner_id=request.learner_id,
        course_id=request.course_id,
        status="enrolled",
    )
