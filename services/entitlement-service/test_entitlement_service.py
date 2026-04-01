from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/entitlement-service/service.py"
_service_spec = importlib.util.spec_from_file_location("entitlement_service_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load service module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)
EntitlementService = _service_module.EntitlementService
from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope
from shared.utils.entitlement import TenantEntitlementContext


def test_runtime_decision_engine_resolves_plan_addons_and_config_overrides() -> None:
    service = EntitlementService()
    tenant = TenantEntitlementContext(
        tenant_id="tenant_123",
        plan_type="free",
        add_ons=("analytics_advanced",),
        country_code="US",
        segment_id="smb",
    )
    service.upsert_tenant_context(tenant)

    assert service.is_enabled(tenant, "assessment.attempt") is True
    assert service.is_enabled(tenant, "learning.analytics.advanced") is True

    service._config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_123"),
            capability_enabled={"assessment.attempt": False},
            behavior_tuning={},
        )
    )
    assert service.is_enabled(tenant, "assessment.attempt") is False


def test_unknown_capability_fails_closed() -> None:
    service = EntitlementService()
    tenant = TenantEntitlementContext(tenant_id="tenant_x", plan_type="pro")

    decision = service.decide(tenant, "does.not.exist")

    assert decision.is_enabled is False
    assert "unknown_capability" in decision.sources


def test_resolve_enabled_capabilities_returns_effective_capability_set() -> None:
    service = EntitlementService()
    tenant = TenantEntitlementContext(
        tenant_id="tenant_caps",
        plan_type="free",
        add_ons=("ai_tutor_pack",),
        country_code="US",
        segment_id="academy",
    )
    service.upsert_tenant_context(tenant)

    resolved = service.resolve_enabled_capabilities(tenant)

    assert "assessment.attempt" in resolved
    assert "ai.tutor" in resolved
    assert "assessment.author" not in resolved


def test_purchased_add_on_capability_resolves_through_entitlement_service() -> None:
    service = EntitlementService()
    tenant = TenantEntitlementContext(
        tenant_id="tenant_addon",
        plan_type="growth_academy",
        country_code="PK",
        segment_id="academy",
    )
    service.upsert_tenant_context(tenant)

    service._subscription_service.purchase_add_on(
        tenant_id="tenant_addon",
        addon_id="owner_analytics",
        actor_id="test",
    )

    assert service.is_enabled(tenant, "owner_analytics") is True


def test_usage_metering_emits_canonical_event_and_prevents_duplicates() -> None:
    service = EntitlementService()
    tenant = TenantEntitlementContext(
        tenant_id="tenant_usage",
        plan_type="enterprise_learning",
        country_code="PK",
        segment_id="academy",
    )
    service.upsert_tenant_context(tenant)

    first = service.meter_usage(
        tenant=tenant,
        capability_id="exam_engine",
        quantity=3,
        source_service="exam-engine",
        reference_id="attempt-123",
        metadata={"session_id": "sess-123"},
    )
    duplicate = service.meter_usage(
        tenant=tenant,
        capability_id="exam_engine",
        quantity=3,
        source_service="exam-engine",
        reference_id="attempt-123",
    )

    assert first is not None
    assert duplicate is None
    events = service.list_usage_events()
    assert len(events) == 1
    assert events[0].event_type == "lms.usage.recorded.v1"
    assert events[0].topic == "lms.usage.recorded"
    assert events[0].producer_service == "entitlement-service"
