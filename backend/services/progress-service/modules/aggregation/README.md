# Progress Aggregation Module

This module implements progress aggregation capabilities for:

- Course progress percentage (`LessonCompletionTracked` to course-level rollup)
- Learning path completion (`LearningPathProgressUpdated` aligned with path completion rules)
- Cohort progress summaries (manager/dashboard-level cohort snapshots)

## Exposed APIs

- `calculate_course_progress_percentage(payload)`
- `calculate_learning_path_completion(payload)`
- `summarize_cohort_progress(learner_progress, at_risk_threshold=50.0)`

## Metric Definitions

See `metrics.py` for canonical metric definitions and formulas.
