from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.capability import Capability

from store import capability_index, feature_capability_mapping


class CapabilityRegistryService:
    def get_capability(self, capability_id: str) -> Capability | None:
        return capability_index().get(capability_id.strip())

    def list_capabilities(self) -> list[Capability]:
        return sorted(capability_index().values(), key=lambda item: item.capability_id)

    def get_capability_for_feature(self, feature_id: str) -> Capability | None:
        mapped_capability_id = feature_capability_mapping().get(feature_id.strip())
        if not mapped_capability_id:
            return None
        return self.get_capability(mapped_capability_id)


    def is_enabled_by_default(self, capability_id: str) -> bool:
        """Registry default signal consumed by entitlement service only."""
        capability = self.get_capability(capability_id)
        return bool(capability.default_enabled) if capability else False
