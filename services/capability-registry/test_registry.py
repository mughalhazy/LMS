from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from qc import run_qc
from service import CapabilityRegistryService


def test_get_capability_and_list_capabilities() -> None:
    registry = CapabilityRegistryService()

    capability = registry.get_capability("assessment.author")

    assert capability is not None
    assert capability.capability_id == "assessment.author"
    assert capability.name == "Assessment Authoring"
    assert len(registry.list_capabilities()) >= 1


def test_feature_to_capability_resolution() -> None:
    registry = CapabilityRegistryService()

    resolved = registry.get_capability_for_feature("analytics_advanced")

    assert resolved is not None
    assert resolved.capability_id == "learning.analytics.advanced"


def test_qc_gate_score_is_perfect() -> None:
    report = run_qc()

    assert report["checks"]["all_features_mapped_to_capability"] is True
    assert report["checks"]["no_orphan_features"] is True
    assert report["score"] == 10
