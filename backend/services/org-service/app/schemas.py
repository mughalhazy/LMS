from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .models import Status


class OrgBase(BaseModel):
    name: str
    code: str
    primary_admin_user_id: Optional[str] = None
    timezone: str = "UTC"
    locale: str = "en-US"
    parent_organization_id: Optional[str] = None
    metadata: dict[str, str] = Field(default_factory=dict)


class OrganizationCreate(OrgBase):
    tenant_id: str


class OrganizationPatch(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    primary_admin_user_id: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    parent_organization_id: Optional[str] = None
    metadata: Optional[dict[str, str]] = None
    status: Optional[Status] = None


class OrganizationOut(OrgBase):
    model_config = ConfigDict(from_attributes=True)

    organization_id: str
    tenant_id: str
    status: Status
    created_at: datetime
    updated_at: datetime


class DepartmentBase(BaseModel):
    name: str
    code: str
    department_head_user_id: Optional[str] = None
    cost_center: Optional[str] = None
    parent_department_id: Optional[str] = None
    metadata: dict[str, str] = Field(default_factory=dict)


class DepartmentCreate(DepartmentBase):
    organization_id: str


class DepartmentPatch(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department_head_user_id: Optional[str] = None
    cost_center: Optional[str] = None
    parent_department_id: Optional[str] = None
    metadata: Optional[dict[str, str]] = None
    status: Optional[Status] = None


class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    department_id: str
    organization_id: str
    status: Status
    created_at: datetime
    updated_at: datetime


class TeamBase(BaseModel):
    name: str
    code: str
    team_lead_user_id: Optional[str] = None
    capacity: Optional[int] = None
    metadata: dict[str, str] = Field(default_factory=dict)


class TeamCreate(TeamBase):
    department_id: str


class TeamPatch(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    team_lead_user_id: Optional[str] = None
    capacity: Optional[int] = None
    department_id: Optional[str] = None
    metadata: Optional[dict[str, str]] = None
    status: Optional[Status] = None


class TeamOut(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    team_id: str
    department_id: str
    status: Status
    created_at: datetime
    updated_at: datetime


class LifecycleRequest(BaseModel):
    cascade: bool = False


class HierarchyOut(BaseModel):
    organization: OrganizationOut
    departments: list[DepartmentOut]
    teams: list[TeamOut]
