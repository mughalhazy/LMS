from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

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


_EnterpriseControlModule = _load_module("enterprise_control_service_for_integration", "services/enterprise-control/service.py")
EnterpriseControlService = _EnterpriseControlModule.EnterpriseControlService
IdentityContext = _EnterpriseControlModule.IdentityContext

IntegrationDomain = Literal["student_data", "enrollment", "progress", "billing", "attendance", "teacher_data"]
ExternalSystemType = Literal["hr", "erp", "reporting"]


@dataclass(frozen=True)
class RateLimitPolicy:
    requests_per_minute: int = 120


@dataclass(frozen=True)
class IntegrationRequest:
    request_id: str
    tenant_id: str
    domain: IntegrationDomain
    external_system: ExternalSystemType
    resource_id: str


class IntegrationAPIService:
    """Integration APIs with consistent contracts, authN/Z guardrails, and rate-limit readiness."""

    _supported_domains: tuple[IntegrationDomain, ...] = (
        "student_data",
        "enrollment",
        "progress",
        "billing",
        "attendance",
        "teacher_data",
    )

    _supported_systems_by_domain: dict[IntegrationDomain, set[ExternalSystemType]] = {
        "student_data": {"hr", "erp", "reporting"},
        "enrollment": {"hr", "erp", "reporting"},
        "progress": {"erp", "reporting"},
        "billing": {"erp", "reporting"},
        "attendance": {"hr", "erp", "reporting"},
        "teacher_data": {"hr", "erp", "reporting"},
    }

    def __init__(
        self,
        *,
        enterprise_control: EnterpriseControlService | None = None,
        rate_limit_policy: RateLimitPolicy | None = None,
    ) -> None:
        self._enterprise_control = enterprise_control or EnterpriseControlService()
        self._rate_limit_policy = rate_limit_policy or RateLimitPolicy()
        self._requests_by_actor_by_minute: dict[tuple[str, str], int] = {}

    @staticmethod
    def _minute_bucket(now: datetime) -> str:
        return now.astimezone(timezone.utc).strftime("%Y%m%d%H%M")

    def _rate_limit_guard(self, *, actor_id: str, now: datetime) -> tuple[bool, int]:
        bucket = self._minute_bucket(now)
        key = (actor_id.strip(), bucket)
        used = self._requests_by_actor_by_minute.get(key, 0)
        if used >= self._rate_limit_policy.requests_per_minute:
            return False, 0
        self._requests_by_actor_by_minute[key] = used + 1
        remaining = self._rate_limit_policy.requests_per_minute - (used + 1)
        return True, remaining

    @staticmethod
    def _permission_for(domain: IntegrationDomain) -> str:
        return f"integration.read.{domain}"

    @staticmethod
    def _resource_for(domain: IntegrationDomain, resource_id: str) -> str:
        return f"integration:{domain}:{resource_id.strip() or 'all'}"

    def _contract(
        self,
        *,
        request: IntegrationRequest,
        status: str,
        data: dict[str, Any] | None = None,
        error: dict[str, str] | None = None,
        remaining: int,
    ) -> dict[str, Any]:
        return {
            "request_id": request.request_id,
            "status": status,
            "data": data or {},
            "error": error,
            "meta": {
                "tenant_id": request.tenant_id,
                "domain": request.domain,
                "external_system": request.external_system,
                "rate_limit": {
                    "limit_per_minute": self._rate_limit_policy.requests_per_minute,
                    "remaining": max(remaining, 0),
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    def get_domain_payload(self, *, identity: IdentityContext, request: IntegrationRequest) -> tuple[int, dict[str, Any]]:
        if request.domain not in self._supported_domains:
            return 400, self._contract(
                request=request,
                status="error",
                error={"code": "unsupported_domain", "message": f"Unsupported domain: {request.domain}"},
                remaining=self._rate_limit_policy.requests_per_minute,
            )
        if request.external_system not in self._supported_systems_by_domain[request.domain]:
            return 400, self._contract(
                request=request,
                status="error",
                error={"code": "unsupported_external_system", "message": f"{request.external_system} is not allowed for {request.domain}"},
                remaining=self._rate_limit_policy.requests_per_minute,
            )

        now = datetime.now(timezone.utc)
        allowed_by_rate, remaining = self._rate_limit_guard(actor_id=identity.actor_id, now=now)
        if not allowed_by_rate:
            return 429, self._contract(
                request=request,
                status="error",
                error={"code": "rate_limited", "message": "Rate limit exceeded"},
                remaining=0,
            )

        permission = self._permission_for(request.domain)
        auth_status, auth_payload = self._enterprise_control.api_authorize(
            identity=identity,
            action="read",
            resource=self._resource_for(request.domain, request.resource_id),
            permission=permission,
            tenant_id=request.tenant_id,
        )
        if auth_status != 200:
            return 403, self._contract(
                request=request,
                status="error",
                error={"code": "forbidden", "message": auth_payload.get("reason", "authorization_failed")},
                remaining=remaining,
            )

        data = {
            "resource_id": request.resource_id,
            "attributes": {
                "source": request.external_system,
                "sync_hint": "incremental",
                "contract_version": "2026-04-01",
            },
        }
        return 200, self._contract(request=request, status="success", data=data, remaining=remaining)
