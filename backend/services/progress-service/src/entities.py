from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class LessonProgress:
    tenant_id: str
    learner_id: str
    course_id: str
    lesson_id: str
    enrollment_id: str
    completion_status: str
    score: Optional[float]
    time_spent_seconds: int
    completed_at: Optional[datetime]
    attempt_count: int


@dataclass
class CourseProgress:
    tenant_id: str
    learner_id: str
    course_id: str
    enrollment_id: str
    completion_status: str
    final_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    total_time_spent_seconds: int
    certificate_id: Optional[str]


@dataclass
class LearningPathProgress:
    tenant_id: str
    learner_id: str
    learning_path_id: str
    assigned_course_ids: List[str]
    completed_course_ids: List[str] = field(default_factory=list)
    progress_percentage: float = 0.0
    current_course_id: Optional[str] = None
    status: str = "not_started"
    last_activity_at: Optional[datetime] = None
    expected_completion_date: Optional[datetime] = None


@dataclass
class LearnerProgressAggregate:
    tenant_id: str
    learner_id: str
    courses: Dict[str, CourseProgress] = field(default_factory=dict)
    lessons: Dict[str, Dict[str, LessonProgress]] = field(default_factory=dict)
    learning_paths: Dict[str, LearningPathProgress] = field(default_factory=dict)
