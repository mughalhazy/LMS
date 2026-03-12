import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unittest

from src.progress_service import ProgressTrackingService


class ProgressTrackingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ProgressTrackingService()

    def test_lesson_completion_rolls_up_to_course(self) -> None:
        self.service.track_lesson_completion(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-1",
            enrollment_id="enroll-1",
            completion_status="completed",
            score=80,
            time_spent_seconds=120,
            attempt_count=1,
        )

        self.service.track_lesson_completion(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-2",
            enrollment_id="enroll-1",
            completion_status="completed",
            score=100,
            time_spent_seconds=60,
            attempt_count=1,
        )

        progress = self.service.get_learner_progress("tenant-a", "learner-1")
        course = progress["courses"]["course-1"]
        self.assertEqual(course["completion_status"], "completed")
        self.assertEqual(course["final_score"], 90.0)
        self.assertEqual(course["total_time_spent_seconds"], 180)

    def test_learning_path_progress_updates_from_course_completion(self) -> None:
        self.service.assign_learning_path(
            tenant_id="tenant-a",
            learner_id="learner-1",
            learning_path_id="lp-1",
            assigned_course_ids=["course-1", "course-2"],
        )

        self.service.track_lesson_completion(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-1",
            enrollment_id="enroll-1",
            completion_status="completed",
            score=95,
            time_spent_seconds=90,
            attempt_count=1,
        )

        progress = self.service.get_learner_progress("tenant-a", "learner-1")
        lp = progress["learning_paths"]["lp-1"]

        self.assertEqual(lp["completed_course_ids"], ["course-1"])
        self.assertEqual(lp["progress_percentage"], 50.0)
        self.assertEqual(lp["current_course_id"], "course-2")
        self.assertEqual(lp["status"], "in_progress")

    def test_tenant_scope_isolation(self) -> None:
        self.service.track_lesson_completion(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-1",
            enrollment_id="enroll-a",
            completion_status="completed",
            score=100,
            time_spent_seconds=20,
            attempt_count=1,
        )

        tenant_b_progress = self.service.get_learner_progress("tenant-b", "learner-1")
        self.assertEqual(tenant_b_progress["courses"], {})
        self.assertEqual(tenant_b_progress["lessons"], {})
        self.assertEqual(tenant_b_progress["learning_paths"], {})


if __name__ == "__main__":
    unittest.main()
