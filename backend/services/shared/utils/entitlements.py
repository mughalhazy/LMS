from __future__ import annotations

from dataclasses import dataclass

from backend.services.shared.models.tenant import TenantContract


PLAN_CAPABILITY_MAP: dict[str, set[str]] = {
    "free": {"course.read"},
    "pro": {"course.read", "assessment.attempt", "recommendation.basic"},
    "enterprise": {
        "course.read",
        "course.write",
        "assessment.attempt",
        "assessment.author",
        "ai.tutor",
        "recommendation.basic",
        "recommendation.advanced",
        "analytics.read",
    },
}

ADDON_CAPABILITY_MAP: dict[str, set[str]] = {
    "ai_tutor": {"ai.tutor"},
    "advanced_recommendations": {"recommendation.advanced"},
    "assessment_authoring": {"assessment.author"},
}

SEGMENT_CAPABILITY_MAP: dict[str, set[str]] = {
    "enterprise": {"analytics.read"},
    "edu": {"assessment.author"},
}

COUNTRY_RESTRICTIONS: dict[str, set[str]] = {
    "DE": {"recommendation.advanced"},
}


@dataclass(frozen=True)
class EntitlementResolution:
    capabilities: set[str]


def resolve_capabilities(tenant: TenantContract) -> EntitlementResolution:
    normalized = tenant.normalized()
    capabilities = set(PLAN_CAPABILITY_MAP.get(normalized.plan_type, set()))
    capabilities.update(SEGMENT_CAPABILITY_MAP.get(normalized.segment_type, set()))
    for addon in normalized.addon_flags:
        capabilities.update(ADDON_CAPABILITY_MAP.get(addon, set()))
    capabilities.difference_update(COUNTRY_RESTRICTIONS.get(normalized.country_code, set()))
    return EntitlementResolution(capabilities=capabilities)


def is_capability_enabled(tenant: TenantContract, capability: str) -> bool:
    return capability in resolve_capabilities(tenant).capabilities
