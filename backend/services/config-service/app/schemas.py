from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResolutionContext:
    tenant_id: str
    country_code: str
    segment_key: str
    plan_key: str
    runtime_selectors: Dict[str, str] = field(default_factory=dict)
    capability_key: Optional[str] = None
    overrides: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolveKeyRequest:
    context: Dict[str, Any]
    key: str
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolveKeysRequest:
    context: Dict[str, Any]
    keys: List[str]
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolveNamespaceRequest:
    context: Dict[str, Any]
    namespace: str
    options: Dict[str, Any] = field(default_factory=dict)
