from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from qc import run_qc
from service import ConfigService
from shared.models.config import ConfigLevel, ConfigOverride, ConfigResolutionContext, ConfigScope


def test_resolve_respects_level_precedence_and_merges_behavior() -> None:
    service = ConfigService()
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.GLOBAL, scope_id="global"),
            capability_enabled={"analytics.basic": True, "analytics.advanced": False},
            behavior_tuning={"recommendations": {"max_items": 5, "strategy": "balanced"}},
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
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_abc"),
            capability_enabled={"analytics.basic": False},
            behavior_tuning={"recommendations": {"max_items": 12}},
        )
    )

    effective = service.resolve(
        ConfigResolutionContext(tenant_id="tenant_abc", country_code="US", segment_id="default")
    )

    assert effective.capability_enabled["analytics.basic"] is False
    assert effective.capability_enabled["analytics.advanced"] is True
    assert effective.behavior_tuning["recommendations"] == {"max_items": 12, "strategy": "local"}


def test_qc_gate_score_is_perfect() -> None:
    report = run_qc()

    assert report["checks"]["overrides_work_correctly"] is True
    assert report["checks"]["no_conflicting_config_paths"] is True
    assert report["score"] == 10
