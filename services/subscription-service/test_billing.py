from __future__ import annotations

import importlib.util
from decimal import Decimal
from pathlib import Path

from shared.models.capability_pricing import CapabilityPricing


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/subscription-service/service.py"
spec = importlib.util.spec_from_file_location("subscription_service_module_for_tests", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load subscription service module")
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)
SubscriptionService = module.SubscriptionService
TenantSubscription = module.TenantSubscription


def test_upsert_and_get_tenant_subscription() -> None:
    service = SubscriptionService()
    service.upsert_tenant_subscription(TenantSubscription(tenant_id="tenant_1", plan_type="Pro", add_ons=("analytics_plus",)))

    current = service.get_tenant_subscription("tenant_1")

    assert current is not None
    assert current.plan_type == "pro"
    assert current.add_ons == ("analytics_plus",)


def test_calculate_usage_based_charge() -> None:
    service = SubscriptionService()
    pricing = CapabilityPricing(capability_id="analytics.reports.export", usage_based=True, price=Decimal("2.50"))
    service.record_capability_usage(tenant_id="tenant_1", capability_id="analytics.reports.export", units=4)

    charge = service.calculate_capability_charge(tenant_id="tenant_1", pricing=pricing)

    assert charge == Decimal("10.00")


def test_plan_catalog_exposes_pakistan_ready_plan_patterns() -> None:
    service = SubscriptionService()

    starter = service.get_plan("starter_academy")
    growth = service.get_plan("growth_academy")
    school = service.get_plan("school_basic")
    enterprise_learning = service.get_plan("enterprise_learning")

    assert starter is not None
    assert growth is not None
    assert school is not None
    assert enterprise_learning is not None
    assert "attendance_tracking" in starter.included_capability_ids
    assert "fee_tracking" in growth.included_capability_ids
    assert "parent_notifications" in school.included_capability_ids
    assert "operations_dashboard" in enterprise_learning.included_capability_ids
