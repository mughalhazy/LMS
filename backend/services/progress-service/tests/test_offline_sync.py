import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.progress_service import ProgressTrackingService
from sync import OfflineProgressSyncEngine


class FlakyServerProgressService(ProgressTrackingService):
    def track_lesson_completion(self, **kwargs):
        if kwargs["lesson_id"] == "lesson-2":
            raise RuntimeError("temporary_outage")
        return super().track_lesson_completion(**kwargs)


class OfflineProgressSyncEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = OfflineProgressSyncEngine(Path(self.tmp.name) / "sync-state.json")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_offline_progress_syncs_to_server_without_data_loss(self) -> None:
        self.engine.track_lesson_completion_offline(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-1",
            enrollment_id="enroll-1",
            completion_status="completed",
            score=75,
            time_spent_seconds=120,
            attempt_count=1,
        )
        self.engine.track_lesson_completion_offline(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-2",
            enrollment_id="enroll-1",
            completion_status="completed",
            score=95,
            time_spent_seconds=80,
            attempt_count=1,
        )

        server = ProgressTrackingService()
        result = self.engine.sync_to_server(server)

        self.assertEqual(result["succeeded"], 2)
        self.assertEqual(result["pending"], 0)

        progress = server.get_learner_progress("tenant-a", "learner-1")
        self.assertEqual(progress["courses"]["course-1"]["completion_status"], "completed")
        self.assertEqual(progress["courses"]["course-1"]["total_time_spent_seconds"], 200)

    def test_sync_is_idempotent_for_retries(self) -> None:
        op = self.engine.track_lesson_completion_offline(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-1",
            enrollment_id="enroll-1",
            completion_status="completed",
            score=90,
            time_spent_seconds=60,
            attempt_count=1,
        )

        server = ProgressTrackingService()
        first = self.engine.sync_to_server(server)
        self.assertEqual(first["succeeded"], 1)

        self.engine._state["pending"].append(op.__dict__.copy())  # simulate duplicate retry payload
        self.engine._persist_state()

        second = self.engine.sync_to_server(server)
        self.assertEqual(second["succeeded"], 0)
        self.assertEqual(second["pending"], 0)
        progress = server.get_learner_progress("tenant-a", "learner-1")
        self.assertEqual(progress["courses"]["course-1"]["total_time_spent_seconds"], 60)

    def test_failed_sync_keeps_pending_items(self) -> None:
        self.engine.track_lesson_completion_offline(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-1",
            enrollment_id="enroll-1",
            completion_status="completed",
            score=70,
            time_spent_seconds=30,
            attempt_count=1,
        )
        self.engine.track_lesson_completion_offline(
            tenant_id="tenant-a",
            learner_id="learner-1",
            course_id="course-1",
            lesson_id="lesson-2",
            enrollment_id="enroll-1",
            completion_status="completed",
            score=88,
            time_spent_seconds=45,
            attempt_count=1,
        )

        flaky_server = FlakyServerProgressService()
        result = self.engine.sync_to_server(flaky_server)

        self.assertEqual(result["succeeded"], 1)
        self.assertEqual(result["pending"], 1)
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(self.engine.pending_operations()[0].lesson_id, "lesson-2")


if __name__ == "__main__":
    unittest.main()
