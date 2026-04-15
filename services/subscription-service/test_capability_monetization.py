from __future__ import annotations

from decimal import Decimal

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.models.capability_pricing import CapabilityPricing
_SERVICE_PATH = Path(__file__).resolve().parent / "service.py"
_SPEC = importlib.util.spec_from_file_location("subscription_service_module", _SERVICE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)
SubscriptionService = _MODULE.SubscriptionService
TenantSubscription = _MODULE.TenantSubscription


def test_purchase_add_on_enables_capability() -> None:
    service = SubscriptionService()
    service.purchase_capability_add_on("tenant_1", "ai.tutor")

    assert service.is_enabled_for_subscription(
        tenant_id="tenant_1",
        plan_type="free",
        add_ons=tuple(),
        capability="ai.tutor",
        entitlement=lambda _: False,
    )


def test_usage_tracking_supports_usage_based_charges() -> None:
    service = SubscriptionService()
    service.record_capability_usage(tenant_id="tenant_1", capability_id="learning.analytics.advanced", units=7)

    total = service.calculate_capability_charge(
        tenant_id="tenant_1",
        pricing=CapabilityPricing(
            capability_id="learning.analytics.advanced",
            price=Decimal("0.10"),
            usage_based=True,
        ),
    )

    assert total == Decimal("0.70")


def test_flat_price_charges_once_for_capability() -> None:
    service = SubscriptionService()
    service.record_capability_usage(tenant_id="tenant_1", capability_id="platform.support.priority", units=99)

    total = service.calculate_capability_charge(
        tenant_id="tenant_1",
        pricing=CapabilityPricing(
            capability_id="platform.support.priority",
            price=Decimal("149.00"),
            usage_based=False,
        ),
    )

    assert total == Decimal("149.00")


def test_add_on_purchase_attach_activation_audit_and_revoke() -> None:
    service = SubscriptionService()
    service.upsert_tenant_subscription(TenantSubscription(tenant_id="tenant_pk", plan_type="growth_academy"))

    attachment = service.purchase_add_on(tenant_id="tenant_pk", addon_id="owner_analytics", actor_id="tester")
    assert attachment.capability_id == "owner_analytics"
    assert "owner_analytics" in service.get_active_add_on_capability_ids("tenant_pk")
    assert service.get_add_on_activation_audit_log("tenant_pk")[0]["event"] == "activated"

    service.revoke_add_on(tenant_id="tenant_pk", addon_id="owner_analytics", reason="cancelled")
    assert "owner_analytics" not in service.get_active_add_on_capability_ids("tenant_pk")
    assert service.get_add_on_activation_audit_log("tenant_pk")[-1]["event"] == "revoked:cancelled"


def test_duplicate_add_on_purchase_is_blocked() -> None:
    service = SubscriptionService()
    service.upsert_tenant_subscription(TenantSubscription(tenant_id="tenant_pk", plan_type="growth_academy"))
    service.purchase_add_on(tenant_id="tenant_pk", addon_id="owner_analytics")

    try:
        service.purchase_add_on(tenant_id="tenant_pk", addon_id="owner_analytics")
    except ValueError as exc:
        assert "duplicate add-on purchase" in str(exc)
    else:
        raise AssertionError("expected duplicate add-on purchase to be rejected")
