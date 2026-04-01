from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from shared.models.capability import Capability
from shared.utils.entitlement import TenantEntitlementContext

from service import CapabilityRegistryService


class CapabilityEntitlementGateway(Protocol):
    def is_enabled(self, tenant: TenantEntitlementContext, capability_id: str) -> bool: ...


@dataclass(frozen=True)
class CapabilityMintRequest:
    capability_id: str
    name: str
    description: str
    category: str
    price: Decimal
    usage_based: bool = False
    default_enabled: bool = False
    included_in_plans: tuple[str, ...] = ()
    included_in_add_ons: tuple[str, ...] = ()
    feature_ids: tuple[str, ...] = ()
    enable_globally: bool = False


class CapabilityMintingFlow:
    """Create capabilities in registry and expose them via boundary-safe contracts."""

    def __init__(
        self,
        *,
        registry: CapabilityRegistryService | None = None,
        entitlement_gateway: CapabilityEntitlementGateway | None = None,
    ) -> None:
        self.registry = registry or CapabilityRegistryService()
        self._entitlement_gateway = entitlement_gateway
        self._globally_enabled: set[str] = set()

    def mint(self, request: CapabilityMintRequest) -> Capability:
        capability = Capability(
            capability_id=request.capability_id.strip(),
            name=request.name.strip(),
            description=request.description.strip(),
            category=request.category.strip(),
            default_enabled=bool(request.default_enabled),
            price=request.price,
            usage_based=bool(request.usage_based),
            included_in_plans=request.included_in_plans,
            included_in_add_ons=request.included_in_add_ons,
        )

        self.registry.register_capability(capability, feature_ids=request.feature_ids)

        if request.enable_globally:
            self._globally_enabled.add(capability.capability_id)

        return capability

    def is_usable_via_entitlement(self, tenant: TenantEntitlementContext, capability_id: str) -> bool:
        normalized = tenant.normalized()
        normalized_capability = capability_id.strip()
        if self._entitlement_gateway is not None:
            return self._entitlement_gateway.is_enabled(normalized, normalized_capability)
        capability = self.registry.get_capability(normalized_capability)
        if capability is None:
            return False
        if normalized_capability in self._globally_enabled:
            return True
        if capability.default_enabled:
            return True
        if normalized.plan_type in capability.included_in_plans:
            return True
        return any(add_on in capability.included_in_add_ons for add_on in normalized.add_ons)
