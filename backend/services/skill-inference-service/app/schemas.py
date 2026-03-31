from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AnalyticsSignalIn:
    skill_id: str
    signal_id: str
    signal_type: str
    score: float
    confidence: float
    occurred_at: datetime
    verified: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class IngestAnalyticsRequest:
    tenant_id: str
    learner_id: str
    signals: list[AnalyticsSignalIn]


@dataclass
class SkillNodeIn:
    skill_id: str
    name: str
    category_id: str
    difficulty_base: float = 0.5


@dataclass
class SkillEdgeIn:
    source_skill_id: str
    target_skill_id: str
    relation_type: str
    relation_weight: float = 1.0


@dataclass
class KnowledgeGraphUpsertRequest:
    skills: list[SkillNodeIn] = field(default_factory=list)
    edges: list[SkillEdgeIn] = field(default_factory=list)


@dataclass
class InferenceRequest:
    tenant_id: str
    learner_id: str
    as_of: datetime | None = None


@dataclass
class ProgressionQuery:
    tenant_id: str
    learner_id: str
