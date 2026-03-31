from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from qc import run_qc
from service import EntitlementService
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


def test_qc_gate_score_is_perfect() -> None:
    report = run_qc()

    assert report["checks"]["no_bypass_paths"] is True
    assert report["checks"]["all_services_use_entitlement"] is True
    assert report["score"] == 10
