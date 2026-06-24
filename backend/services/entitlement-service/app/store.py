from __future__ import annotations

from typing import Dict, List, Optional

from .models import CapabilityMeta, PolicyEntry


class InMemoryPolicyStore:
    """EntitlementPolicyProviderPort — provides commercial entitlement inputs."""

    def __init__(self) -> None:
        self._policies: List[PolicyEntry] = []
        self.revision = "policy-rev-initial"

    def seed(self, policies: List[PolicyEntry]) -> None:
        self._policies.extend(policies)

    def get_base_policies(self, segment: str, plan: str, country: str) -> List[PolicyEntry]:
        return [
            p for p in self._policies
            if p.add_on is None
            and (p.segment is None or p.segment == segment)
            and (p.plan is None or p.plan == plan)
            and (p.country is None or p.country == country)
        ]

    def get_addon_policies(self, add_on: str, segment: str, plan: str, country: str) -> List[PolicyEntry]:
        return [
            p for p in self._policies
            if p.add_on == add_on
            and (p.segment is None or p.segment == segment)
            and (p.plan is None or p.plan == plan)
            and (p.country is None or p.country == country)
        ]


class InMemoryRegistryReader:
    """CapabilityRegistryReaderPort — read-only capability metadata."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityMeta] = {}
        self.version = "registry-initial"

    def seed(self, capabilities: List[CapabilityMeta]) -> None:
        for cap in capabilities:
            self._capabilities[cap.key] = cap

    def get_dependencies(self, key: str) -> List[str]:
        cap = self._capabilities.get(key)
        return cap.dependencies if cap else []

    def all_keys(self) -> List[str]:
        return list(self._capabilities.keys())
