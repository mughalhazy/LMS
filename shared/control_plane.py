from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from shared.models.config import ConfigResolutionContext

ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    sys.path.insert(0, str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


CapabilityRegistryService = _load(
    "capability_registry_control_plane",
    "services/capability-registry/service.py",
).CapabilityRegistryService
ConfigService = _load("config_control_plane", "services/config-service/service.py").ConfigService
EntitlementService = _load("entitlement_control_plane", "services/entitlement-service/service.py").EntitlementService


@dataclass(frozen=True)
class RuntimeServiceBinding:
    service_name: str
    endpoint: str


@dataclass(frozen=True)
class ControlPlaneClients:
    capability_registry: CapabilityRegistryService
    config_service: ConfigService
    entitlement_service: EntitlementService


@dataclass(frozen=True)
class ControlPlaneClient:
    capability_registry: CapabilityRegistryService
    config_service: ConfigService
    entitlement_service: EntitlementService

    def get_capability(self, capability_id: str):
        return self.capability_registry.get_capability(capability_id)

    def is_enabled(self, tenant_context, capability_id: str) -> bool:
        return self.entitlement_service.is_enabled(tenant_context, capability_id)

    def get_config(self, context: ConfigResolutionContext):
        return self.config_service.resolve(context)


def _endpoint_for(service_name: str) -> str:
    env_key = service_name.upper().replace("-", "_") + "_URL"
    return os.getenv(env_key, f"discovery://{service_name}")


RUNTIME_SERVICE_REGISTRY: dict[str, RuntimeServiceBinding] = {
    "capability-registry": RuntimeServiceBinding(
        service_name="capability-registry",
        endpoint=_endpoint_for("capability-registry"),
    ),
    "config-service": RuntimeServiceBinding(
        service_name="config-service",
        endpoint=_endpoint_for("config-service"),
    ),
    "entitlement-service": RuntimeServiceBinding(
        service_name="entitlement-service",
        endpoint=_endpoint_for("entitlement-service"),
    ),
}


def build_control_plane_clients(
    *,
    config_factory: Callable[[], ConfigService] = ConfigService,
    capability_registry_factory: Callable[[], CapabilityRegistryService] = CapabilityRegistryService,
    entitlement_factory: Callable[..., EntitlementService] = EntitlementService,
) -> ControlPlaneClients:
    config_service = config_factory()
    capability_registry = capability_registry_factory()
    entitlement_service = entitlement_factory(
        config_service=config_service,
        capability_registry_service=capability_registry,
    )
    return ControlPlaneClients(
        capability_registry=capability_registry,
        config_service=config_service,
        entitlement_service=entitlement_service,
    )


def build_control_plane_client(
    *,
    config_factory: Callable[[], ConfigService] = ConfigService,
    capability_registry_factory: Callable[[], CapabilityRegistryService] = CapabilityRegistryService,
    entitlement_factory: Callable[..., EntitlementService] = EntitlementService,
) -> ControlPlaneClient:
    clients = build_control_plane_clients(
        config_factory=config_factory,
        capability_registry_factory=capability_registry_factory,
        entitlement_factory=entitlement_factory,
    )
    return ControlPlaneClient(
        capability_registry=clients.capability_registry,
        config_service=clients.config_service,
        entitlement_service=clients.entitlement_service,
    )
