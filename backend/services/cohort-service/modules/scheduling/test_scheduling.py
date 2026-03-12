from datetime import datetime, timedelta
import unittest

from service import CohortSchedulingModule, ScheduleValidationError
from models import SessionModality


class CohortSchedulingModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = CohortSchedulingModule(cohort_id="cohort-1")
        self.start = datetime(2026, 1, 1, 9, 0, 0)
        self.end = datetime(2026, 3, 1, 17, 0, 0)

    def test_sets_start_and_end_dates(self) -> None:
        schedule = self.module.set_schedule_window(self.start, self.end)
        self.assertEqual(schedule.schedule_window.start_date, self.start)
        self.assertEqual(schedule.schedule_window.end_date, self.end)

    def test_rejects_invalid_enrollment_window(self) -> None:
        self.module.set_schedule_window(self.start, self.end)
        with self.assertRaises(ScheduleValidationError):
            self.module.set_enrollment_window(self.end, self.start)

    def test_schedules_sessions_without_instructor_overlap(self) -> None:
        self.module.set_schedule_window(self.start, self.end)
        self.module.set_enrollment_window(self.start - timedelta(days=7), self.start)
        self.module.add_session(
            session_id="s1",
            title="Kickoff",
            start_at=self.start + timedelta(days=1),
            end_at=self.start + timedelta(days=1, hours=2),
            instructor_id="inst-1",
            modality=SessionModality.VIRTUAL,
        )

        with self.assertRaises(ScheduleValidationError):
            self.module.add_session(
                session_id="s2",
                title="Overlap",
                start_at=self.start + timedelta(days=1, hours=1),
                end_at=self.start + timedelta(days=1, hours=3),
                instructor_id="inst-1",
                modality=SessionModality.VIRTUAL,
            )


if __name__ == "__main__":
    unittest.main()
