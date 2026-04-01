from __future__ import annotations

import importlib.util
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def _load_models_module():
    module_path = Path(__file__).resolve().parent / "models.py"
    spec = importlib.util.spec_from_file_location("network_effects_models", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load network-effects models")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ModelsModule = _load_models_module()
BenchmarkSummary = _ModelsModule.BenchmarkSummary
TeacherScore = _ModelsModule.TeacherScore
TeacherSignal = _ModelsModule.TeacherSignal
_q4 = _ModelsModule._q4


class NetworkEffectsService:
    """Privacy-safe cross-tenant benchmarking and teacher scoring."""

    def __init__(self, *, min_tenants: int = 3, min_teacher_sample: int = 5) -> None:
        self._min_tenants = min_tenants
        self._min_teacher_sample = min_teacher_sample

    def teacher_scoring(self, *, signal: TeacherSignal, peer_signals: tuple[TeacherSignal, ...], benchmark_window: str) -> TeacherScore:
        safe_peers = self._privacy_safe_pool(subject=signal, peers=peer_signals)
        own_score = self._weighted_score(signal)
        peer_scores = [self._weighted_score(peer) for peer in safe_peers]
        percentile = self._percentile_rank(own_score, peer_scores)

        return TeacherScore(
            teacher_id=signal.teacher_id,
            tenant_id=signal.tenant_id,
            weighted_score=_q4(own_score),
            percentile_rank=_q4(percentile),
            benchmark_window=benchmark_window.strip(),
            aggregation_safe=True,
            metadata={
                "peer_sample_size": len(peer_scores),
                "tenant_count": len({peer.tenant_id for peer in safe_peers}),
                "privacy_mode": "k_anonymized",
            },
        )

    def benchmarking(self, *, teacher_scores: tuple[TeacherScore, ...], benchmark_window: str) -> BenchmarkSummary:
        self._validate_cross_tenant_scores(teacher_scores)
        values = [float(score.weighted_score) for score in teacher_scores]
        tenant_ids = {score.tenant_id for score in teacher_scores}

        return BenchmarkSummary(
            benchmark_window=benchmark_window.strip(),
            participating_tenant_count=len(tenant_ids),
            teacher_sample_size=len(values),
            network_average_score=_q4(statistics.fmean(values)),
            network_median_score=_q4(statistics.median(values)),
            p10_score=_q4(self.percentiles(values, 0.10)),
            p50_score=_q4(self.percentiles(values, 0.50)),
            p90_score=_q4(self.percentiles(values, 0.90)),
            aggregation_safe=True,
            metadata={"privacy_safe_aggregation": True, "tenant_ids_exposed": False},
        )

    def percentiles(self, values: list[float] | tuple[float, ...], quantile: float) -> float:
        ordered = sorted(float(v) for v in values)
        if not ordered:
            return 0.0
        if quantile <= 0:
            return ordered[0]
        if quantile >= 1:
            return ordered[-1]

        index = (len(ordered) - 1) * quantile
        lower = int(index)
        upper = min(lower + 1, len(ordered) - 1)
        weight = index - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    def _weighted_score(self, signal: TeacherSignal) -> float:
        return (
            float(signal.assessment_quality) * 0.35
            + float(signal.learner_outcome) * 0.30
            + float(signal.retention_rate) * 0.20
            + float(signal.engagement_index) * 0.15
        )

    def _percentile_rank(self, score: float, peers: list[float]) -> float:
        if not peers:
            return 1.0
        less_or_equal = sum(1 for peer in peers if peer <= score)
        return less_or_equal / len(peers)

    def _privacy_safe_pool(self, *, subject: TeacherSignal, peers: tuple[TeacherSignal, ...]) -> tuple[TeacherSignal, ...]:
        filtered = tuple(peer for peer in peers if peer.teacher_id != subject.teacher_id)
        by_tenant: dict[str, list[TeacherSignal]] = defaultdict(list)
        for peer in filtered:
            by_tenant[peer.tenant_id].append(peer)

        safe_tenant_ids = [tenant_id for tenant_id, records in by_tenant.items() if len(records) >= 2]
        if subject.tenant_id in safe_tenant_ids:
            safe_tenant_ids.remove(subject.tenant_id)

        safe_pool = tuple(peer for peer in filtered if peer.tenant_id in safe_tenant_ids)
        self._validate_aggregation_safety(safe_pool)
        return safe_pool

    def _validate_aggregation_safety(self, signals: tuple[TeacherSignal, ...]) -> None:
        tenant_ids = {signal.tenant_id for signal in signals}
        if len(tenant_ids) < self._min_tenants:
            raise ValueError("aggregation safe check failed: insufficient cross-tenant coverage")
        if len(signals) < self._min_teacher_sample:
            raise ValueError("aggregation safe check failed: insufficient anonymized teacher sample")

    def _validate_cross_tenant_scores(self, teacher_scores: tuple[TeacherScore, ...]) -> None:
        if not teacher_scores:
            raise ValueError("no teacher scores provided")
        tenant_ids = {score.tenant_id for score in teacher_scores}
        if len(tenant_ids) < self._min_tenants:
            raise ValueError("no cross-tenant exposure allowed: minimum tenant threshold not met")
        if len(teacher_scores) < self._min_teacher_sample:
            raise ValueError("aggregation safe check failed: minimum teacher score sample not met")
