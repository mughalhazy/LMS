from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class InstitutionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class RelationshipType(str, Enum):
    GOVERNANCE_PARENT = "governance_parent"
    AFFILIATE = "affiliate"
    ACADEMIC_PARTNERSHIP = "academic_partnership"


class LinkScope(str, Enum):
    PRIMARY = "primary"
    AFFILIATE = "affiliate"
    DELIVERY = "delivery"


SYSTEM_INSTITUTION_TYPES = {
    "school",
    "university",
    "academy",
    "tutor_organization",
    "corporate_training_organization",
}


@dataclass
class InstitutionType:
    type_code: str
    type_name: str
    governance_profile: dict[str, Any] = field(default_factory=dict)
    is_system_type: bool = False


@dataclass
class Institution:
    institution_id: str
    institution_type: str
    legal_name: str
    display_name: str
    tenant_id: str
    status: InstitutionStatus = InstitutionStatus.DRAFT
    registration_country: str | None = None
    default_locale: str = "en-US"
    timezone: str = "UTC"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class InstitutionHierarchyEdge:
    edge_id: str
    parent_institution_id: str
    child_institution_id: str
    relationship_type: RelationshipType
    status: str = "active"
    effective_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    effective_to: datetime | None = None


@dataclass
class InstitutionTenantLink:
    link_id: str
    institution_id: str
    tenant_id: str
    link_scope: LinkScope
    status: str = "active"
    linked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    payload: dict[str, Any]
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
