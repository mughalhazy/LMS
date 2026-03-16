"""Content service API entrypoint."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Content Service", version="0.1.0")


class ContentUploadRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content_type: Literal["video", "document", "assessment_asset"]


class ContentUploadResponse(BaseModel):
    content_id: str
    tenant_id: str
    course_id: str
    title: str
    content_type: str
    status: Literal["uploaded"]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/content/uploads", response_model=ContentUploadResponse)
def upload_content(request: ContentUploadRequest) -> ContentUploadResponse:
    return ContentUploadResponse(
        content_id=f"cnt-{uuid4().hex[:10]}",
        tenant_id=request.tenant_id,
        course_id=request.course_id,
        title=request.title,
        content_type=request.content_type,
        status="uploaded",
    )

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "content-service", "service_up": 1}

