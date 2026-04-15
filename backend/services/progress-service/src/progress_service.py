from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional

from .entities import (
    CourseProgress,
    LearnerProgressAggregate,
    LearningPathProgress,
    LessonProgress,
)


class ProgressTrackingService:
    """Tenant-scoped progress tracking service for lesson, course, and learning path state."""

    def __init__(self) -> None:
        self._tenant_learner_progress: Dict[str, Dict[str, LearnerProgressAggregate]] = {}
        self._applied_reference_tokens: Dict[str, set[str]] = {}

    def _get_or_create_aggregate(self, tenant_id: str, learner_id: str) -> LearnerProgressAggregate:
        tenant_bucket = self._tenant_learner_progress.setdefault(tenant_id, {})
        if learner_id not in tenant_bucket:
            tenant_bucket[learner_id] = LearnerProgressAggregate(
                tenant_id=tenant_id,
                learner_id=learner_id,
            )
        return tenant_bucket[learner_id]

    def assign_learning_path(
        self,
        tenant_id: str,
        learner_id: str,
        learning_path_id: str,
        assigned_course_ids: List[str],
        expected_completion_date: Optional[datetime] = None,
    ) -> LearningPathProgress:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        path = LearningPathProgress(
            tenant_id=tenant_id,
            learner_id=learner_id,
            learning_path_id=learning_path_id,
            assigned_course_ids=assigned_course_ids,
            current_course_id=assigned_course_ids[0] if assigned_course_ids else None,
            status="in_progress" if assigned_course_ids else "completed",
            expected_completion_date=expected_completion_date,
            last_activity_at=datetime.utcnow(),
        )
        if not assigned_course_ids:
            path.progress_percentage = 100.0
        aggregate.learning_paths[learning_path_id] = path
        return path

    def track_lesson_completion(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        lesson_id: str,
        enrollment_id: str,
        completion_status: str,
        score: Optional[float],
        time_spent_seconds: int,
        attempt_count: int,
    ) -> LessonProgress:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        lesson_bucket = aggregate.lessons.setdefault(course_id, {})

        lesson_progress = LessonProgress(
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment_id,
            completion_status=completion_status,
            score=score,
            time_spent_seconds=time_spent_seconds,
            completed_at=datetime.utcnow() if completion_status == "completed" else None,
            attempt_count=attempt_count,
        )
        lesson_bucket[lesson_id] = lesson_progress

        self._recompute_course_progress(
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            enrollment_id=enrollment_id,
        )
        self._refresh_learning_path_progress(tenant_id=tenant_id, learner_id=learner_id)
        return lesson_progress

    def on_progress_milestone(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        lesson_id: str,
        enrollment_id: str,
        progress_percentage: float,
    ) -> LessonProgress:
        status = "completed" if progress_percentage >= 100 else "in_progress"
        return self.track_lesson_completion(
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment_id,
            completion_status=status,
            score=None,
            time_spent_seconds=0,
            attempt_count=1,
        )

    def on_completion(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        lesson_id: str,
        enrollment_id: str,
        score: float | None = None,
    ) -> LessonProgress:
        return self.track_lesson_completion(
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment_id,
            completion_status="completed",
            score=score,
            time_spent_seconds=0,
            attempt_count=1,
        )

    def record_offline_progress(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        lesson_id: str,
        enrollment_id: str,
        completion_percent: float,
        playback_position: int,
        reference_token: str,
        attempt_count: int = 1,
    ) -> LessonProgress:
        token = reference_token.strip()
        tenant_tokens = self._applied_reference_tokens.setdefault(tenant_id, set())
        if token and token in tenant_tokens:
            aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
            existing = aggregate.lessons.get(course_id, {}).get(lesson_id)
            if existing:
                return existing

        status = "completed" if completion_percent >= 100 else "in_progress"
        lesson = self.track_lesson_completion(
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment_id,
            completion_status=status,
            score=None,
            time_spent_seconds=max(0, int(playback_position)),
            attempt_count=max(1, int(attempt_count)),
        )
        if token:
            tenant_tokens.add(token)
        return lesson

    def _recompute_course_progress(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        enrollment_id: str,
    ) -> CourseProgress:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        lessons = list(aggregate.lessons.get(course_id, {}).values())

        completed_lessons = [lesson for lesson in lessons if lesson.completion_status == "completed"]
        completion_status = "completed" if lessons and len(completed_lessons) == len(lessons) else "in_progress"

        final_score = None
        if completed_lessons:
            score_values = [item.score for item in completed_lessons if item.score is not None]
            if score_values:
                final_score = round(sum(score_values) / len(score_values), 2)

        existing = aggregate.courses.get(course_id)
        started_at = existing.started_at if existing else datetime.utcnow()

        course = CourseProgress(
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            enrollment_id=enrollment_id,
            completion_status=completion_status,
            final_score=final_score,
            started_at=started_at,
            completed_at=datetime.utcnow() if completion_status == "completed" else None,
            total_time_spent_seconds=sum(lesson.time_spent_seconds for lesson in lessons),
            certificate_id=None,
        )
        aggregate.courses[course_id] = course
        return course

    def _refresh_learning_path_progress(self, *, tenant_id: str, learner_id: str) -> None:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        completed_courses = {
            course_id
            for course_id, course in aggregate.courses.items()
            if course.completion_status == "completed"
        }

        for path in aggregate.learning_paths.values():
            assigned = path.assigned_course_ids
            if not assigned:
                path.completed_course_ids = []
                path.progress_percentage = 100.0
                path.current_course_id = None
                path.status = "completed"
                path.last_activity_at = datetime.utcnow()
                continue

            path.completed_course_ids = [course_id for course_id in assigned if course_id in completed_courses]
            path.progress_percentage = round((len(path.completed_course_ids) / len(assigned)) * 100, 2)
            remaining = [course_id for course_id in assigned if course_id not in completed_courses]
            path.current_course_id = remaining[0] if remaining else None
            path.status = "completed" if not remaining else "in_progress"
            path.last_activity_at = datetime.utcnow()

    def get_learner_progress(self, tenant_id: str, learner_id: str) -> Dict[str, object]:
        tenant_bucket = self._tenant_learner_progress.get(tenant_id, {})
        aggregate = tenant_bucket.get(learner_id)
        if not aggregate:
            return {
                "tenant_id": tenant_id,
                "learner_id": learner_id,
                "courses": {},
                "lessons": {},
                "learning_paths": {},
            }

        return {
            "tenant_id": aggregate.tenant_id,
            "learner_id": aggregate.learner_id,
            "courses": {course_id: asdict(course) for course_id, course in aggregate.courses.items()},
            "lessons": {
                course_id: {lesson_id: asdict(lesson) for lesson_id, lesson in lesson_map.items()}
                for course_id, lesson_map in aggregate.lessons.items()
            },
            "learning_paths": {
                path_id: asdict(path) for path_id, path in aggregate.learning_paths.items()
            },
        }
