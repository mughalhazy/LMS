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


_ServiceModule = _load_module("integration_service_api_facade_module", "services/integration-service/service.py")
IntegrationAPIService = _ServiceModule.IntegrationAPIService
IntegrationRequest = _ServiceModule.IntegrationRequest


class IntegrationAPI:
    """Thin API facade to provide stable method contracts for integration consumers."""

    def __init__(self, *, service: IntegrationAPIService | None = None) -> None:
        self._service = service or IntegrationAPIService()

    def fetch(self, *, identity: Any, payload: dict[str, str]) -> tuple[int, dict[str, Any]]:
        request = IntegrationRequest(
            request_id=payload["request_id"],
            tenant_id=payload["tenant_id"],
            domain=payload["domain"],
            external_system=payload["external_system"],
            resource_id=payload.get("resource_id", ""),
        )
        return self._service.get_domain_payload(identity=identity, request=request)
