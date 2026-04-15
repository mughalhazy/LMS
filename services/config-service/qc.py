from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from service import ConfigService
from shared.models.config import (
    ConfigLevel,
    ConfigOverride,
    ConfigResolutionContext,
    ConfigScope,
    segment_behavior_from_effective_config,
)


def run_qc() -> dict[str, object]:
    service = ConfigService()
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.GLOBAL, scope_id="global"),
            capability_enabled={"assessment.author": True},
            behavior_tuning={
                "notifications": {"retry_limit": 2, "channel": "email"},
                "segment_behavior": {"attendance_enabled": False, "cohort_enabled": False},
            },
        )
    )
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.COUNTRY, scope_id="US"),
            capability_enabled={"assessment.author": False},
            behavior_tuning={"notifications": {"channel": "sms"}},
        )
    )
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.SEGMENT, scope_id="school"),
            capability_enabled={"analytics.advanced": True},
            behavior_tuning={
                "grading": {"automation": "strict"},
                "segment_behavior": {"attendance_enabled": True, "guardian_notifications_enabled": True},
            },
        )
    )
    service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_001"),
            capability_enabled={"assessment.author": True},
            behavior_tuning={"notifications": {"retry_limit": 5}},
        )
    )

    effective = service.resolve(
        ConfigResolutionContext(tenant_id="tenant_001", country_code="US", segment_id="school")
    )
    segment_behavior = segment_behavior_from_effective_config(effective)

    overrides_work = (
        effective.capability_enabled.get("assessment.author") is True
        and effective.capability_enabled.get("analytics.advanced") is True
        and effective.behavior_tuning.get("notifications", {}).get("channel") == "sms"
        and effective.behavior_tuning.get("notifications", {}).get("retry_limit") == 5
        and effective.behavior_tuning.get("grading", {}).get("automation") == "strict"
    )
    behavior_controlled_via_config = (
        segment_behavior.attendance_enabled is True
        and segment_behavior.guardian_notifications_enabled is True
        and segment_behavior.cohort_enabled is False
    )
    no_conflicts = not service.has_conflicting_config_paths()

    passed = overrides_work and no_conflicts and behavior_controlled_via_config
    return {
        "checks": {
            "overrides_work_correctly": overrides_work,
            "behavior_controlled_via_config": behavior_controlled_via_config,
            "no_conflicting_config_paths": no_conflicts,
        },
        "score": 10 if passed else 0,
    }


if __name__ == "__main__":
    print(json.dumps(run_qc(), indent=2))
