"""API schemas for scorm-service (stub — MO-044 deferred for full build)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScormPackageUploadRequest(BaseModel):
    title: str = Field(min_length=1)
    scorm_version: str = Field(default="2004", pattern=r"^(1\.2|2004)$")
    course_id: str | None = None
    tenant_id: str = Field(min_length=1)
    package_url: str | None = None


class ScormPackageResponse(BaseModel):
    package_id: str
    title: str
    scorm_version: str
    course_id: str | None
    tenant_id: str
    status: str
    created_at: datetime


class ScormLaunchRequest(BaseModel):
    learner_id: str = Field(min_length=1)
    enrollment_id: str | None = None
    return_url: str | None = None


class ScormLaunchResponse(BaseModel):
    launch_url: str
    attempt_id: str
    package_id: str
    learner_id: str


class ScormCompletionStatus(BaseModel):
    package_id: str
    learner_id: str
    completion_status: str
    success_status: str
    score: float | None
    total_time: str | None
    last_accessed_at: datetime | None


class CmiDataUpdateRequest(BaseModel):
    attempt_id: str = Field(min_length=1)
    learner_id: str = Field(min_length=1)
    cmi_data: dict[str, Any] = Field(default_factory=dict)


class CmiDataResponse(BaseModel):
    attempt_id: str
    learner_id: str
    cmi_data: dict[str, Any]
    updated_at: datetime
