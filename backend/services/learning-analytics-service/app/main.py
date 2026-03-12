from __future__ import annotations

from .repository import AnalyticsRepository
from .schemas import CourseAnalyticsQuery, LearningPathAnalyticsQuery, TimeWindowQuery
from .service import LearningAnalyticsService


class LearningAnalyticsAPI:
    def __init__(self, repository: AnalyticsRepository | None = None) -> None:
        self.service = LearningAnalyticsService(repository or AnalyticsRepository())

    def get_course_completion_analytics(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.course_completion_analytics(
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_learner_engagement_metrics(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.learner_engagement_metrics(
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_cohort_performance_metrics(self, cohort_id: str, query: TimeWindowQuery) -> dict:
        return self.service.cohort_performance_metrics(
            cohort_id=cohort_id,
            start_at=query.start_at,
            end_at=query.end_at,
        )

    def get_learning_path_completion_analysis(self, learning_path_id: str, query: LearningPathAnalyticsQuery) -> dict:
        return self.service.learning_path_completion_analysis(
            learning_path_id=learning_path_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )
