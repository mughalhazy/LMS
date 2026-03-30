from __future__ import annotations

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


HEALTH_ENDPOINT = "/health"
METRICS_ENDPOINT = "/metrics"


def health() -> dict[str, str]:
    return {"status": "ok", "service": "learning-analytics-service"}


def metrics() -> dict[str, int | str]:
    return {"service": "learning-analytics-service", "service_up": 1}
