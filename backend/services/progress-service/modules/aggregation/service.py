"""Progress aggregation logic for course, learning path, and cohort rollups."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Literal

LearningPathRule = Literal[
    "all_required_complete",
    "required_plus_n_electives",
    "milestone_based",
    "score_threshold",
]


@dataclass(frozen=True)
class CourseProgressInput:
    total_lessons: int
    completed_lessons: int


@dataclass(frozen=True)
class LearningPathNodeProgress:
    node_id: str
    is_required: bool
    completed: bool
    score: float | None = None
    min_score: float | None = None
    is_milestone: bool = False


@dataclass(frozen=True)
class LearningPathCompletionInput:
    rule: LearningPathRule
    nodes: list[LearningPathNodeProgress]
    elective_min_select: int = 0


@dataclass(frozen=True)
class CohortLearnerProgress:
    learner_id: str
    progress_percentage: float
    status: Literal["not_started", "in_progress", "completed"]
    overdue: bool = False


@dataclass(frozen=True)
class CohortProgressSummary:
    learner_count: int
    not_started_count: int
    in_progress_count: int
    completed_count: int
    overdue_count: int
    at_risk_count: int
    on_track_count: int
    average_progress_percentage: float
    completion_rate_percentage: float
    on_track_vs_at_risk_ratio: float


def _clamp_percentage(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def calculate_course_progress_percentage(payload: CourseProgressInput) -> float:
    """Compute course completion percentage from lesson completion counts."""
    if payload.total_lessons <= 0:
        return 0.0

    completed = max(0, min(payload.completed_lessons, payload.total_lessons))
    return _clamp_percentage((completed / payload.total_lessons) * 100)


def calculate_learning_path_completion(
    payload: LearningPathCompletionInput,
) -> tuple[float, Literal["not_started", "in_progress", "completed"]]:
    """Calculate learning path completion percent and derived lifecycle status."""
    if not payload.nodes:
        return 0.0, "not_started"

    required_nodes = [node for node in payload.nodes if node.is_required]
    elective_nodes = [node for node in payload.nodes if not node.is_required]

    def is_node_complete(node: LearningPathNodeProgress) -> bool:
        if not node.completed:
            return False
        if node.min_score is None:
            return True
        return (node.score or 0.0) >= node.min_score

    required_completed = sum(1 for n in required_nodes if is_node_complete(n))
    elective_completed = sum(1 for n in elective_nodes if is_node_complete(n))

    required_weight = 1.0 if required_nodes else 0.0
    elective_weight = 0.0 if not elective_nodes else 0.2
    required_component = (
        (required_completed / len(required_nodes)) * (100 * required_weight)
        if required_nodes
        else 100.0
    )
    elective_component = 0.0
    if elective_nodes:
        denom = max(payload.elective_min_select, len(elective_nodes))
        elective_component = (min(elective_completed, denom) / denom) * (100 * elective_weight)

    percentage = _clamp_percentage(required_component + elective_component)

    if payload.rule == "all_required_complete":
        complete = required_completed == len(required_nodes)
    elif payload.rule == "required_plus_n_electives":
        complete = (
            required_completed == len(required_nodes)
            and elective_completed >= payload.elective_min_select
        )
    elif payload.rule == "milestone_based":
        milestones = [node for node in payload.nodes if node.is_milestone]
        complete = all(is_node_complete(m) for m in milestones) and (
            required_completed == len(required_nodes)
        )
    else:  # score_threshold
        complete = required_completed == len(required_nodes)

    if complete:
        return 100.0, "completed"
    if percentage <= 0:
        return 0.0, "not_started"
    return percentage, "in_progress"


def summarize_cohort_progress(
    learner_progress: list[CohortLearnerProgress],
    at_risk_threshold: float = 50.0,
) -> CohortProgressSummary:
    """Aggregate learner progress snapshots into cohort-level summary metrics."""
    if not learner_progress:
        return CohortProgressSummary(
            learner_count=0,
            not_started_count=0,
            in_progress_count=0,
            completed_count=0,
            overdue_count=0,
            at_risk_count=0,
            on_track_count=0,
            average_progress_percentage=0.0,
            completion_rate_percentage=0.0,
            on_track_vs_at_risk_ratio=0.0,
        )

    not_started_count = sum(1 for p in learner_progress if p.status == "not_started")
    in_progress_count = sum(1 for p in learner_progress if p.status == "in_progress")
    completed_count = sum(1 for p in learner_progress if p.status == "completed")
    overdue_count = sum(1 for p in learner_progress if p.overdue)
    at_risk_count = sum(
        1
        for p in learner_progress
        if p.status != "completed"
        and (p.overdue or p.progress_percentage < at_risk_threshold)
    )
    on_track_count = len(learner_progress) - at_risk_count

    avg_progress = _clamp_percentage(mean(p.progress_percentage for p in learner_progress))
    completion_rate = _clamp_percentage((completed_count / len(learner_progress)) * 100)
    ratio = round(on_track_count / max(at_risk_count, 1), 2)

    return CohortProgressSummary(
        learner_count=len(learner_progress),
        not_started_count=not_started_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        overdue_count=overdue_count,
        at_risk_count=at_risk_count,
        on_track_count=on_track_count,
        average_progress_percentage=avg_progress,
        completion_rate_percentage=completion_rate,
        on_track_vs_at_risk_ratio=ratio,
    )
