from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.config import (
    ConfigLevel,
    ConfigOverride,
    ConfigResolutionContext,
    ConfigScope,
    EffectiveConfig,
)


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


class ConfigService:
    """Single source of truth for runtime config overrides.

    All services should request effective configuration through this service.
    """

    _precedence = [ConfigLevel.GLOBAL, ConfigLevel.COUNTRY, ConfigLevel.SEGMENT, ConfigLevel.TENANT]

    def __init__(self) -> None:
        self._overrides: dict[tuple[ConfigLevel, str], ConfigOverride] = {}

    def upsert_override(self, override: ConfigOverride) -> None:
        self._overrides[(override.scope.level, override.scope.scope_id)] = override

    def remove_override(self, *, level: ConfigLevel, scope_id: str) -> None:
        self._overrides.pop((level, scope_id), None)

    def get_override(self, *, level: ConfigLevel, scope_id: str) -> ConfigOverride | None:
        return self._overrides.get((level, scope_id))

    def resolve(self, context: ConfigResolutionContext) -> EffectiveConfig:
        path = [
            ConfigScope(level=ConfigLevel.GLOBAL, scope_id="global"),
            ConfigScope(level=ConfigLevel.COUNTRY, scope_id=context.country_code),
            ConfigScope(level=ConfigLevel.SEGMENT, scope_id=context.segment_id),
            ConfigScope(level=ConfigLevel.TENANT, scope_id=context.tenant_id),
        ]

        ordered = sorted(path, key=lambda item: self._precedence.index(item.level))
        capability_enabled: dict[str, bool] = {}
        behavior_tuning: dict[str, Any] = {}

        for scope in ordered:
            override = self.get_override(level=scope.level, scope_id=scope.scope_id)
            if not override:
                continue
            capability_enabled.update(override.capability_enabled)
            behavior_tuning = _deep_merge(behavior_tuning, override.behavior_tuning)

        return EffectiveConfig(
            capability_enabled=capability_enabled,
            behavior_tuning=behavior_tuning,
        )

    def has_conflicting_config_paths(self) -> bool:
        seen: set[tuple[ConfigLevel, str, str]] = set()
        for override in self._overrides.values():
            for capability_id in override.capability_enabled:
                path = (override.scope.level, override.scope.scope_id, f"capability.{capability_id}.enabled")
                if path in seen:
                    return True
                seen.add(path)
            for behavior_key in override.behavior_tuning:
                path = (override.scope.level, override.scope.scope_id, f"behavior.{behavior_key}")
                if path in seen:
                    return True
                seen.add(path)
        return False
