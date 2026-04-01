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


    def resolve_communication_routing(
        self,
        context: ConfigResolutionContext,
        *,
        capability_id: str = "whatsapp_primary_interface",
        default_priority: tuple[str, ...] = ("whatsapp", "sms", "email"),
    ) -> tuple[str, ...]:
        """Resolve communication routing order from effective config + capability flag."""
        effective = self.resolve(context)

        configured_priority = (
            effective.behavior_tuning.get("communication", {}).get("routing_priority", default_priority)
        )
        if isinstance(configured_priority, str):
            candidate_order = [configured_priority]
        else:
            candidate_order = [str(item).strip().lower() for item in configured_priority if str(item).strip()]

        if effective.capability_enabled.get(capability_id, False):
            candidate_order.insert(0, "whatsapp")

        supported_channels = {"whatsapp", "sms", "email"}
        order: list[str] = []
        for channel in candidate_order:
            if channel in supported_channels and channel not in order:
                order.append(channel)

        return tuple(order or ["sms"])

    def resolve_capability_entitlement(self, context: ConfigResolutionContext, capability: str) -> bool | None:
        """Config contribution for entitlement engine (`None` means no override)."""
        effective = self.resolve(context)
        return effective.capability_enabled.get(capability)

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


    def resolve_onboarding_mode(self, context: ConfigResolutionContext) -> str:
        """Resolve onboarding mode preferring WhatsApp-first operation."""
        effective = self.resolve(context)
        onboarding = effective.behavior_tuning.get("onboarding", {})
        preferred = str(onboarding.get("preferred_channel", "whatsapp")).strip().lower()
        dashboard_required = bool(onboarding.get("dashboard_required", False))
        if preferred == "whatsapp" and not dashboard_required:
            return "whatsapp_first"
        return "dashboard"
