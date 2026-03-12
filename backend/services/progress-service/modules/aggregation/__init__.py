"""Progress aggregation module for course, learning path, and cohort metrics."""

from .metrics import METRICS_DEFINED
from .service import (
    CohortLearnerProgress,
    CohortProgressSummary,
    CourseProgressInput,
    LearningPathCompletionInput,
    LearningPathNodeProgress,
    LearningPathRule,
    calculate_course_progress_percentage,
    calculate_learning_path_completion,
    summarize_cohort_progress,
)

__all__ = [
    "CohortLearnerProgress",
    "CohortProgressSummary",
    "CourseProgressInput",
    "LearningPathCompletionInput",
    "LearningPathNodeProgress",
    "LearningPathRule",
    "METRICS_DEFINED",
    "calculate_course_progress_percentage",
    "calculate_learning_path_completion",
    "summarize_cohort_progress",
]
