from __future__ import annotations

from typing import Dict, Optional

from .models import (
    CompletionPolicy,
    CompletionResult,
    CourseNavigationState,
    LearnerProgress,
    Lesson,
    LessonStatus,
    LockResult,
    LockingMode,
    NavigationResult,
)


class LessonNavigationService:
    """Navigation and locking engine for lesson progression."""

    def __init__(self, state: CourseNavigationState):
        self._state = state
        self._by_id: Dict[str, Lesson] = {
            lesson.lesson_id: lesson for lesson in state.lessons_in_order
        }
        self._ordered_published = sorted(
            [l for l in state.lessons_in_order if l.status == LessonStatus.PUBLISHED],
            key=lambda l: l.order_index,
        )

    def get_next_lesson(
        self, current_lesson_id: str, progress: LearnerProgress
    ) -> NavigationResult:
        current = self._require_lesson(current_lesson_id)
        candidates = [l for l in self._ordered_published if l.order_index > current.order_index]
        if not candidates:
            return NavigationResult(current_lesson_id, None, "end_of_course")

        target = candidates[0]
        lock_state = self.is_lesson_locked(target.lesson_id, progress)
        if lock_state.locked:
            return NavigationResult(current_lesson_id, target.lesson_id, "target_locked")
        return NavigationResult(current_lesson_id, target.lesson_id, "ok")

    def get_previous_lesson(self, current_lesson_id: str) -> NavigationResult:
        current = self._require_lesson(current_lesson_id)
        candidates = [l for l in self._ordered_published if l.order_index < current.order_index]
        if not candidates:
            return NavigationResult(current_lesson_id, None, "start_of_course")

        return NavigationResult(current_lesson_id, candidates[-1].lesson_id, "ok")

    def trigger_completion(
        self,
        lesson_id: str,
        progress: LearnerProgress,
        *,
        viewed: bool = False,
        score: Optional[float] = None,
        manually_completed: bool = False,
    ) -> CompletionResult:
        lesson = self._require_lesson(lesson_id)

        if lesson.completion_policy == CompletionPolicy.VIEW:
            if not viewed:
                return CompletionResult(lesson_id, False, "view_not_recorded")

        elif lesson.completion_policy == CompletionPolicy.QUIZ_PASS:
            if score is None:
                return CompletionResult(lesson_id, False, "score_required")
            if score < self._state.minimum_passing_score:
                return CompletionResult(lesson_id, False, "score_below_threshold")

        elif lesson.completion_policy == CompletionPolicy.MANUAL:
            if not manually_completed:
                return CompletionResult(lesson_id, False, "manual_confirmation_required")

        progress.completed_lessons.add(lesson_id)
        if viewed:
            progress.lesson_views.add(lesson_id)
        if score is not None:
            progress.lesson_scores[lesson_id] = score

        return CompletionResult(lesson_id, True, "completed")

    def is_lesson_locked(self, lesson_id: str, progress: LearnerProgress) -> LockResult:
        lesson = self._require_lesson(lesson_id)
        if lesson.status != LessonStatus.PUBLISHED:
            return LockResult(lesson_id, True, "lesson_not_published")

        mode = self._state.locking_mode
        if mode == LockingMode.NONE:
            return LockResult(lesson_id, False, "unlocked")

        if mode == LockingMode.SEQUENTIAL:
            prior = [
                l.lesson_id
                for l in self._ordered_published
                if l.order_index < lesson.order_index
            ]
            missing = [lid for lid in prior if lid not in progress.completed_lessons]
            if missing:
                return LockResult(lesson_id, True, "prior_lessons_incomplete")
            return LockResult(lesson_id, False, "unlocked")

        if mode == LockingMode.PREREQUISITE:
            missing = [
                lid
                for lid in sorted(lesson.prerequisite_lesson_ids)
                if lid not in progress.completed_lessons
            ]
            if missing:
                return LockResult(lesson_id, True, "prerequisites_incomplete")
            return LockResult(lesson_id, False, "unlocked")

        return LockResult(lesson_id, True, "unknown_locking_mode")

    def _require_lesson(self, lesson_id: str) -> Lesson:
        lesson = self._by_id.get(lesson_id)
        if lesson is None:
            raise KeyError(f"Unknown lesson_id: {lesson_id}")
        return lesson
