from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class CreateInstitutionRequest:
    institution_type: str
    legal_name: str
    display_name: str
    tenant_id: str
    registration_country: str
    default_locale: str = "en-US"
    timezone: str = "UTC"
    metadata: dict[str, Any] = field(default_factory=dict)
    actor_id: str = "system"


@dataclass
class UpdateInstitutionRequest:
    display_name: str | None = None
    default_locale: str | None = None
    timezone: str | None = None
    metadata: dict[str, Any] | None = None
    actor_id: str = "system"


@dataclass
class TransitionInstitutionRequest:
    actor_id: str
    reason: str


@dataclass
class CreateHierarchyEdgeRequest:
    parent_institution_id: str
    relationship_type: str
    actor_id: str
    reason: str


@dataclass
class ReparentInstitutionRequest:
    new_parent_institution_id: str
    relationship_type: str
    actor_id: str
    reason: str


@dataclass
class CreateInstitutionTypeRequest:
    type_code: str
    type_name: str
    governance_profile: dict[str, Any] = field(default_factory=dict)


@dataclass
class CreateTenantLinkRequest:
    tenant_id: str
    link_scope: str
    actor_id: str
    effective_from: date | None = None


@dataclass
class InstitutionResponse:
    institution_id: str
    institution_type: str
    legal_name: str
    display_name: str
    tenant_id: str
    status: str


@dataclass
class HealthResponse:
    status: str
    service: str


@dataclass
class MetricsResponse:
    service: str
    service_up: int
    institutions_total: int
    active_links_total: int
