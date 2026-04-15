from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/config-service/service.py"
_service_spec = importlib.util.spec_from_file_location("config_service_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load service module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)
ConfigService = _service_module.ConfigService
from shared.models.config import (
    ConfigLevel,
    ConfigOverride,
    ConfigResolutionContext,
    ConfigScope,
    segment_behavior_from_effective_config,
)


def test_resolve_respects_level_precedence_and_merges_behavior() -> None:
    service = ConfigService()
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.GLOBAL, scope_id="global"),
            capability_enabled={"analytics.basic": True, "analytics.advanced": False},
            behavior_tuning={
                "recommendations": {"max_items": 5, "strategy": "balanced"},
                "segment_behavior": {"attendance_enabled": False, "cohort_enabled": False},
            },
        )
    )
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.COUNTRY, scope_id="US"),
            capability_enabled={"analytics.advanced": True},
            behavior_tuning={"recommendations": {"strategy": "local"}},
        )
    )
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.SEGMENT, scope_id="school"),
            capability_enabled={},
            behavior_tuning={"segment_behavior": {"attendance_enabled": True}},
        )
    )
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_abc"),
            capability_enabled={"analytics.basic": False},
            behavior_tuning={"recommendations": {"max_items": 12}},
        )
    )

    effective = service.resolve(
        ConfigResolutionContext(tenant_id="tenant_abc", country_code="US", segment_id="school")
    )
    segment_behavior = segment_behavior_from_effective_config(effective)

    assert effective.capability_enabled["analytics.basic"] is False
    assert effective.capability_enabled["analytics.advanced"] is True
    assert effective.behavior_tuning["recommendations"] == {"max_items": 12, "strategy": "local"}
    assert segment_behavior.attendance_enabled is True
    assert segment_behavior.cohort_enabled is False



def test_resolve_communication_routing_is_capability_and_config_driven() -> None:
    service = ConfigService()
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.GLOBAL, scope_id="global"),
            capability_enabled={"whatsapp_primary_interface": True},
            behavior_tuning={"communication": {"routing_priority": ["email", "sms"]}},
        )
    )

    routing = service.resolve_communication_routing(
        ConfigResolutionContext(tenant_id="tenant_route", country_code="PK", segment_id="academy")
    )

    assert routing == ("whatsapp", "email", "sms")

def test_resolve_onboarding_mode_defaults_to_whatsapp_first() -> None:
    service = ConfigService()
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_onb"),
            behavior_tuning={"onboarding": {"preferred_channel": "whatsapp", "dashboard_required": False}},
        )
    )

    mode = service.resolve_onboarding_mode(
        ConfigResolutionContext(tenant_id="tenant_onb", country_code="PK", segment_id="academy")
    )

    assert mode == "whatsapp_first"

