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
        revenue_records=[],
    )
    repository.ingest_events(
        [
            {
                "event_type": "revenue",
                "tenant_id": "tenant-a",
                "plan_id": "pro",
                "amount": 150.0,
                "timestamp": now.isoformat(),
            },
            {
                "event_type": "revenue",
                "tenant_id": "tenant-a",
                "plan_id": "enterprise",
                "amount": 300.0,
                "timestamp": now.isoformat(),
            },
            {
                "event_type": "revenue",
                "tenant_id": "tenant-b",
                "plan_id": "pro",
                "amount": 500.0,
                "timestamp": now.isoformat(),
            },
        ]
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

    combined = api.get_learning_and_performance_metrics("c1", CourseAnalyticsQuery(tenant_id="tenant-a", cohort_id="co1"))
    assert combined["learning_metrics"]["completion_rate"] == 66.67
    assert combined["performance_metrics"]["average_assessment_score"] == 79.0

    revenue = api.service.revenue_metrics()
    assert revenue["total_revenue"] == 950.0
    assert revenue["per_tenant_revenue"] == {"tenant-a": 450.0, "tenant-b": 500.0}
    assert revenue["per_plan_revenue"] == {"enterprise": 300.0, "pro": 650.0}


def test_event_ingestion_pipeline_and_ai_output_shape() -> None:
    api = LearningAnalyticsAPI(AnalyticsRepository())
    result = api.ingest_events(
        [
            {
                "event_type": "enrollment",
                "tenant_id": "tenant-x",
                "learner_id": "lx1",
                "course_id": "cx1",
                "cohort_id": "cox1",
                "enrollment_status": "enrolled",
                "timestamp": "2026-01-01T00:00:00+00:00",
            },
            {
                "event_type": "completion",
                "tenant_id": "tenant-x",
                "learner_id": "lx1",
                "course_id": "cx1",
                "completion_status": "completed",
                "total_time_spent_seconds": 4500,
                "timestamp": "2026-01-02T00:00:00+00:00",
            },
            {
                "event_type": "activity",
                "tenant_id": "tenant-x",
                "learner_id": "lx1",
                "course_id": "cx1",
                "cohort_id": "cox1",
                "active_minutes": 45,
                "content_interactions": 8,
                "assessment_attempts": 1,
                "discussion_actions": 2,
                "sentiment_score": 0.4,
                "event_timestamp": "2026-01-02T00:15:00+00:00",
            },
            {
                "event_type": "assessment_attempt",
                "tenant_id": "tenant-x",
                "learner_id": "lx1",
                "course_id": "cx1",
                "cohort_id": "cox1",
                "score": 85,
                "max_score": 100,
                "timestamp": "2026-01-02T00:30:00+00:00",
            },
            {
                "event_type": "revenue",
                "tenant_id": "tenant-x",
                "plan_id": "starter",
                "amount": 199.99,
                "currency": "USD",
                "timestamp": "2026-01-02T00:30:30+00:00",
            },
            {"event_type": "unknown", "tenant_id": "tenant-x"},
        ]
    )

    assert result == {"processed": 5, "rejected": 1, "success_rate": 83.33}

    ai_payload = api.get_ai_service_signals("cx1", CourseAnalyticsQuery(tenant_id="tenant-x", cohort_id="cox1"))
    assert "learning_metrics" in ai_payload
    assert "performance_metrics" in ai_payload
    assert "revenue_metrics" in ai_payload
    assert ai_payload["revenue_metrics"]["total_revenue"] == 199.99
    assert ai_payload["learning_metrics"]["completion_rate"] == 100.0
    assert ai_payload["performance_metrics"]["average_assessment_score"] == 85.0


def test_risk_insights_emit_automation_events() -> None:
    now = datetime(2026, 1, 10, tzinfo=timezone.utc)
    repository = AnalyticsRepository(
        enrollments=[
            CourseEnrollment("tenant-z", "learner-1", "course-9", "co-z", "enrolled", now),
            CourseEnrollment("tenant-z", "learner-2", "course-9", "co-z", "enrolled", now),
        ],
        completions=[],
        activities=[
            LearningActivityEvent("tenant-z", "learner-1", "course-9", "co-z", 5, 1, 0, 0, now - timedelta(days=2), -0.7),
            LearningActivityEvent("tenant-z", "learner-1", "course-9", "co-z", 4, 1, 0, 0, now - timedelta(days=1), -0.8),
            LearningActivityEvent("tenant-z", "learner-2", "course-9", "co-z", 120, 30, 10, 9, now - timedelta(days=1), 0.6),
        ],
        assessment_attempts=[AssessmentAttempt("tenant-z", "learner-1", "course-9", "co-z", 40, 100, now - timedelta(days=1))],
        path_snapshots=[],
        revenue_records=[],
    )
    api = LearningAnalyticsAPI(repository)
    payload = api.get_learner_risk_insights("course-9", CourseAnalyticsQuery(tenant_id="tenant-z", cohort_id="co-z"))
    event_types = {row["event_type"] for row in payload["automation_events"]}
    assert "learning.low_engagement" in event_types
    assert "learning.low_performance" in event_types


def test_network_effect_insights_support_benchmarking_scoring_and_optimization() -> None:
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    repository = AnalyticsRepository(
        enrollments=[
            CourseEnrollment("tenant-net", "l1", "course-1", "co-a", "enrolled", now),
            CourseEnrollment("tenant-net", "l2", "course-1", "co-a", "enrolled", now),
            CourseEnrollment("tenant-net", "l3", "course-1", "co-b", "enrolled", now),
            CourseEnrollment("tenant-net", "l4", "course-1", "co-b", "enrolled", now),
        ],
        completions=[
            CourseCompletion("tenant-net", "l1", "course-1", "completed", now, 3600),
            CourseCompletion("tenant-net", "l3", "course-1", "completed", now, 4000),
            CourseCompletion("tenant-net", "l4", "course-1", "completed", now, 3000),
        ],
        activities=[
            LearningActivityEvent("tenant-net", "l1", "course-1", "co-a", 45, 6, 2, 1, now - timedelta(days=1), 0.4),
            LearningActivityEvent("tenant-net", "l2", "course-1", "co-a", 10, 2, 0, 0, now - timedelta(days=1), -0.2),
            LearningActivityEvent("tenant-net", "l3", "course-1", "co-b", 70, 8, 3, 3, now - timedelta(days=2), 0.6),
            LearningActivityEvent("tenant-net", "l4", "course-1", "co-b", 60, 6, 2, 2, now - timedelta(days=1), 0.3),
        ],
        assessment_attempts=[
            AssessmentAttempt("tenant-net", "l1", "course-1", "co-a", 68, 100, now),
            AssessmentAttempt("tenant-net", "l2", "course-1", "co-a", 52, 100, now),
            AssessmentAttempt("tenant-net", "l3", "course-1", "co-b", 85, 100, now),
            AssessmentAttempt("tenant-net", "l4", "course-1", "co-b", 88, 100, now),
        ],
        path_snapshots=[],
        revenue_records=[],
    )
    api = LearningAnalyticsAPI(repository)

    payload = api.get_network_effect_insights(
        "course-1",
        CourseAnalyticsQuery(tenant_id="tenant-net", cohort_id="co-a"),
    )

    assert set(payload.keys()) == {"tenant_id", "course_id", "cohort_id", "benchmarking", "scoring", "optimization"}
    assert payload["benchmarking"]["completion_gap"] < 0
    assert payload["benchmarking"]["assessment_gap"] < 0
    assert 0 <= payload["scoring"]["network_effect_score"] <= 100
    assert payload["scoring"]["contributors"]["completion_rate"] == 50.0
    assert payload["optimization"]["next_review_window_days"] == 14
    assert payload["optimization"]["priority_actions"][0]["focus_area"] in {"completion", "engagement", "performance", "optimization"}
