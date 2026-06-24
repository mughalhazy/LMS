"""API schemas for learning-path-service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CompletionRulesIn(BaseModel):
    mode: str = "all_required_complete"
    required_plus_n_electives: Optional[int] = None
    strict_due_date: bool = False
    due_date: Optional[datetime] = None
    recertification_interval_days: Optional[int] = None
    grace_window_days: int = 0


class CreateLearningPathRequest(BaseModel):
    title: str
    owner_id: str
    description: Optional[str] = None
    audience: Optional[Dict[str, str]] = None
    completion_rules: Optional[CompletionRulesIn] = None


class PublishPathRequest(BaseModel):
    change_reason: str


class ConfigureCompletionRulesRequest(BaseModel):
    rules: CompletionRulesIn
    change_reason: str


class PathNodeIn(BaseModel):
    node_type: str
    ref_id: str
    sequence_index: int
    is_required: bool
    min_score: Optional[float] = None
    estimated_duration_mins: Optional[int] = None
    elective_group_id: Optional[str] = None


class PathEdgeIn(BaseModel):
    from_node_id: str
    to_node_id: str
    relation: str
    condition: Optional[Dict[str, str]] = None


class SetNodesRequest(BaseModel):
    nodes: List[PathNodeIn] = Field(default_factory=list)


class SetEdgesRequest(BaseModel):
    edges: List[PathEdgeIn] = Field(default_factory=list)


class AssignPathRequest(BaseModel):
    assignment_type: str
    target_ref: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    assigned_by: str


class EvaluateCompletionRequest(BaseModel):
    progress_by_node_id: Dict[str, Dict[str, Any]]
    completed_at: Optional[datetime] = None


class CreateElectiveGroupRequest(BaseModel):
    # B04-002: learning-path-spec.md data model — elective_group management
    name: str
    min_select: int = Field(ge=1)
    max_select: int = Field(ge=1)
    node_ids: List[str] = Field(default_factory=list)
