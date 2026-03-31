from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
    now = datetime(2026, 1, 3, tzinfo=timezone.utc)
    repository = AnalyticsRepository(
        enrollments=[
            CourseEnrollment("tenant-a", "l1", "c1", "co1", "enrolled", now),
            CourseEnrollment("tenant-a", "l2", "c1", "co1", "in_progress", now),
            CourseEnrollment("tenant-a", "l3", "c1", "co1", "enrolled", now),
            CourseEnrollment("tenant-b", "l1", "c1", "co1", "enrolled", now),
        ],
        completions=[
            CourseCompletion("tenant-a", "l1", "c1", "completed", now, 3600),
            CourseCompletion("tenant-a", "l2", "c1", "completed", now, 5400),
            CourseCompletion("tenant-b", "l1", "c1", "completed", now, 60),
        ],
        activities=[
            LearningActivityEvent("tenant-a", "l1", "c1", "co1", 70, 12, 3, 3, now - timedelta(days=2), 0.7),
            LearningActivityEvent("tenant-a", "l2", "c1", "co1", 30, 6, 1, 1, now - timedelta(days=2), -0.1),
            LearningActivityEvent("tenant-a", "l3", "c1", "co1", 10, 2, 1, 0, now - timedelta(days=2), -0.5),
            LearningActivityEvent("tenant-a", "l1", "c1", "co1", 100, 20, 4, 5, now - timedelta(days=1), 0.9),
            LearningActivityEvent("tenant-a", "l2", "c1", "co1", 50, 10, 2, 1, now - timedelta(days=1), 0.2),
            LearningActivityEvent("tenant-a", "l3", "c1", "co1", 10, 2, 1, 0, now - timedelta(days=1), -0.6),
            LearningActivityEvent("tenant-b", "l1", "c1", "co1", 1000, 200, 20, 20, now, 0.8),
        ],
        assessment_attempts=[
            AssessmentAttempt("tenant-a", "l1", "c1", "co1", 88, 100, now),
            AssessmentAttempt("tenant-a", "l2", "c1", "co1", 70, 100, now),
            AssessmentAttempt("tenant-b", "l1", "c1", "co1", 10, 100, now),
        ],
        path_snapshots=[
            PathProgressSnapshot("tenant-a", "l1", "lp1", "co1", 100, 10, 10, now),
            PathProgressSnapshot("tenant-a", "l2", "lp1", "co1", 55, 5, 10, now),
            PathProgressSnapshot("tenant-a", "l3", "lp1", "co1", 20, 2, 10, now),
            PathProgressSnapshot("tenant-b", "l1", "lp1", "co1", 100, 10, 10, now),
        ],
    )

    api = LearningAnalyticsAPI(repository)

    course_completion = api.get_course_completion_analytics("c1", CourseAnalyticsQuery(tenant_id="tenant-a", cohort_id="co1"))
    assert course_completion["completion_rate"] == 66.67
    assert course_completion["median_time_to_complete_hours"] == 1.25

    engagement = api.get_learner_engagement_metrics("c1", CourseAnalyticsQuery(tenant_id="tenant-a", cohort_id="co1"))
    assert engagement["active_learners"] == 3
    assert engagement["scores_by_learner"]["l1"] == 100.0
    assert engagement["average_sentiment"] == 0.1
    assert engagement["sentiment_distribution"] == {"positive": 1, "neutral": 1, "negative": 1}
    assert engagement["sentiment_by_learner"]["l3"]["label"] == "negative"

    trends = api.get_engagement_trends("c1", CourseAnalyticsQuery(tenant_id="tenant-a", cohort_id="co1"))
    assert trends["periods"] == 2
    assert trends["direction"] == "up"
    assert trends["trend_points"][1]["engagement_delta"] > 0

    dashboard = api.get_engagement_dashboard("c1", CourseAnalyticsQuery(tenant_id="tenant-a", cohort_id="co1"))
    assert dashboard["summary"]["trend_direction"] == "up"
    assert len(dashboard["widgets"]) == 3
    assert dashboard["widgets"][1]["widget_id"] == "sentiment_tracking"

    cohort = api.get_cohort_performance_metrics("co1", TimeWindowQuery(tenant_id="tenant-a"))
    assert cohort["average_completion_rate"] == 66.67
    assert cohort["average_assessment_score"] == 79.0
    assert cohort["average_sentiment"] == 0.1

    path = api.get_learning_path_completion_analysis("lp1", LearningPathAnalyticsQuery(tenant_id="tenant-a", cohort_id="co1"))
    assert path["completion_rate"] == 33.33
    assert path["dominant_drop_off_stage"] == "midpoint"

    risk = api.get_learner_risk_insights("c1", CourseAnalyticsQuery(tenant_id="tenant-a", cohort_id="co1"))
    assert risk["summary"]["total_learners"] == 3
    assert risk["summary"]["alert_totals"]["low_engagement"] == 1
    assert risk["summary"]["alert_totals"]["poor_performance"] == 1
    assert risk["risk_insights"][0]["learner_id"] == "l3"
    assert "low_engagement" in risk["risk_insights"][0]["alerts"]
    assert "poor_performance" in risk["risk_insights"][0]["alerts"]
