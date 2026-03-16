"""Certificate service API entrypoint."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from .security import apply_security_headers, require_jwt

app = FastAPI(title="Certificate Service", version="0.1.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)


class CertificateIssueRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    learner_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)


class CertificateIssueResponse(BaseModel):
    certificate_id: str
    tenant_id: str
    learner_id: str
    course_id: str
    status: Literal["issued"]
    issued_at: datetime


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/certificates", response_model=CertificateIssueResponse)
def issue_certificate(request: CertificateIssueRequest) -> CertificateIssueResponse:
    return CertificateIssueResponse(
        certificate_id=f"crt-{uuid4().hex[:10]}",
        tenant_id=request.tenant_id,
        learner_id=request.learner_id,
        course_id=request.course_id,
        status="issued",
        issued_at=datetime.now(timezone.utc),
    )
