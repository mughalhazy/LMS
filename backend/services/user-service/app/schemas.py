from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

from .models import AccountStatus, IdentityMapping, LifecycleEvent, User, UserPreferences, UserProfile


class CreateUserRequest(BaseModel):
    tenant_id: str
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    role_set: List[str] = Field(default_factory=list)
    auth_provider: str
    external_subject_id: Optional[str] = None
    created_by: str
    start_active: bool = False


class ActivateUserRequest(BaseModel):
    tenant_id: str
    activation_token: Optional[str] = None
    admin_override_reason: Optional[str] = None
    activated_by: str


class UpdateUserRequest(BaseModel):
    tenant_id: str
    updated_by: str
    username: Optional[str] = None
    role_set: Optional[List[str]] = None
    status: Optional[AccountStatus] = None
    department: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    tenant_id: str
    updated_by: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[str] = None
    avatar_url: Optional[str] = None


class ManagePreferencesRequest(BaseModel):
    tenant_id: str
    updated_by: str
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)
    accessibility_preferences: Dict[str, str] = Field(default_factory=dict)
    language_preference: Optional[str] = None


class ChangeStatusRequest(BaseModel):
    tenant_id: str
    target_status: AccountStatus
    reason_code: str
    changed_by: str
    effective_at: Optional[datetime] = None


class LockUnlockRequest(BaseModel):
    tenant_id: str
    action: str
    reason_code: str
    performed_by: str
    lock_duration: Optional[int] = None


class TerminateReinstateRequest(BaseModel):
    tenant_id: str
    action: str
    performed_by: str
    offboarding_date: Optional[datetime] = None
    data_retention_policy_id: Optional[str] = None


class MapIdentityRequest(BaseModel):
    tenant_id: str
    identity_provider: str
    external_subject_id: str
    mapped_by: str
    external_username: Optional[str] = None
    mapping_attributes: Dict[str, str] = Field(default_factory=dict)


class UnmapIdentityRequest(BaseModel):
    tenant_id: str
    identity_provider: str
    external_subject_id: str
    unmapped_by: str
    reason: str


class UserResponse(BaseModel):
    user: User


class PreferencesResponse(BaseModel):
    preferences: UserPreferences


class IdentityLinksResponse(BaseModel):
    identity_links: List[IdentityMapping]


class TimelineResponse(BaseModel):
    lifecycle_timeline: List[LifecycleEvent]


class UserListResponse(BaseModel):
    items: List[User]
