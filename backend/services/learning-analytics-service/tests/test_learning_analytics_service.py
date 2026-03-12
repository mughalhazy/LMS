from __future__ import annotations

from datetime import datetime, timezone

from app.main import LearningAnalyticsAPI
from app.models import (
    AssessmentAttempt,
    CourseCompletion,
    CourseEnrollment,
    LearningActivityEvent,
    PathProgressSnapshot,
)
from app.repository import AnalyticsRepository
from app.schemas import CourseAnalyticsQuery, LearningPathAnalyticsQuery, TimeWindowQuery


def test_learning_analytics_metrics_and_endpoints() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    repository = AnalyticsRepository(
        enrollments=[
            CourseEnrollment("l1", "c1", "co1", "enrolled", now),
            CourseEnrollment("l2", "c1", "co1", "in_progress", now),
            CourseEnrollment("l3", "c1", "co1", "enrolled", now),
        ],
        completions=[
            CourseCompletion("l1", "c1", "completed", now, 3600),
            CourseCompletion("l2", "c1", "completed", now, 5400),
        ],
        activities=[
            LearningActivityEvent("l1", "c1", "co1", 100, 20, 4, 5, now),
            LearningActivityEvent("l2", "c1", "co1", 50, 10, 2, 1, now),
            LearningActivityEvent("l3", "c1", "co1", 10, 2, 1, 0, now),
        ],
        assessment_attempts=[
            AssessmentAttempt("l1", "c1", "co1", 88, 100, now),
            AssessmentAttempt("l2", "c1", "co1", 70, 100, now),
        ],
        path_snapshots=[
            PathProgressSnapshot("l1", "lp1", "co1", 100, 10, 10, now),
            PathProgressSnapshot("l2", "lp1", "co1", 55, 5, 10, now),
            PathProgressSnapshot("l3", "lp1", "co1", 20, 2, 10, now),
        ],
    )

    api = LearningAnalyticsAPI(repository)

    course_completion = api.get_course_completion_analytics("c1", CourseAnalyticsQuery(cohort_id="co1"))
    assert course_completion["completion_rate"] == 66.67
    assert course_completion["median_time_to_complete_hours"] == 1.25

    engagement = api.get_learner_engagement_metrics("c1", CourseAnalyticsQuery(cohort_id="co1"))
    assert engagement["active_learners"] == 3
    assert engagement["scores_by_learner"]["l1"] == 100.0

    cohort = api.get_cohort_performance_metrics("co1", TimeWindowQuery())
    assert cohort["average_completion_rate"] == 66.67
    assert cohort["average_assessment_score"] == 79.0

    path = api.get_learning_path_completion_analysis("lp1", LearningPathAnalyticsQuery(cohort_id="co1"))
    assert path["completion_rate"] == 33.33
    assert path["dominant_drop_off_stage"] == "midpoint"
