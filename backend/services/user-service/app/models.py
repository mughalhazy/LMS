from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field


class AccountStatus(str, Enum):
    PENDING_ACTIVATION = "pending_activation"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    DEACTIVATED = "deactivated"
    TERMINATED = "terminated"


class LifecycleEventType(str, Enum):
    CREATED = "user.created"
    ACTIVATED = "user.activated"
    PROFILE_UPDATED = "user.profile_updated"
    PREFERENCES_UPDATED = "user.preferences.updated"
    STATUS_CHANGED = "user.status_changed"
    IDENTITY_MAPPED = "user.identity.mapped"
    IDENTITY_UNMAPPED = "user.identity.unmapped"


class UserProfile(BaseModel):
    first_name: str
    last_name: str
    locale: Optional[str] = None
    timezone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPreferences(BaseModel):
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)
    accessibility_preferences: Dict[str, str] = Field(default_factory=dict)
    language_preference: Optional[str] = None


class IdentityMapping(BaseModel):
    mapping_id: str = Field(default_factory=lambda: str(uuid4()))
    identity_provider: str
    external_subject_id: str
    external_username: Optional[str] = None
    mapping_attributes: Dict[str, str] = Field(default_factory=dict)
    status: str = "active"
    mapped_by: str
    mapped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None
    assurance_level: Optional[str] = None


class LifecycleEvent(BaseModel):
    event_type: LifecycleEventType
    actor: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detail: Dict[str, str] = Field(default_factory=dict)


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    email: EmailStr
    username: str
    role_set: List[str] = Field(default_factory=list)
    auth_provider: str
    external_subject_id: Optional[str] = None
    profile: UserProfile
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    status: AccountStatus = AccountStatus.PENDING_ACTIVATION
    profile_version: int = 1
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None
    lifecycle_timeline: List[LifecycleEvent] = Field(default_factory=list)
    identity_links: List[IdentityMapping] = Field(default_factory=list)
