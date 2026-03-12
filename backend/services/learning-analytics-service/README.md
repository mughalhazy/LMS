# Learning Analytics Service

Service module for LMS learning analytics with support for:

- course completion analytics
- learner engagement metrics
- cohort performance metrics
- learning path completion analysis

## API surface

- `get_course_completion_analytics(course_id, query)`
- `get_learner_engagement_metrics(course_id, query)`
- `get_cohort_performance_metrics(cohort_id, query)`
- `get_learning_path_completion_analysis(learning_path_id, query)`

## Metric formulas implemented

- **Completion rate**: completed learners / active enrolled learners * 100.
- **Engagement score**: `0.35*active_minutes + 0.25*content_interactions + 0.20*assessment_attempts + 0.20*discussion_actions` after per-dimension normalization.
- **Cohort performance**: aggregated completion and engagement metrics across cohort courses plus average assessment score.
- **Path drop-off**: stage-to-stage drop-off percentages across assigned → started → midpoint → completed.
