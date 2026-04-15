from __future__ import annotations

from typing import Any

from .repository import AnalyticsRepository
from .schemas import CourseAnalyticsQuery, LearningPathAnalyticsQuery, TimeWindowQuery
from .service import LearningAnalyticsService


class LearningAnalyticsAPI:
    def __init__(self, repository: AnalyticsRepository | None = None) -> None:
        self.service = LearningAnalyticsService(repository or AnalyticsRepository())

    def get_course_completion_analytics(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.course_completion_analytics(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_learner_engagement_metrics(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.learner_engagement_metrics(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_engagement_trends(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.engagement_trends(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_engagement_dashboard(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.engagement_dashboard(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_cohort_performance_metrics(self, cohort_id: str, query: TimeWindowQuery) -> dict:
        return self.service.cohort_performance_metrics(
            tenant_id=query.tenant_id,
            cohort_id=cohort_id,
            start_at=query.start_at,
            end_at=query.end_at,
        )

    def get_learning_path_completion_analysis(self, learning_path_id: str, query: LearningPathAnalyticsQuery) -> dict:
        return self.service.learning_path_completion_analysis(
            tenant_id=query.tenant_id,
            learning_path_id=learning_path_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def ingest_events(self, events: list[dict[str, Any]]) -> dict[str, int | float]:
        return self.service.ingest_events(events)

    def get_learning_and_performance_metrics(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.learning_and_performance_metrics(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_revenue_metrics(self, query: TimeWindowQuery) -> dict:
        return self.service.revenue_metrics(
            start_at=query.start_at,
            end_at=query.end_at,
            tenant_id=query.tenant_id,
            owner_id=query.owner_id,
        )

    def get_cashflow_metrics(self, query: TimeWindowQuery) -> dict:
        return self.service.cashflow_metrics(
            start_at=query.start_at,
            end_at=query.end_at,
            tenant_id=query.tenant_id,
            owner_id=query.owner_id,
        )

    def get_profitability_metrics(self, query: TimeWindowQuery) -> dict:
        return self.service.profitability_metrics(
            start_at=query.start_at,
            end_at=query.end_at,
            tenant_id=query.tenant_id,
            owner_id=query.owner_id,
        )

    def get_owner_economics(self, query: TimeWindowQuery) -> dict:
        return {
            "revenue": self.get_revenue_metrics(query),
            "cashflow": self.get_cashflow_metrics(query),
            "profitability": self.get_profitability_metrics(query),
        }

    def get_ai_service_signals(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.ai_service_signals(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_learner_risk_insights(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.learner_risk_insights(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_network_effect_insights(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.network_effect_insights(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )


HEALTH_ENDPOINT = "/health"
METRICS_ENDPOINT = "/metrics"


def health() -> dict[str, str]:
    return {"status": "ok", "service": "learning-analytics-service"}


def metrics() -> dict[str, int | str]:
    return {"service": "learning-analytics-service", "service_up": 1}
