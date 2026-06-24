from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ResolveRequest:
    tenant_id: str
    segment: str
    plan: str
    country: str
    add_ons: List[str] = field(default_factory=list)
    policy_snapshot_version: Optional[str] = None
    registry_snapshot_version: Optional[str] = None


@dataclass
class IsEnabledRequest:
    tenant_id: str
    segment: str
    plan: str
    country: str
    capability_key: str
    add_ons: List[str] = field(default_factory=list)
