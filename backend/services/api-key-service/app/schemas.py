from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ApiKeyCreateRequest:
    tenant_id: str
    name: str
    scopes: List[str]
    created_by: str


@dataclass
class ApiKeyRotateRequest:
    tenant_id: str
    key_id: str
    rotated_by: str


@dataclass
class ApiKeyAuthorizeRequest:
    tenant_id: str
    api_key: str
    required_scope: str


@dataclass
class ApiKeyUsageReportRequest:
    tenant_id: str
    key_id: str


ALLOWED_SCOPES = {
    "integrations:hris.sync",
    "integrations:crm.upsert",
    "integrations:lti.launch",
    "integrations:webhooks.publish",
    "integrations:*",
}
