from __future__ import annotations

import json
import os
from dataclasses import dataclass

from backend.services.shared.models.tenant import TenantContract

_PLAN_CAPABILITIES_ENV = "SUBSCRIPTION_PLAN_CAPABILITIES_JSON"


@dataclass(frozen=True)
class EntitlementResolution:
    capabilities: set[str]


def _read_plan_capability_mapping() -> dict[str, set[str]]:
    """Load plan->capabilities mapping from runtime subscription configuration.

    The mapping is sourced dynamically from an environment payload so plan changes
    do not require tenant-data writes or source-code updates.
    """

    raw_mapping = os.getenv(_PLAN_CAPABILITIES_ENV, "")
    if not raw_mapping.strip():
        return {}

    try:
        parsed = json.loads(raw_mapping)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, dict):
        return {}

    normalized_mapping: dict[str, set[str]] = {}
    for plan_type, capabilities in parsed.items():
        if not isinstance(plan_type, str) or not isinstance(capabilities, list):
            continue
        normalized_mapping[plan_type.strip().lower()] = {
            capability.strip()
            for capability in capabilities
            if isinstance(capability, str) and capability.strip()
        }
    return normalized_mapping


def resolve_capabilities(tenant: TenantContract) -> EntitlementResolution:
    normalized_tenant = tenant.normalized()
    plan_capability_mapping = _read_plan_capability_mapping()
    return EntitlementResolution(capabilities=set(plan_capability_mapping.get(normalized_tenant.plan_type.lower(), set())))
