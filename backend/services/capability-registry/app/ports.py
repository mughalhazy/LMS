from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class EntitlementRegistryReaderPort(ABC):
    """B15-022: Read-only contract exposing the capability registry to the entitlement service.
    Prevents direct store coupling across service boundaries."""

    @abstractmethod
    def get_capability(self, key: str) -> Optional[Dict[str, Any]]:
        """Return serialised CapabilityRecord for key, or None if not found."""

    @abstractmethod
    def list_capabilities(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all capabilities, optionally filtered by domain."""

    @abstractmethod
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Return key → direct_deps mapping for entitlement dependency resolution."""

    @abstractmethod
    def capability_exists(self, key: str) -> bool:
        """Return True if capability key is present and active in the registry."""


class CapabilityModuleInterface(ABC):
    """B15-034: Runtime interface every capability plug-in must implement.
    Governs the enable/disable lifecycle, dependency validation, usage hooks,
    and config injection per capability-interface-contract.md."""

    @property
    @abstractmethod
    def capability_key(self) -> str:
        """Unique capability identifier (e.g. 'CAP-VIDEO-STREAMING')."""

    @abstractmethod
    def enable(self, tenant_id: str, config: Dict[str, Any]) -> None:
        """Called when a tenant activates this capability. Inject config and set up state."""

    @abstractmethod
    def disable(self, tenant_id: str) -> None:
        """Called when a tenant deactivates this capability. Clean up tenant state."""

    @abstractmethod
    def validate_dependencies(self, registry: EntitlementRegistryReaderPort) -> List[str]:
        """Return list of missing required dependency keys, empty list if all satisfied."""

    @abstractmethod
    def on_usage(self, tenant_id: str, usage_event: Dict[str, Any]) -> None:
        """Called on every usage event for this capability. Used for metering hooks."""

    @abstractmethod
    def inject_config(self, config: Dict[str, Any]) -> None:
        """Hot-reload config without restart. Called when config-service propagates changes."""


class InProcessEntitlementRegistryReader(EntitlementRegistryReaderPort):
    """Concrete adapter that wraps CapabilityRegistryService for in-process use."""

    def __init__(self, service) -> None:
        self._service = service

    def get_capability(self, key: str) -> Optional[Dict[str, Any]]:
        status, body = self._service.get_capability(key)
        return body if status == 200 else None

    def list_capabilities(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        _, body = self._service.list_capabilities()
        caps = body.get("capabilities", [])
        if domain:
            caps = [c for c in caps if c.get("domain") == domain]
        return caps

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        _, body = self._service.get_dependency_graph()
        return body.get("graph", {})

    def capability_exists(self, key: str) -> bool:
        status, body = self._service.get_capability(key)
        return status == 200 and body.get("lifecycle_status") == "active"
