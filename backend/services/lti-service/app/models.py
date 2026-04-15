from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RegistrationStatus(str, Enum):
    PENDING_VALIDATION = "pending_validation"
    ACTIVE = "active"


class TrustStatus(str, Enum):
    UNTRUSTED = "untrusted"
    TRUSTED = "trusted"


class ProvisioningMode(str, Enum):
    JIT = "JIT"
    PRE_PROVISIONED = "pre-provisioned"


class ToolRegistrationRequest(BaseModel):
    tenant_id: str
    tool_name: str
    initiate_login_uri: str
    redirect_uris: list[str]
    jwks_uri: str | None = None
    public_key_set: dict[str, Any] | None = None
    requested_scopes: list[str]
    deployment_context: str
    default_role_mapping: dict[str, str] = Field(default_factory=dict)
    admin_actor_id: str


class ToolRegistrationResponse(BaseModel):
    tool_id: str
    client_id: str
    deployment_id: str
    platform_issuer: str
    authorization_endpoint: str
    keyset_url: str
    registration_status: RegistrationStatus
    created_at: datetime


class ValidationActivationRequest(BaseModel):
    tool_id: str
    jwks_fetch_result: bool
    redirect_uri_verification_result: bool
    scope_policy_check: bool
    tenant_security_policy: str
    admin_approval: bool


class ValidationActivationResponse(BaseModel):
    validation_report: dict[str, list[str]]
    activation_decision: bool
    activated_scopes: list[str]
    trust_status: TrustStatus
    audit_event_id: str


class OIDCLoginInitiationRequest(BaseModel):
    iss: str
    login_hint: str
    target_link_uri: str
    lti_message_hint: str | None = None
    client_id: str
    deployment_id: str
    nonce: str | None = None


class OIDCLoginInitiationResponse(BaseModel):
    authorization_redirect_url: str
    state: str
    nonce_binding_record: dict[str, str]
    correlation_id: str


class LaunchValidationRequest(BaseModel):
    id_token: str
    state: str
    nonce: str
    expected_audience: str
    expected_issuer: str
    deployment_id: str


class LaunchValidationResponse(BaseModel):
    launch_validation_status: str
    launch_context_id: str
    resource_link_id: str | None = None
    context_id: str | None = None
    launch_claims_snapshot: dict[str, Any]
    policy_decisions: dict[str, str]


class SessionProvisioningRequest(BaseModel):
    launch_context_id: str
    user_subject: str
    roles: list[str]
    context_membership: dict[str, Any] = Field(default_factory=dict)
    tool_settings: dict[str, Any] = Field(default_factory=dict)
    tenant_policies: dict[str, Any] = Field(default_factory=dict)


class SessionProvisioningResponse(BaseModel):
    lms_session_token: str
    effective_permissions: list[str]
    learner_or_instructor_view: str
    landing_route: str
    session_expiry: datetime


class IdentityMappingRequest(BaseModel):
    tenant_id: str
    issuer: str
    platform_user_sub: str
    lis_person_sourcedid: str | None = None
    email: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    roles: list[str]
    provisioning_mode: ProvisioningMode


class IdentityMappingResponse(BaseModel):
    lms_user_id: str
    identity_link_id: str
    match_strategy_used: str
    account_state: str
    remediation_action: str | None = None


class RoleNormalizationRequest(BaseModel):
    lti_roles: list[str]
    context_type: str
    tenant_role_mapping_rules: dict[str, str] = Field(default_factory=dict)
    default_role_fallback: str = "learner"


class RoleNormalizationResponse(BaseModel):
    normalized_lms_roles: list[str]
    enrollment_actions: list[str]
    authorization_scope_set: list[str]
    role_mapping_audit_id: str


class ServiceAccessTokenRequest(BaseModel):
    client_assertion_jwt: str
    grant_type: str = "client_credentials"
    requested_scope: str
    tool_id: str
    deployment_id: str


class ServiceAccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    granted_scopes: list[str]
    service_endpoints: dict[str, str]


class GradePassbackRequest(BaseModel):
    access_token: str
    lineitem_id: str
    user_id: str
    score_given: float
    score_maximum: float
    grading_progress: str
    activity_progress: str
    timestamp: datetime


class GradePassbackResponse(BaseModel):
    score_write_status: str
    platform_response_code: int
    idempotency_key: str
    retry_instruction: str | None = None


class MembershipSyncRequest(BaseModel):
    access_token: str
    context_id: str
    pagination_cursor: str | None = None
    role_filter: str | None = None


class MembershipSyncResponse(BaseModel):
    membership_page: list[dict[str, Any]]
    next_cursor: str | None
    sync_checkpoint: datetime
    import_summary: dict[str, int]


class ConsumerToolRegistrationRequest(BaseModel):
    tenant_id: str
    tool_name: str
    issuer: str
    client_id: str
    deployment_id: str
    launch_url: str
    jwks_endpoint: str
    oidc_auth_initiation_url: str
    target_link_uri: str
    allowed_message_types: list[str] = Field(default_factory=lambda: ["LtiResourceLinkRequest"])
    ags_endpoint: str | None = None
    nrps_endpoint: str | None = None


class ConsumerToolRegistrationResponse(BaseModel):
    tool_id: str
    status: str
    redirect_uri_allowlist: list[str]
    security_controls: dict[str, Any]


class ConsumerLaunchInitiateRequest(BaseModel):
    tool_id: str
    user_id: str
    course_id: str
    resource_link_id: str
    role: str
    locale: str = "en-US"
    custom_params: dict[str, str] = Field(default_factory=dict)


class ConsumerLaunchInitiateResponse(BaseModel):
    auth_request_url: str
    state: str
    nonce: str
    launch_hint: str


class ConsumerLaunchCompleteRequest(BaseModel):
    tool_id: str
    id_token: str
    state: str
    nonce: str


class ConsumerLaunchCompleteResponse(BaseModel):
    launch_status: str
    user_binding: dict[str, str]
    resource_context: dict[str, str]


def session_expiry(hours: int = 1) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)
