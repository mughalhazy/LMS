# Learning Analytics Service

Service module for LMS learning analytics with support for:

- course completion analytics
- learner engagement metrics
- sentiment tracking across learner activity
- engagement trends over time
- engagement dashboards
- cohort performance metrics
- learning path completion analysis

## API surface

- `get_course_completion_analytics(course_id, query)`
- `get_learner_engagement_metrics(course_id, query)`
- `get_engagement_trends(course_id, query)`
- `get_engagement_dashboard(course_id, query)`
- `get_cohort_performance_metrics(cohort_id, query)`
- `get_learning_path_completion_analysis(learning_path_id, query)`

## Metric formulas implemented

- **Completion rate**: completed learners / active enrolled learners * 100.
- **Engagement score**: `0.35*active_minutes + 0.25*content_interactions + 0.20*assessment_attempts + 0.20*discussion_actions` after per-dimension normalization.
- **Sentiment tracking**: learner sentiment is averaged from event-level sentiment scores and categorized as positive (`>= 0.25`), neutral, or negative (`<= -0.25`).
- **Engagement trends**: daily snapshots combine active minutes and interactions, then track directional deltas alongside average sentiment.
- **Cohort performance**: aggregated completion, engagement, sentiment, and assessment metrics across cohort courses.
- **Path drop-off**: stage-to-stage drop-off percentages across assigned → started → midpoint → completed.
