from __future__ import annotations

from decimal import Decimal

from integrations.payments.adapters import MockSuccessAdapter
from integrations.payments.orchestration import PaymentOrchestrationService
from integrations.payments.router import PaymentProviderRouter
from services.commerce.service import CommerceService
from shared.utils.entitlement import TenantEntitlementContext


def _commerce(country: str = "US") -> CommerceService:
    router = PaymentProviderRouter({country: "mock_success"}, [MockSuccessAdapter()])
    return CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router), payment_country_code=country)


def test_included_capability_billing_path_is_plan_scoped() -> None:
    commerce = _commerce("US")
    tenant = TenantEntitlementContext(tenant_id="tenant_plan", plan_type="pro", country_code="US", segment_id="academy")
    commerce.entitlement_service.upsert_tenant_context(tenant)

    charges = commerce.calculate_capability_charges(tenant)
    charge_map = {charge.capability_id: charge.amount for charge in charges}

    assert charge_map["assessment.author"] == Decimal("29.00")
    assert commerce.entitlement_service.is_enabled(tenant, "assessment.author") is True


def test_add_on_capability_billing_path_requires_entitlement_and_audit() -> None:
    commerce = _commerce("PK")
    tenant = TenantEntitlementContext(
        tenant_id="tenant_addon_pk",
        plan_type="growth_academy",
        country_code="PK",
        segment_id="academy",
    )
    commerce.entitlement_service.upsert_tenant_context(tenant)

    eligible = {item.addon_id for item in commerce.monetization.list_eligible_add_ons_for_tenant(tenant=tenant)}
    assert "owner_analytics" in eligible

    commerce.monetization.purchase_add_on(tenant=tenant, addon_id="owner_analytics", actor_id="qa")
    assert commerce.entitlement_service.is_enabled(tenant, "owner_analytics") is True
    assert commerce.subscription_service.get_add_on_activation_audit_log("tenant_addon_pk")[-1]["event"] == "activated"


def test_usage_based_capability_uses_usage_hook_and_bills_units() -> None:
    commerce = _commerce("US")
    tenant = TenantEntitlementContext(
        tenant_id="tenant_usage",
        plan_type="free",
        add_ons=("analytics_advanced",),
        country_code="US",
        segment_id="academy",
    )
    commerce.entitlement_service.upsert_tenant_context(tenant)

    commerce.record_capability_usage(
        tenant_id="tenant_usage",
        capability_id="learning.analytics.advanced",
        units=5,
        source_service="analytics",
        reference_id="usage-1",
    )

    usage = commerce.subscription_service.get_usage_for_tenant("tenant_usage")
    assert usage["learning.analytics.advanced"] == 5
    charges = {charge.capability_id: charge.amount for charge in commerce.calculate_capability_charges(tenant)}
    assert charges["learning.analytics.advanced"] == Decimal("0.50")


def test_pakistan_default_plan_addon_combinations_are_eligible() -> None:
    commerce = _commerce("PK")

    starter = TenantEntitlementContext(
        tenant_id="tenant_pk_starter",
        plan_type="starter_academy",
        country_code="PK",
        segment_id="academy",
    )
    growth = TenantEntitlementContext(
        tenant_id="tenant_pk_growth",
        plan_type="growth_academy",
        country_code="PK",
        segment_id="academy",
    )

    commerce.entitlement_service.upsert_tenant_context(starter)
    commerce.entitlement_service.upsert_tenant_context(growth)

    starter_eligible = {item.addon_id for item in commerce.monetization.list_eligible_add_ons_for_tenant(tenant=starter)}
    growth_eligible = {item.addon_id for item in commerce.monetization.list_eligible_add_ons_for_tenant(tenant=growth)}

    assert starter_eligible == set()
    assert growth_eligible == {"owner_analytics"}


def test_monetization_validation_has_no_orphaned_capabilities() -> None:
    commerce = _commerce("US")
    valid, orphaned = commerce.monetization.validate_no_orphaned_monetized_capabilities()
    assert valid is True
    assert orphaned == set()
