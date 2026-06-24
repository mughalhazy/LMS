from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CapabilityDraftEntry:
    key: str
    domain: str
    description: str
    dependencies: List[str]
    usage_metrics: List[str]
    billing_type: str
    required_adapters: List[str]
    owner: str
    lifecycle_status: str = "active"
    add_on_refs: List[str] = field(default_factory=list)
    activation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubmitDraftRequest:
    created_by: str
    changes: List[Dict[str, Any]]


@dataclass
class PublishDraftRequest:
    draft_id: str
    published_by: str
