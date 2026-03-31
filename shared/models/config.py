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


@dataclass(frozen=True)
class SegmentBehaviorConfig:
    attendance_enabled: bool = False
    cohort_enabled: bool = False
    guardian_notifications_enabled: bool = False


def segment_behavior_from_effective_config(effective: EffectiveConfig) -> SegmentBehaviorConfig:
    behavior = effective.behavior_tuning.get("segment_behavior", {})
    return SegmentBehaviorConfig(
        attendance_enabled=bool(behavior.get("attendance_enabled", False)),
        cohort_enabled=bool(behavior.get("cohort_enabled", False)),
        guardian_notifications_enabled=bool(behavior.get("guardian_notifications_enabled", False)),
    )
