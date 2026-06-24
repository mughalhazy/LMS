from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ConfigLayer:
    level: str  # global | country | segment | plan | tenant | override
    values: Dict[str, Any]
    revision: str
    fetched_at: datetime


@dataclass
class ResolutionResult:
    values: Dict[str, Any]
    provenance: Dict[str, str]
    applied_levels: List[str]
    revisions: Dict[str, str]
    resolved_at: datetime
    validation: Optional[Dict[str, Any]] = None


@dataclass
class ConfigEntry:
    key: str
    value: Any
    level: str
    revision: str
    tenant_id: Optional[str] = None
    country_code: Optional[str] = None
    segment_key: Optional[str] = None
    plan_key: Optional[str] = None
    capability_key: Optional[str] = None


@dataclass
class RuntimeOverride:
    key: str
    value: Any
    reason: str
    ttl_seconds: int
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
