"""Metric catalog for the progress aggregation module."""

METRICS_DEFINED = {
    "course_progress_percentage": {
        "description": "Percent of completed lessons for a learner enrollment in a course.",
        "formula": "(completed_lessons / total_lessons) * 100",
        "range": "0-100",
    },
    "learning_path_completion_percentage": {
        "description": "Percent completion across required path nodes with elective contribution.",
        "formula": "weighted_required_completion + weighted_elective_completion",
        "range": "0-100",
    },
    "learning_path_status": {
        "description": "Derived status for a learner path progress snapshot.",
        "values": ["not_started", "in_progress", "completed"],
    },
    "cohort_average_progress_percentage": {
        "description": "Arithmetic mean of course progress percentage across learners in cohort.",
        "formula": "sum(learner_progress_percentage) / learner_count",
        "range": "0-100",
    },
    "cohort_completion_rate_percentage": {
        "description": "Percent of cohort learners in completed status.",
        "formula": "(completed_learners / learner_count) * 100",
        "range": "0-100",
    },
    "cohort_on_track_vs_at_risk_ratio": {
        "description": "Ratio between learners considered on-track and at-risk.",
        "formula": "on_track_count / max(at_risk_count, 1)",
        "range": "0+",
    },
}
