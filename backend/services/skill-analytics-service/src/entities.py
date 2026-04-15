from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Skill:
    skill_id: str
    name: str
    difficulty_base: float = 0.0


@dataclass
class UserSkillEvidence:
    tenant_id: str
    learner_id: str
    skill_id: str
    evidence_type: str
    normalized_score: float
    evidence_date: datetime
    verified: bool = False
    difficulty_weight: float = 1.0


@dataclass
class UserSkill:
    tenant_id: str
    learner_id: str
    skill_id: str
    current_level: float = 0.0
    confidence: float = 0.0
    decay_rate: float = 0.02
    last_assessed_at: Optional[datetime] = None


@dataclass
class RoleSkillRequirement:
    role_profile_id: str
    skill_id: str
    target_level: float
    business_criticality: float
    role_weight: float


@dataclass
class LearnerSkillAnalyticsAggregate:
    tenant_id: str
    learner_id: str
    skills: Dict[str, UserSkill] = field(default_factory=dict)
    evidence_by_skill: Dict[str, List[UserSkillEvidence]] = field(default_factory=dict)
    trend_snapshots: Dict[str, List[tuple[datetime, float]]] = field(default_factory=dict)
