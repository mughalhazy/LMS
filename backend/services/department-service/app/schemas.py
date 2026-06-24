"""API schemas for department-service."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreateDepartmentRequest(BaseModel):
    organization_id: str
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    parent_department_id: Optional[str] = None
    department_head_user_id: Optional[str] = None
    cost_center: Optional[str] = None


class UpdateDepartmentRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department_head_user_id: Optional[str] = None
    cost_center: Optional[str] = None


class DeactivateDepartmentRequest(BaseModel):
    cascade: bool = False


class ReparentDepartmentRequest(BaseModel):
    new_parent_department_id: Optional[str] = None


class MapMembershipRequest(BaseModel):
    organization_id: str
    user_id: str
    role: str = "member"
