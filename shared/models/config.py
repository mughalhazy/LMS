from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConfigLevel(str, Enum):
    GLOBAL = "global"
    TENANT = "tenant"
    COUNTRY = "country"
    SEGMENT = "segment"


@dataclass(frozen=True)
class ConfigScope:
    level: ConfigLevel
    scope_id: str

    def __post_init__(self) -> None:
        if not self.scope_id.strip():
            raise ValueError("scope_id is required")


@dataclass(frozen=True)
class ConfigOverride:
    scope: ConfigScope
    capability_enabled: dict[str, bool] = field(default_factory=dict)
    behavior_tuning: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.scope.level == ConfigLevel.GLOBAL and self.scope.scope_id != "global":
            raise ValueError("global config must use scope_id='global'")


@dataclass(frozen=True)
class ConfigResolutionContext:
    tenant_id: str
    country_code: str
    segment_id: str


@dataclass(frozen=True)
class EffectiveConfig:
    capability_enabled: dict[str, bool]
    behavior_tuning: dict[str, Any]
