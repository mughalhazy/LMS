from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/network-effects/service.py"
INIT_PATH = ROOT / "services/network-effects/__init__.py"

service_spec = importlib.util.spec_from_file_location("network_effects_service_test", MODULE_PATH)
init_spec = importlib.util.spec_from_file_location("network_effects_init_test", INIT_PATH)
if service_spec is None or service_spec.loader is None or init_spec is None or init_spec.loader is None:
    raise RuntimeError("Unable to load network-effects service modules")

service_module = importlib.util.module_from_spec(service_spec)
init_module = importlib.util.module_from_spec(init_spec)
sys.modules[service_spec.name] = service_module
sys.modules[init_spec.name] = init_module
service_spec.loader.exec_module(service_module)
init_spec.loader.exec_module(init_module)

NetworkEffectsService = service_module.NetworkEffectsService
TeacherSignal = service_module.TeacherSignal


def _teacher_signal(teacher_id: str, tenant_id: str, base: float) -> TeacherSignal:
    return TeacherSignal(
        teacher_id=teacher_id,
        tenant_id=tenant_id,
        assessment_quality=base + 0.04,
        learner_outcome=base + 0.02,
        retention_rate=base,
        engagement_index=base - 0.03,
    )


def test_teacher_scoring_and_percentiles_are_privacy_safe() -> None:
    service = NetworkEffectsService(min_tenants=3, min_teacher_sample=6)
    subject = _teacher_signal("t-home", "tenant-home", 0.78)
    peers = (
        _teacher_signal("t-a-1", "tenant-a", 0.61),
        _teacher_signal("t-a-2", "tenant-a", 0.66),
        _teacher_signal("t-b-1", "tenant-b", 0.55),
        _teacher_signal("t-b-2", "tenant-b", 0.58),
        _teacher_signal("t-c-1", "tenant-c", 0.63),
        _teacher_signal("t-c-2", "tenant-c", 0.69),
    )

    scored = service.teacher_scoring(signal=subject, peer_signals=peers, benchmark_window="2026-Q1")

    assert scored.aggregation_safe is True
    assert scored.metadata["privacy_mode"] == "k_anonymized"
    assert 0 <= float(scored.percentile_rank) <= 1


def test_benchmarking_rollup_exposes_only_aggregated_metrics() -> None:
    service = NetworkEffectsService(min_tenants=3, min_teacher_sample=6)
    scores = (
        service.teacher_scoring(
            signal=_teacher_signal("t-home", "tenant-home", 0.78),
            peer_signals=(
                _teacher_signal("t-a-1", "tenant-a", 0.61),
                _teacher_signal("t-a-2", "tenant-a", 0.66),
                _teacher_signal("t-b-1", "tenant-b", 0.55),
                _teacher_signal("t-b-2", "tenant-b", 0.58),
                _teacher_signal("t-c-1", "tenant-c", 0.63),
                _teacher_signal("t-c-2", "tenant-c", 0.69),
            ),
            benchmark_window="2026-Q1",
        ),
        service.teacher_scoring(
            signal=_teacher_signal("t-a-1", "tenant-a", 0.61),
            peer_signals=(
                _teacher_signal("t-home", "tenant-home", 0.78),
                _teacher_signal("t-home-2", "tenant-home", 0.74),
                _teacher_signal("t-b-1", "tenant-b", 0.55),
                _teacher_signal("t-b-2", "tenant-b", 0.58),
                _teacher_signal("t-c-1", "tenant-c", 0.63),
                _teacher_signal("t-c-2", "tenant-c", 0.69),
            ),
            benchmark_window="2026-Q1",
        ),
        service.teacher_scoring(
            signal=_teacher_signal("t-b-1", "tenant-b", 0.55),
            peer_signals=(
                _teacher_signal("t-home", "tenant-home", 0.78),
                _teacher_signal("t-home-2", "tenant-home", 0.74),
                _teacher_signal("t-a-1", "tenant-a", 0.61),
                _teacher_signal("t-a-2", "tenant-a", 0.66),
                _teacher_signal("t-c-1", "tenant-c", 0.63),
                _teacher_signal("t-c-2", "tenant-c", 0.69),
            ),
            benchmark_window="2026-Q1",
        ),
        service.teacher_scoring(
            signal=_teacher_signal("t-c-1", "tenant-c", 0.63),
            peer_signals=(
                _teacher_signal("t-home", "tenant-home", 0.78),
                _teacher_signal("t-home-2", "tenant-home", 0.74),
                _teacher_signal("t-a-1", "tenant-a", 0.61),
                _teacher_signal("t-a-2", "tenant-a", 0.66),
                _teacher_signal("t-b-1", "tenant-b", 0.55),
                _teacher_signal("t-b-2", "tenant-b", 0.58),
            ),
            benchmark_window="2026-Q1",
        ),
        service.teacher_scoring(
            signal=_teacher_signal("t-home-2", "tenant-home", 0.74),
            peer_signals=(
                _teacher_signal("t-a-1", "tenant-a", 0.61),
                _teacher_signal("t-a-2", "tenant-a", 0.66),
                _teacher_signal("t-b-1", "tenant-b", 0.55),
                _teacher_signal("t-b-2", "tenant-b", 0.58),
                _teacher_signal("t-c-1", "tenant-c", 0.63),
                _teacher_signal("t-c-2", "tenant-c", 0.69),
            ),
            benchmark_window="2026-Q1",
        ),
        service.teacher_scoring(
            signal=_teacher_signal("t-a-2", "tenant-a", 0.66),
            peer_signals=(
                _teacher_signal("t-home", "tenant-home", 0.78),
                _teacher_signal("t-home-2", "tenant-home", 0.74),
                _teacher_signal("t-b-1", "tenant-b", 0.55),
                _teacher_signal("t-b-2", "tenant-b", 0.58),
                _teacher_signal("t-c-1", "tenant-c", 0.63),
                _teacher_signal("t-c-2", "tenant-c", 0.69),
            ),
            benchmark_window="2026-Q1",
        ),
    )

    summary = service.benchmarking(teacher_scores=scores, benchmark_window="2026-Q1")

    assert summary.aggregation_safe is True
    assert summary.metadata["tenant_ids_exposed"] is False
    assert float(summary.p10_score) <= float(summary.p50_score) <= float(summary.p90_score)


def test_cross_tenant_exposure_is_blocked_when_sample_is_not_safe() -> None:
    service = NetworkEffectsService(min_tenants=3, min_teacher_sample=5)
    subject = _teacher_signal("t-home", "tenant-home", 0.78)
    unsafe_peers = (
        _teacher_signal("t-a-1", "tenant-a", 0.61),
        _teacher_signal("t-a-2", "tenant-a", 0.66),
        _teacher_signal("t-home-2", "tenant-home", 0.74),
    )

    try:
        service.teacher_scoring(signal=subject, peer_signals=unsafe_peers, benchmark_window="2026-Q1")
        raise AssertionError("Expected privacy-safe aggregation guard to reject unsafe sample")
    except ValueError as exc:
        assert "aggregation safe check failed" in str(exc)


def test_package_exports_network_effects_types() -> None:
    assert hasattr(init_module, "NetworkEffectsService")
    assert hasattr(init_module, "TeacherSignal")
    assert hasattr(init_module, "TeacherScore")
    assert hasattr(init_module, "BenchmarkSummary")
