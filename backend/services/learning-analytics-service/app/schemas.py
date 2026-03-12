from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimeWindowQuery:
    start_at: datetime | None = None
    end_at: datetime | None = None


@dataclass
class CourseAnalyticsQuery(TimeWindowQuery):
    cohort_id: str | None = None


@dataclass
class LearningPathAnalyticsQuery(TimeWindowQuery):
    cohort_id: str | None = None
