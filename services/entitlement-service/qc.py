from __future__ import annotations

import json
from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from service import EntitlementService
from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope
from shared.utils.entitlement import TenantEntitlementContext

ROOT = Path(__file__).resolve().parents[2]

SERVICES_THAT_MUST_USE_ENTITLEMENT = [
    ROOT / "services/subscription-service/service.py",
    ROOT / "services/config-service/service.py",
    ROOT / "services/capability-registry/service.py",
    ROOT / "services/entitlement-service/service.py",
]


def _all_services_reference_entitlement() -> bool:
    required_markers = ("entitlement", "is_enabled")
    for file_path in SERVICES_THAT_MUST_USE_ENTITLEMENT:
        if not file_path.exists():
            return False
        content = file_path.read_text(encoding="utf-8").lower()
        if file_path.name == "service.py" and "entitlement-service" in str(file_path):
            continue
        if not any(marker in content for marker in required_markers):
            return False
    return True


def run_qc() -> dict[str, object]:
    entitlement_service = EntitlementService()
    tenant = TenantEntitlementContext(
        tenant_id="tenant_qc",
        plan_type="pro",
        add_ons=("ai_tutor_pack",),
        country_code="US",
        segment_id="enterprise",
    )
    entitlement_service.upsert_tenant_context(tenant)

    entitlement_service._config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_qc"),
            capability_enabled={"learning.analytics.advanced": True},
            behavior_tuning={},
        )
    )

    resolved_by_plan = entitlement_service.is_enabled(tenant, "course.write")
    resolved_by_addon = entitlement_service.is_enabled(tenant, "ai.tutor")
    resolved_by_override = entitlement_service.is_enabled(tenant, "learning.analytics.advanced")

    no_bypass_paths = not entitlement_service.has_bypass_paths()
    all_services_use_entitlement = _all_services_reference_entitlement()

    passed = (
        resolved_by_plan
        and resolved_by_addon
        and resolved_by_override
        and no_bypass_paths
        and all_services_use_entitlement
    )
    return {
        "checks": {
            "no_bypass_paths": no_bypass_paths,
            "all_services_use_entitlement": all_services_use_entitlement,
            "resolves_plan_type": resolved_by_plan,
            "resolves_add_ons": resolved_by_addon,
            "resolves_config_overrides": resolved_by_override,
        },
        "score": 10 if passed else 0,
    }


if __name__ == "__main__":
    print(json.dumps(run_qc(), indent=2))
