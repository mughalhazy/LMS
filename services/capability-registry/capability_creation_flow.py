from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import importlib.util
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.capability import Capability
from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope
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


RegistryService = _load_module("registry_service_for_minting", "services/capability-registry/service.py").CapabilityRegistryService
SubscriptionService = _load_module("subscription_service_for_minting", "services/subscription-service/service.py").SubscriptionService
ConfigService = _load_module("config_service_for_minting", "services/config-service/service.py").ConfigService
EntitlementService = _load_module("entitlement_service_for_minting", "services/entitlement-service/service.py").EntitlementService


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
    """Create a new capability once and make it available end-to-end."""

    def __init__(self) -> None:
        self.registry = RegistryService()
        self.subscription = SubscriptionService()
        self.config = ConfigService()
        self.entitlement = EntitlementService(
            subscription_service=self.subscription,
            config_service=self.config,
            capability_registry_service=self.registry,
        )

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
            self.config.upsert_override(
                ConfigOverride(
                    scope=ConfigScope(level=ConfigLevel.GLOBAL, scope_id="global"),
                    capability_enabled={capability.capability_id: True},
                    behavior_tuning={},
                )
            )

        return capability

    def is_usable_via_entitlement(self, tenant: TenantEntitlementContext, capability_id: str) -> bool:
        self.entitlement.upsert_tenant_context(tenant)
        return self.entitlement.is_enabled(tenant, capability_id)
