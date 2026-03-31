from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AnalyticsSignal:
    tenant_id: str
    learner_id: str
    skill_id: str
    signal_id: str
    signal_type: str
    score: float
    confidence: float
    occurred_at: datetime
    verified: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillGraphNode:
    skill_id: str
    name: str
    category_id: str
    difficulty_base: float = 0.5


@dataclass(frozen=True)
class SkillGraphEdge:
    source_skill_id: str
    target_skill_id: str
    relation_type: str
    relation_weight: float = 1.0
