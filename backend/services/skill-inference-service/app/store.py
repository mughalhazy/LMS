from __future__ import annotations

from collections import defaultdict

from .models import AnalyticsSignal, SkillGraphEdge, SkillGraphNode


class SkillInferenceStore:
    """In-memory persistence for the app layer."""

    def __init__(self) -> None:
        self.analytics_signals: dict[str, dict[str, dict[str, list[AnalyticsSignal]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self.skill_nodes: dict[str, SkillGraphNode] = {}
        self.skill_edges: list[SkillGraphEdge] = []

    def add_analytics_signals(self, signals: list[AnalyticsSignal]) -> None:
        for signal in signals:
            self.analytics_signals[signal.tenant_id][signal.learner_id][signal.skill_id].append(signal)

    def upsert_skill_nodes(self, nodes: list[SkillGraphNode]) -> None:
        for node in nodes:
            self.skill_nodes[node.skill_id] = node

    def append_skill_edges(self, edges: list[SkillGraphEdge]) -> None:
        for edge in edges:
            if edge not in self.skill_edges:
                self.skill_edges.append(edge)
