from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from store import capability_index, feature_capability_mapping

ROOT = Path(__file__).resolve().parents[2]

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

    passed = not unmapped_features and not invalid_capability_links and not orphan_features
    return {
        "checks": {
            "all_features_mapped_to_capability": not unmapped_features,
            "no_orphan_features": not orphan_features,
            "all_capability_links_resolvable": not invalid_capability_links,
        },
        "unmapped_features": unmapped_features,
        "orphan_features": orphan_features,
        "invalid_capability_links": invalid_capability_links,
        "score": 10 if passed else 0,
    }


if __name__ == "__main__":
    print(json.dumps(run_qc(), indent=2))
