from __future__ import annotations

from decimal import Decimal
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from capability_creation_flow import CapabilityMintRequest, CapabilityMintingFlow
from shared.utils.entitlement import TenantEntitlementContext


def test_minting_flow_registers_prices_enables_and_resolves_entitlement() -> None:
    flow = CapabilityMintingFlow()

    minted = flow.mint(
        CapabilityMintRequest(
            capability_id="insights.prediction",
            name="Predictive Insights",
            description="Forecast learner risk and outcomes.",
            category="analytics",
            price=Decimal("0.30"),
            usage_based=True,
            included_in_plans=("enterprise",),
            included_in_add_ons=("analytics_advanced",),
            feature_ids=("insights_prediction",),
            enable_globally=False,
        )
    )

    assert flow.registry.get_capability("insights.prediction") is not None
    assert flow.registry.get_capability_for_feature("insights_prediction") is not None
    assert flow.registry.get_capability_pricing("insights.prediction") is not None
    assert minted.price == Decimal("0.30")

    tenant = TenantEntitlementContext(
        tenant_id="tenant_ent",
        plan_type="free",
        add_ons=("analytics_advanced",),
        country_code="US",
        segment_id="school",
    )
    assert flow.is_usable_via_entitlement(tenant, "insights.prediction") is True


def test_minting_flow_can_enable_capability_globally_via_config() -> None:
    flow = CapabilityMintingFlow()

    flow.mint(
        CapabilityMintRequest(
            capability_id="content.translation.ai",
            name="AI Translation",
            description="Translate content across supported languages.",
            category="intelligence",
            price=Decimal("25.00"),
            usage_based=False,
            included_in_plans=(),
            included_in_add_ons=(),
            feature_ids=("content_translation_ai",),
            enable_globally=True,
        )
    )

    tenant = TenantEntitlementContext(
        tenant_id="tenant_cfg",
        plan_type="free",
        add_ons=(),
        country_code="US",
        segment_id="school",
    )
    assert flow.is_usable_via_entitlement(tenant, "content.translation.ai") is True
