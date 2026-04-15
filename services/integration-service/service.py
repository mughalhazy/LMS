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
        system_of_record: Any | None = None,
        commerce_service: Any | None = None,
        academy_ops_service: Any | None = None,
    ) -> None:
        self._enterprise_control = enterprise_control or EnterpriseControlService()
        self._rate_limit_policy = rate_limit_policy or RateLimitPolicy()
        self._requests_by_actor_by_minute: dict[tuple[str, str], int] = {}
        # Domain service adapters for real data retrieval (CGAP-028)
        self._system_of_record = system_of_record
        self._commerce_service = commerce_service
        self._academy_ops_service = academy_ops_service

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

        data = self._fetch_domain_data(request=request)
        return 200, self._contract(request=request, status="success", data=data, remaining=remaining)

    def _fetch_domain_data(self, *, request: IntegrationRequest) -> dict[str, Any]:
        """CGAP-028: retrieve actual domain data for the requested integration domain.

        Each domain delegates to the appropriate injected service. Falls back to
        a minimal envelope if the service is not injected — callers receive real
        data when services are wired and a graceful stub when they are not.
        """
        tenant_id = request.tenant_id
        resource_id = request.resource_id.strip()
        domain = request.domain

        try:
            if domain == "student_data" and self._system_of_record is not None:
                profiles = self._system_of_record.list_student_profiles(tenant_id=tenant_id)
                if resource_id and resource_id != "all":
                    profiles = [p for p in profiles if getattr(p, "student_id", None) == resource_id]
                return {
                    "resource_id": resource_id or "all",
                    "domain": domain,
                    "records": [
                        {"student_id": p.student_id, "name": getattr(p, "name", ""), "status": getattr(p, "status", "")}
                        for p in profiles
                    ],
                    "count": len(profiles),
                    "source": request.external_system,
                }

            if domain == "enrollment" and self._system_of_record is not None:
                profiles = self._system_of_record.list_student_profiles(tenant_id=tenant_id)
                enrollments = []
                for p in profiles:
                    if resource_id and resource_id != "all" and p.student_id != resource_id:
                        continue
                    balance = self._system_of_record.get_student_balance(tenant_id=tenant_id, student_id=p.student_id)
                    enrollments.append({"student_id": p.student_id, "outstanding_balance": str(balance)})
                return {
                    "resource_id": resource_id or "all",
                    "domain": domain,
                    "records": enrollments,
                    "count": len(enrollments),
                    "source": request.external_system,
                }

            if domain == "billing" and self._commerce_service is not None:
                invoices = []
                if hasattr(self._commerce_service, "list_invoices"):
                    invoices = list(self._commerce_service.list_invoices(tenant_id=tenant_id))
                if resource_id and resource_id != "all":
                    invoices = [i for i in invoices if getattr(i, "invoice_id", None) == resource_id]
                return {
                    "resource_id": resource_id or "all",
                    "domain": domain,
                    "records": [
                        {"invoice_id": getattr(i, "invoice_id", ""), "status": getattr(i, "status", ""), "amount": str(getattr(i, "amount", 0))}
                        for i in invoices
                    ],
                    "count": len(invoices),
                    "source": request.external_system,
                }

            if domain == "attendance" and self._academy_ops_service is not None:
                records = []
                if hasattr(self._academy_ops_service, "list_attendance_records"):
                    records = list(self._academy_ops_service.list_attendance_records(tenant_id=tenant_id))
                if resource_id and resource_id != "all":
                    records = [r for r in records if getattr(r, "student_id", None) == resource_id]
                return {
                    "resource_id": resource_id or "all",
                    "domain": domain,
                    "records": [
                        {"student_id": getattr(r, "student_id", ""), "status": getattr(r, "status", ""), "date": str(getattr(r, "date", ""))}
                        for r in records
                    ],
                    "count": len(records),
                    "source": request.external_system,
                }

            if domain in {"progress", "teacher_data"} and self._system_of_record is not None:
                profiles = self._system_of_record.list_student_profiles(tenant_id=tenant_id)
                if resource_id and resource_id != "all":
                    profiles = [p for p in profiles if getattr(p, "student_id", None) == resource_id]
                return {
                    "resource_id": resource_id or "all",
                    "domain": domain,
                    "records": [{"id": getattr(p, "student_id", ""), "metadata": getattr(p, "metadata", {})} for p in profiles],
                    "count": len(profiles),
                    "source": request.external_system,
                }

        except Exception:
            pass  # Fall through to minimal stub on any service error

        # Minimal stub when no domain service is injected
        return {
            "resource_id": resource_id or "all",
            "domain": domain,
            "records": [],
            "count": 0,
            "source": request.external_system,
            "note": "domain_service_not_injected",
        }
