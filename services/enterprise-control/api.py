from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_EnterpriseControlServiceModule = _load_module("enterprise_control_service_api_module", "services/enterprise-control/service.py")
_IntegrationServiceModule = _load_module("integration_service_api_module", "services/integration-service/service.py")
EnterpriseControlService = _EnterpriseControlServiceModule.EnterpriseControlService
IdentityContext = _EnterpriseControlServiceModule.IdentityContext
IntegrationAPIService = _IntegrationServiceModule.IntegrationAPIService
IntegrationRequest = _IntegrationServiceModule.IntegrationRequest


class EnterpriseControlAPI:
    """Aggregated API surface for enterprise controls and integration endpoints."""

    def __init__(self, *, control_service: EnterpriseControlService | None = None) -> None:
        self._control = control_service or EnterpriseControlService()
        self._integrations = IntegrationAPIService(enterprise_control=self._control)

    def authorize(self, *, identity: IdentityContext, payload: dict[str, str]) -> tuple[int, dict[str, Any]]:
        return self._control.api_authorize(
            identity=identity,
            action=payload["action"],
            resource=payload["resource"],
            permission=payload["permission"],
            tenant_id=payload["tenant_id"],
        )

    def fetch_integration_data(self, *, identity: IdentityContext, payload: dict[str, str]) -> tuple[int, dict[str, Any]]:
        request = IntegrationRequest(
            request_id=payload["request_id"],
            tenant_id=payload["tenant_id"],
            domain=payload["domain"],
            external_system=payload["external_system"],
            resource_id=payload.get("resource_id", ""),
        )
        return self._integrations.get_domain_payload(identity=identity, request=request)
