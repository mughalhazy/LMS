from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


service_module = _load("integration_service_test_module", "services/integration-service/service.py")
enterprise_module = _load("enterprise_control_test_module_for_integration", "services/enterprise-control/service.py")
IntegrationAPIService = service_module.IntegrationAPIService
IntegrationRequest = service_module.IntegrationRequest
RateLimitPolicy = service_module.RateLimitPolicy
IdentityContext = enterprise_module.IdentityContext
EnterpriseControlService = enterprise_module.EnterpriseControlService


def test_integration_domains_have_consistent_contract_and_allowed_systems() -> None:
    control = EnterpriseControlService()
    domains = ("student_data", "enrollment", "progress", "billing", "attendance", "teacher_data")
    permissions = {f"integration.read.{domain}" for domain in domains}
    control.set_role_permissions(tenant_id="tenant_1", role="integration-reader", permissions=permissions)

    service = IntegrationAPIService(enterprise_control=control)
    identity = IdentityContext(tenant_id="tenant_1", actor_id="actor_1", roles=("integration-reader",))

    for domain in domains:
        status, payload = service.get_domain_payload(
            identity=identity,
            request=IntegrationRequest(
                request_id=f"req_{domain}",
                tenant_id="tenant_1",
                domain=domain,
                external_system="reporting",
                resource_id="r1",
            ),
        )
        assert status == 200
        assert payload["status"] == "success"
        assert payload["meta"]["domain"] == domain
        assert payload["meta"]["rate_limit"]["limit_per_minute"] > 0


def test_integration_enforces_authorization_and_tenant_scoping() -> None:
    control = EnterpriseControlService()
    control.set_role_permissions(tenant_id="tenant_1", role="reader", permissions={"integration.read.student_data"})
    service = IntegrationAPIService(enterprise_control=control)

    outsider = IdentityContext(tenant_id="tenant_2", actor_id="actor_2", roles=("reader",))
    status, payload = service.get_domain_payload(
        identity=outsider,
        request=IntegrationRequest(
            request_id="req_denied",
            tenant_id="tenant_1",
            domain="student_data",
            external_system="hr",
            resource_id="stu_1",
        ),
    )

    assert status == 403
    assert payload["error"]["code"] == "forbidden"


def test_integration_rate_limit_ready() -> None:
    control = EnterpriseControlService()
    control.set_role_permissions(tenant_id="tenant_1", role="reader", permissions={"integration.read.billing"})
    service = IntegrationAPIService(enterprise_control=control, rate_limit_policy=RateLimitPolicy(requests_per_minute=1))
    identity = IdentityContext(tenant_id="tenant_1", actor_id="actor_1", roles=("reader",))

    first_status, _ = service.get_domain_payload(
        identity=identity,
        request=IntegrationRequest(
            request_id="req_1",
            tenant_id="tenant_1",
            domain="billing",
            external_system="erp",
            resource_id="inv_1",
        ),
    )
    second_status, second_payload = service.get_domain_payload(
        identity=identity,
        request=IntegrationRequest(
            request_id="req_2",
            tenant_id="tenant_1",
            domain="billing",
            external_system="erp",
            resource_id="inv_2",
        ),
    )

    assert first_status == 200
    assert second_status == 429
    assert second_payload["error"]["code"] == "rate_limited"
