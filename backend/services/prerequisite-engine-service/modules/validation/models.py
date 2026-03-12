from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Sequence


class EnrollmentDecision(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"


class DependencyType(str, Enum):
    STRICT = "strict"
    ADVISORY = "advisory"


@dataclass(frozen=True)
class LearnerProfile:
    learner_id: str
    tenant_id: str
    is_active: bool
    roles: Sequence[str] = field(default_factory=tuple)
    departments: Sequence[str] = field(default_factory=tuple)
    locations: Sequence[str] = field(default_factory=tuple)
    compliance_hold: bool = False


@dataclass(frozen=True)
class CourseCatalogEntry:
    course_id: str
    tenant_id: str
    status: str
    audience_roles: Sequence[str] = field(default_factory=tuple)
    audience_departments: Sequence[str] = field(default_factory=tuple)
    audience_locations: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class TranscriptRecord:
    course_id: str
    completion_status: str
    score: Optional[float]
    completed_at: Optional[datetime]


@dataclass(frozen=True)
class EquivalencyMapping:
    source_course_id: str
    equivalent_course_ids: Sequence[str]


@dataclass(frozen=True)
class PrerequisiteNode:
    node_id: str
    required_course_ids: Sequence[str]
    operator: str = "AND"  # AND or OR
    minimum_grade: Optional[float] = None
    valid_for_days: Optional[int] = None
    bridge_recommendations: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class CoursePrerequisiteRule:
    target_course_id: str
    prerequisite_nodes: Sequence[PrerequisiteNode]


@dataclass(frozen=True)
class LearningPathNode:
    node_id: str
    strict_dependency: DependencyType
    minimum_score: Optional[float] = None


@dataclass(frozen=True)
class LearningPathEdge:
    from_node_id: str
    to_node_id: str
    dependency_type: DependencyType


@dataclass(frozen=True)
class NodeProgress:
    node_id: str
    completion_status: str
    score: Optional[float]


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    reasons: Sequence[str]


@dataclass(frozen=True)
class PrerequisiteEvaluationResult:
    enrollment_decision: EnrollmentDecision
    unmet_prerequisites: Sequence[str]
    remedial_recommendations: Sequence[str]
    evaluated_at: datetime


@dataclass(frozen=True)
class LearningPathProgressionResult:
    unlocked_nodes: Sequence[str]
    locked_nodes: Sequence[str]
    advisory_warnings: Sequence[str]
    violations: Sequence[str]


TranscriptIndex = Dict[str, List[TranscriptRecord]]
PathNodeIndex = Dict[str, LearningPathNode]
