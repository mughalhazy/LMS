from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    SAML = "saml"
    OAUTH2 = "oauth2"
    OIDC = "oidc"


class SAMLConfig(BaseModel):
    idp_entity_id: str
    idp_sso_url: str
    idp_x509_certificate: str
    sp_entity_id: str
    acs_url: str
    nameid_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    attribute_mapping: Dict[str, str] = Field(default_factory=lambda: {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "role": "role",
    })
    assertion_signature_required: bool = True
    response_signature_required: bool = True


class OAuth2Config(BaseModel):
    client_id: str
    client_secret: str
    authorization_endpoint: str
    token_endpoint: str
    redirect_uri: str
    scopes: list[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    userinfo_endpoint_or_introspection_endpoint: str
    state_validation_enabled: bool = True
    pkce_required: bool = False


class OIDCConfig(BaseModel):
    issuer: str
    client_id: str
    client_secret: Optional[str] = None
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    redirect_uri: str
    scopes: list[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    nonce_validation_enabled: bool = True
    claim_mapping: Dict[str, str] = Field(default_factory=lambda: {
        "sub": "sub",
        "email": "email",
        "name": "name",
        "roles": "roles",
    })


class InitiateSSORequest(BaseModel):
    tenant_id: str
    provider: ProviderType
    relay_state: Optional[str] = None
    nonce: Optional[str] = None
    config: Dict[str, Any]


class CallbackRequest(BaseModel):
    tenant_id: str
    provider: ProviderType
    payload: Dict[str, Any]


class AuthenticatedIdentity(BaseModel):
    tenant_id: str
    provider: ProviderType
    subject: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    claims: Dict[str, Any] = Field(default_factory=dict)


class SSOInitResponse(BaseModel):
    provider: ProviderType
    flow: str
    redirect_url: str
    correlation_id: str


class SSOCallbackResponse(BaseModel):
    provider: ProviderType
    flow: str
    session_id: str
    identity: AuthenticatedIdentity
