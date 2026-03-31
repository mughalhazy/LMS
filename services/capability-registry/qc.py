from __future__ import annotations

import json
from pathlib import Path
import sys
from decimal import Decimal

sys.path.append(str(Path(__file__).resolve().parents[2]))

from store import capability_index, feature_capability_mapping

ROOT = Path(__file__).resolve().parents[2]
SUBSCRIPTION_SERVICE_FILE = ROOT / "services/subscription-service/service.py"

FEATURE_SOURCE_FILES = [
    ROOT / "backend/services/subscription-service/tests/test_pricing.py",
    ROOT / "backend/services/tenant-service/tests/conftest.py",
    ROOT / "backend/services/tenant-service/app/service.py",
]


def _extract_declared_features() -> set[str]:
    discovered: set[str] = set()
    for path in FEATURE_SOURCE_FILES:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for feature in [
            "dedicated_isolation",
            "priority_support",
            "catalog_basic",
            "analytics_basic",
            "analytics_advanced",
            "feature.analytics",
        ]:
            if feature in content:
                discovered.add(feature)

    # Use capability-registry mapping as the source of truth for declared features.
    discovered.update(feature_capability_mapping().keys())
    return discovered


def run_qc() -> dict[str, object]:
    capabilities = capability_index()
    feature_mapping = feature_capability_mapping()
    discovered_features = _extract_declared_features()

    unmapped_features = sorted(feature for feature in discovered_features if feature not in feature_mapping)
    orphan_features = sorted(feature for feature in feature_mapping if feature not in discovered_features and "." not in feature)
    invalid_capability_links = sorted(
        feature for feature, capability_id in feature_mapping.items() if capability_id not in capabilities
    )
    non_billable_capabilities = sorted(
        capability_id for capability_id, capability in capabilities.items() if capability.price < Decimal("0")
    )
    missing_pricing_fields = sorted(
        capability_id for capability_id, capability in capabilities.items() if capability.price == Decimal("0")
    )
    pricing_leakage_patterns = ["plan_price", "plan_pricing", "plan_rate"]
    subscription_source = SUBSCRIPTION_SERVICE_FILE.read_text(encoding="utf-8") if SUBSCRIPTION_SERVICE_FILE.exists() else ""
    pricing_leakage_hits = sorted(pattern for pattern in pricing_leakage_patterns if pattern in subscription_source)

    passed = (
        not unmapped_features
        and not invalid_capability_links
        and not orphan_features
        and not non_billable_capabilities
        and not missing_pricing_fields
        and not pricing_leakage_hits
    )
    return {
        "checks": {
            "all_features_mapped_to_capability": not unmapped_features,
            "no_orphan_features": not orphan_features,
            "all_capability_links_resolvable": not invalid_capability_links,
            "all_capabilities_billable": not non_billable_capabilities and not missing_pricing_fields,
            "no_pricing_leakage": not pricing_leakage_hits,
        },
        "unmapped_features": unmapped_features,
        "orphan_features": orphan_features,
        "invalid_capability_links": invalid_capability_links,
        "non_billable_capabilities": non_billable_capabilities,
        "missing_pricing_fields": missing_pricing_fields,
        "pricing_leakage_hits": pricing_leakage_hits,
        "score": 10 if passed else 0,
    }


if __name__ == "__main__":
    print(json.dumps(run_qc(), indent=2))
