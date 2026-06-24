"""API schemas for hris-sync-service."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class SyncRolesRequest(BaseModel):
    role_records: list[dict[str, Any]] = Field(min_length=1)
    actor: str = "system"
    session_id: Optional[str] = None


class SyncDepartmentsRequest(BaseModel):
    department_records: list[dict[str, Any]] = Field(min_length=1)
    actor: str = "system"
    session_id: Optional[str] = None


class SyncEmployeesRequest(BaseModel):
    employee_records: list[dict[str, Any]] = Field(min_length=1)
    actor: str = "system"
    session_id: Optional[str] = None


class FullSyncRequest(BaseModel):
    role_records: list[dict[str, Any]] = Field(default_factory=list)
    department_records: list[dict[str, Any]] = Field(default_factory=list)
    employee_records: list[dict[str, Any]] = Field(default_factory=list)
    actor: str = "system"


class StartSessionRequest(BaseModel):
    triggered_by: str = Field(min_length=1)
    sync_mode: str = "manual"


class CompleteSessionRequest(BaseModel):
    status: str = "completed"


class UpsertJobRequest(BaseModel):
    interval_minutes: int = Field(gt=0)
    enabled: bool = True


class RunDueSyncJobsRequest(BaseModel):
    """Empty body — due-job resolution uses tenant_id from header."""
