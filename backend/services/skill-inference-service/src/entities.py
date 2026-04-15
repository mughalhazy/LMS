from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SkillNode:
    skill_id: str
    name: str
    category_id: str
    difficulty_base: float = 0.5
    status: str = "active"


@dataclass
class SkillEdge:
    source_skill_id: str
    target_skill_id: str
    relation_type: str
    relation_weight: float = 1.0


@dataclass
class CourseSkillMapping:
    course_id: str
    skill_id: str
    coverage_level: str
    skill_gain_expected: float
    evidence_weight: float


@dataclass
class LearnerSkillEvidence:
    tenant_id: str
    learner_id: str
    skill_id: str
    evidence_id: str
    evidence_type: str
    normalized_score: float
    confidence_weight: float
    timestamp: datetime
    verified: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class LearnerSkillState:
    tenant_id: str
    learner_id: str
    skill_id: str
    current_level: int
    confidence: float
    mastery_score: float
    predicted_mastery_band: str
    evidence_count: int
    last_assessed_at: Optional[datetime]
    decay_rate: float = 0.02
    source: str = "inference"


@dataclass
class SkillInferenceResult:
    tenant_id: str
    learner_id: str
    inferred_at: datetime
    updated_skills: Dict[str, LearnerSkillState]
