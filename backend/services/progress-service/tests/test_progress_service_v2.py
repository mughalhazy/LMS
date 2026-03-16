import unittest
from datetime import datetime, timezone

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.schemas import LearningPathAssignmentRequest, LessonProgressCompleteRequest, LessonProgressUpsertRequest
from app.service import InMemoryEventPublisher, NoopMetricsHook, ProgressService
from app.store import InMemoryIdempotencyStore, InMemoryProgressStore


class ProgressServiceV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.publisher = InMemoryEventPublisher()
        self.metrics = NoopMetricsHook()
        self.service = ProgressService(
            store=InMemoryProgressStore(),
            idempotency=InMemoryIdempotencyStore(),
            publisher=self.publisher,
            metrics=self.metrics,
        )

    def test_upsert_tracks_canonical_alias_and_idempotency(self) -> None:
        req = LessonProgressUpsertRequest(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            enrollment_id="enroll-1",
            progress_percentage=40.0,
            status="in_progress",
            time_spent_seconds_delta=30,
            attempt_count=1,
            occurred_at=datetime.now(timezone.utc),
            idempotency_key="evt-1",
        )
        first = self.service.upsert_lesson_progress("lesson-1", req, actor_id="tester")
        second = self.service.upsert_lesson_progress("lesson-1", req, actor_id="tester")
        self.assertEqual(first.progress_id, second.progress_id)
        self.assertEqual(first.user_id, first.learner_id)
        self.assertEqual(self.metrics.counters["progress.write.idempotent_hit"], 1)

    def test_lesson_completion_rolls_course_and_emits_completion_event(self) -> None:
        for lesson in ["lesson-1", "lesson-2"]:
            req = LessonProgressCompleteRequest(
                tenant_id="tenant-a",
                learner_id="learner-1",
                course_id="course-1",
                enrollment_id="enroll-1",
                score=95,
                time_spent_seconds=120,
                attempt_count=1,
                completed_at=datetime.now(timezone.utc),
                idempotency_key=f"evt-{lesson}",
            )
            result = self.service.complete_lesson(lesson, req, actor_id="tester")

        self.assertEqual(result.course_progress.completion_status, "completed")
        event_names = [event.name for event in self.publisher.events]
        self.assertIn("CourseCompletionTracked", event_names)
        self.assertIn("progress.completed", event_names)

    def test_learning_path_updates_after_course_completion(self) -> None:
        assign = LearningPathAssignmentRequest(
            tenant_id="tenant-a",
            learner_id="learner-1",
            assigned_course_ids=["course-1", "course-2"],
            expected_completion_date="2026-02-01",
            idempotency_key="path-1",
        )
        self.service.assign_learning_path("lp-1", assign, actor_id="tester")
        complete = LessonProgressCompleteRequest(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            enrollment_id="enroll-1",
            score=88,
            time_spent_seconds=80,
            attempt_count=1,
            completed_at=datetime.now(timezone.utc),
            idempotency_key="evt-l1",
        )
        self.service.complete_lesson("lesson-1", complete, actor_id="tester")
        summary = self.service.get_learner_summary("tenant-a", "learner-1")
        self.assertEqual(summary.learning_paths[0].progress_percentage, 50.0)
        self.assertEqual(summary.learning_paths[0].current_course_id, "course-2")


if __name__ == "__main__":
    unittest.main()
