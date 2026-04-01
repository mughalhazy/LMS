from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.capability import Capability
from shared.models.capability_pricing import CapabilityPricing

from store import capability_index, feature_capability_mapping


class CapabilityRegistryService:
    def register_capability(self, capability: Capability, *, feature_ids: tuple[str, ...] = ()) -> None:
        normalized_capability = Capability(
            capability_id=capability.capability_id.strip(),
            name=capability.name.strip(),
            description=capability.description.strip(),
            category=capability.category.strip(),
            default_enabled=bool(capability.default_enabled),
            monetizable=bool(capability.monetizable),
            usage_metered=bool(capability.usage_metered),
            metadata={
                str(key).strip(): str(value).strip()
                for key, value in capability.metadata.items()
                if str(key).strip() and str(value).strip()
            },
            price=capability.price,
            usage_based=bool(capability.usage_metered),
            included_in_plans=tuple(sorted({plan.strip().lower() for plan in capability.included_in_plans if plan.strip()})),
            included_in_add_ons=tuple(sorted({addon.strip().lower() for addon in capability.included_in_add_ons if addon.strip()})),
        )
        if not normalized_capability.capability_id:
            raise ValueError("capability_id is required")

        index = capability_index()
        index[normalized_capability.capability_id] = normalized_capability

        mapping = feature_capability_mapping()
        for feature_id in feature_ids:
            normalized_feature = feature_id.strip()
            if normalized_feature:
                mapping[normalized_feature] = normalized_capability.capability_id

    def get_capability(self, capability_id: str) -> Capability | None:
        return capability_index().get(capability_id.strip())

    def list_capabilities(self) -> list[Capability]:
        return sorted(capability_index().values(), key=lambda item: item.capability_id)

    def get_capability_for_feature(self, feature_id: str) -> Capability | None:
        mapped_capability_id = feature_capability_mapping().get(feature_id.strip())
        if not mapped_capability_id:
            return None
        return self.get_capability(mapped_capability_id)

    def get_capability_pricing(self, capability_id: str) -> CapabilityPricing | None:
        capability = self.get_capability(capability_id)
        return capability.pricing if capability else None


    def list_plan_capabilities(self, plan_type: str) -> set[str]:
        normalized_plan = plan_type.strip().lower()
        return {
            capability.capability_id
            for capability in self.list_capabilities()
            if normalized_plan in capability.included_in_plans
        }

    def list_add_on_capabilities(self, add_on: str) -> set[str]:
        normalized_add_on = add_on.strip().lower()
        return {
            capability.capability_id
            for capability in self.list_capabilities()
            if normalized_add_on in capability.included_in_add_ons
        }

    def assert_capability_is_single_billing_unit(self, capability_id: str) -> bool:
        capability = self.get_capability(capability_id)
        return capability is not None and bool(capability.capability_id.strip())

    def is_enabled_by_default(self, capability_id: str) -> bool:
        """Registry default signal consumed by entitlement service only."""
        capability = self.get_capability(capability_id)
        return bool(capability.default_enabled) if capability else False
