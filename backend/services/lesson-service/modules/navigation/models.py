from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class LessonStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class CompletionPolicy(str, Enum):
    VIEW = "view"
    QUIZ_PASS = "quiz_pass"
    MANUAL = "manual"


class LockingMode(str, Enum):
    NONE = "none"
    SEQUENTIAL = "sequential"
    PREREQUISITE = "prerequisite"


@dataclass(frozen=True)
class Lesson:
    lesson_id: str
    course_id: str
    order_index: int
    status: LessonStatus = LessonStatus.DRAFT
    completion_policy: CompletionPolicy = CompletionPolicy.VIEW
    prerequisite_lesson_ids: Set[str] = field(default_factory=set)


@dataclass
class LearnerProgress:
    user_id: str
    course_id: str
    completed_lessons: Set[str] = field(default_factory=set)
    lesson_scores: Dict[str, float] = field(default_factory=dict)
    lesson_views: Set[str] = field(default_factory=set)


@dataclass(frozen=True)
class NavigationResult:
    current_lesson_id: str
    target_lesson_id: Optional[str]
    reason: str


@dataclass(frozen=True)
class CompletionResult:
    lesson_id: str
    completed: bool
    reason: str


@dataclass(frozen=True)
class LockResult:
    lesson_id: str
    locked: bool
    reason: str


@dataclass(frozen=True)
class CourseNavigationState:
    lessons_in_order: List[Lesson]
    locking_mode: LockingMode = LockingMode.SEQUENTIAL
    minimum_passing_score: float = 0.7
