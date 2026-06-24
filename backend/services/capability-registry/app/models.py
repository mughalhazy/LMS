from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CapabilityRecord:
    key: str
    domain: str
    description: str
    dependencies: List[str]
    usage_metrics: List[str]
    billing_type: str
    required_adapters: List[str]
    lifecycle_status: str  # draft | active | deprecated
    owner: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    change_reason: str = ""
    add_on_refs: List[str] = field(default_factory=list)
    activation_metadata: Dict[str, Any] = field(default_factory=dict)
    business_impact_description: str = ""  # B08-005: BC-LANG-01 — operator-language description required at registration


@dataclass
class RegistrySnapshot:
    version: str
    capabilities: Dict[str, CapabilityRecord]
    dependency_index: Dict[str, List[str]]   # key → direct deps
    reverse_index: Dict[str, List[str]]       # key → dependents
    published_at: datetime
    integrity_digest: str


@dataclass
class RegistryDraft:
    draft_id: str
    changes: List[Dict[str, Any]]
    created_by: str
    created_at: datetime
    validation_errors: List[str] = field(default_factory=list)
    status: str = "pending"  # pending | validated | rejected
