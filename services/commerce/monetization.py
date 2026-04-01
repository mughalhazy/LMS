from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from .catalog import Product
from shared.models.capability_pricing import CapabilityPricing
from shared.utils.entitlement import TenantEntitlementContext

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_SubscriptionModule = _load_module("subscription_service_module_for_monetization", "services/subscription-service/service.py")
_CapabilityModule = _load_module("capability_registry_module_for_monetization", "services/capability-registry/service.py")
_EntitlementModule = _load_module("entitlement_service_module_for_monetization", "services/entitlement-service/service.py")

SubscriptionService = _SubscriptionModule.SubscriptionService
CapabilityRegistryService = _CapabilityModule.CapabilityRegistryService
EntitlementService = _EntitlementModule.EntitlementService


@dataclass(frozen=True)
class CapabilityCharge:
    capability_id: str
    units: int
    amount: Decimal
    usage_based: bool


class CapabilityMonetizationService:
    """Capability monetization as a thin layer on top of subscription + entitlement services."""

    def __init__(
        self,
        *,
        subscription_service: SubscriptionService,
        capability_registry: CapabilityRegistryService,
        entitlement_service: EntitlementService,
    ) -> None:
        self._subscription_service = subscription_service
        self._capability_registry = capability_registry
        self._entitlement_service = entitlement_service

    def plan_capability_mapping(self, plan_type: str) -> set[str]:
        """Single billing unit is capability_id; plans resolve to sets of capability_ids."""
        return self._capability_registry.list_plan_capabilities(plan_type)

    def enable_add_on(self, *, tenant_id: str, capability_id: str) -> None:
        if self._capability_registry.get_capability(capability_id) is None:
            raise ValueError(f"unknown capability '{capability_id}'")
        self._subscription_service.purchase_capability_add_on(tenant_id, capability_id)

    def usage_billing_hook(self, *, tenant_id: str, capability_id: str, units: int = 1) -> None:
        capability = self._capability_registry.get_capability(capability_id)
        if capability is None:
            raise ValueError(f"unknown capability '{capability_id}'")
        if units < 0:
            raise ValueError("units must be >= 0")
        if units == 0:
            return

        self._subscription_service.record_capability_usage(
            tenant_id=tenant_id,
            capability_id=capability.capability_id,
            units=units,
        )

    def resolve_capability_unit_price(self, capability_id: str) -> Decimal:
        capability = self._capability_registry.get_capability(capability_id.strip())
        if capability is None:
            raise ValueError(f"unknown capability '{capability_id}'")
        return Decimal(capability.price)

    def quote_product_amount(self, product: Product) -> Decimal:
        """Capability-driven rating hook for commerce product checkout."""
        unit_price = self.resolve_capability_unit_price(product.primary_capability_id)
        units = int(product.metadata.get("monetization_units", "1"))
        if units <= 0:
            raise ValueError("monetization_units must be >= 1")
        return unit_price * units

    def calculate_tenant_capability_charges(self, tenant: TenantEntitlementContext) -> list[CapabilityCharge]:
        normalized_tenant = tenant.normalized()
        usage = self._subscription_service.get_usage_for_tenant(normalized_tenant.tenant_id)
        purchased_add_ons = self._subscription_service.get_purchased_capability_add_ons(normalized_tenant.tenant_id)
        charges: list[CapabilityCharge] = []

        for capability in self._capability_registry.list_capabilities():
            is_enabled = self._entitlement_service.is_enabled(normalized_tenant, capability.capability_id)
            if capability.capability_id in purchased_add_ons:
                is_enabled = True
            if not is_enabled:
                continue

            pricing = CapabilityPricing(
                capability_id=capability.capability_id,
                price=capability.price,
                usage_based=capability.usage_based,
            )
            amount = self._subscription_service.calculate_capability_charge(
                tenant_id=normalized_tenant.tenant_id,
                pricing=pricing,
            )
            units = usage.get(capability.capability_id, 1 if not capability.usage_based else 0)
            if amount <= Decimal("0"):
                continue

            charges.append(
                CapabilityCharge(
                    capability_id=capability.capability_id,
                    units=units,
                    amount=amount,
                    usage_based=capability.usage_based,
                )
            )

        return sorted(charges, key=lambda charge: charge.capability_id)
