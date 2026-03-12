from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


PathStatus = str
NodeType = str
EdgeRelation = str
CompletionMode = str


@dataclass
class CompletionRules:
    mode: CompletionMode = "all_required_complete"
    required_plus_n_electives: Optional[int] = None
    strict_due_date: bool = False
    due_date: Optional[datetime] = None
    recertification_interval_days: Optional[int] = None
    grace_window_days: int = 0


@dataclass
class LearningPath:
    tenant_id: str
    title: str
    owner_id: str
    description: Optional[str] = None
    audience: Dict[str, str] = field(default_factory=dict)
    status: PathStatus = "draft"
    version: int = 1
    path_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    completion_rules: CompletionRules = field(default_factory=CompletionRules)


@dataclass
class PathNode:
    path_id: str
    node_type: NodeType
    ref_id: str
    sequence_index: int
    is_required: bool
    min_score: Optional[float] = None
    estimated_duration_mins: Optional[int] = None
    elective_group_id: Optional[str] = None
    node_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class PathEdge:
    path_id: str
    from_node_id: str
    to_node_id: str
    relation: EdgeRelation
    condition: Optional[Dict[str, str]] = None
    edge_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class NodeProgress:
    completed: bool
    score: Optional[float] = None
    completed_at: Optional[datetime] = None


@dataclass
class LearningPathProgress:
    path_id: str
    completed_at: Optional[datetime]
    overdue: bool
    expired: bool

    @classmethod
    def in_progress(cls, path_id: str, overdue: bool = False) -> "LearningPathProgress":
        return cls(path_id=path_id, completed_at=None, overdue=overdue, expired=False)

    @classmethod
    def complete(cls, path_id: str, completed_at: datetime, overdue: bool, expired: bool = False) -> "LearningPathProgress":
        return cls(path_id=path_id, completed_at=completed_at, overdue=overdue, expired=expired)

    def with_recertification(self, rules: CompletionRules) -> "LearningPathProgress":
        if not self.completed_at or not rules.recertification_interval_days:
            return self
        expiry = self.completed_at + timedelta(days=rules.recertification_interval_days + rules.grace_window_days)
        if utc_now() > expiry:
            return LearningPathProgress.in_progress(path_id=self.path_id, overdue=self.overdue)
        return self
