from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class EntitlementContext:
    tenant_id: str
    segment: str
    plan: str
    country: str
    add_ons: List[str] = field(default_factory=list)
    policy_snapshot_version: Optional[str] = None
    registry_snapshot_version: Optional[str] = None


@dataclass
class CapabilityDecision:
    key: str
    enabled: bool
    reasons: List[str] = field(default_factory=list)


@dataclass
class PolicyEntry:
    capability_key: str
    granted: bool  # True = grant, False = deny
    source: str    # "base_plan" | "addon:<key>"
    segment: Optional[str] = None
    plan: Optional[str] = None
    country: Optional[str] = None
    add_on: Optional[str] = None


@dataclass
class CapabilityMeta:
    key: str
    dependencies: List[str] = field(default_factory=list)
    deprecated: bool = False


@dataclass
class EntitlementResult:
    decisions: Dict[str, CapabilityDecision]
    normalized_context: Dict[str, object]
    policy_revision: str
    registry_version: str
    resolved_at: datetime
    evaluation_order: List[str] = field(default_factory=list)
