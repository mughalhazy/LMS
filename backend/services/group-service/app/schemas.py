"""API schemas for group-service."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CreateGroupRequest(BaseModel):
    organization_id: str
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "member"


class AssignLearningRequest(BaseModel):
    assignment_type: str   # course | learning_path
    learning_object_id: str
    target: str = "current_members"   # current_members | current_and_future_members
    due_at: Optional[datetime] = None
    metadata: Optional[Dict[str, str]] = None
