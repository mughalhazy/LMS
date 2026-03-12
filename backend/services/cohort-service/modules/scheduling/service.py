from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from models import CohortSchedule, EnrollmentWindow, ScheduleWindow, Session, SessionModality


class ScheduleValidationError(ValueError):
    """Raised when scheduling inputs violate cohort scheduling constraints."""


class CohortSchedulingModule:
    """Domain module implementing cohort schedule boundaries and session planning."""

    def __init__(self, cohort_id: str) -> None:
        self._schedule = CohortSchedule(cohort_id=cohort_id)

    @property
    def schedule(self) -> CohortSchedule:
        return self._schedule

    def set_schedule_window(self, start_date: datetime, end_date: datetime) -> CohortSchedule:
        if end_date <= start_date:
            raise ScheduleValidationError("end_date must be after start_date")

        self._schedule.schedule_window = ScheduleWindow(start_date=start_date, end_date=end_date)
        self._schedule.schedule_version += 1
        return self._schedule

    def set_enrollment_window(self, opens_at: datetime, closes_at: datetime) -> CohortSchedule:
        if closes_at <= opens_at:
            raise ScheduleValidationError("enrollment close must be after enrollment open")

        if self._schedule.schedule_window is not None:
            if opens_at > self._schedule.schedule_window.end_date:
                raise ScheduleValidationError("enrollment cannot open after the cohort end_date")
            if closes_at > self._schedule.schedule_window.end_date:
                raise ScheduleValidationError("enrollment cannot close after the cohort end_date")

        self._schedule.enrollment_window = EnrollmentWindow(opens_at=opens_at, closes_at=closes_at)
        self._schedule.schedule_version += 1
        return self._schedule

    def add_session(
        self,
        session_id: str,
        title: str,
        start_at: datetime,
        end_at: datetime,
        instructor_id: str,
        modality: SessionModality,
    ) -> CohortSchedule:
        if end_at <= start_at:
            raise ScheduleValidationError("session end_at must be after start_at")

        schedule_window = self._schedule.schedule_window
        if schedule_window is not None:
            if start_at < schedule_window.start_date or end_at > schedule_window.end_date:
                raise ScheduleValidationError("session must fit inside the cohort start/end schedule")

        for existing in self._schedule.sessions:
            if existing.session_id == session_id:
                raise ScheduleValidationError(f"session_id '{session_id}' already exists")

            overlaps = start_at < existing.end_at and end_at > existing.start_at
            if overlaps and existing.instructor_id == instructor_id:
                raise ScheduleValidationError(
                    f"instructor '{instructor_id}' has overlapping sessions: {existing.session_id}"
                )

        self._schedule.sessions.append(
            Session(
                session_id=session_id,
                title=title,
                start_at=start_at,
                end_at=end_at,
                instructor_id=instructor_id,
                modality=modality,
            )
        )
        self._schedule.sessions.sort(key=lambda item: item.start_at)
        self._schedule.schedule_version += 1
        return self._schedule

    def publish_calendar(self) -> dict:
        if self._schedule.schedule_window is None:
            raise ScheduleValidationError("schedule window must be set before publishing")

        if self._schedule.enrollment_window is None:
            raise ScheduleValidationError("enrollment window must be set before publishing")

        return {
            "cohort_id": self._schedule.cohort_id,
            "schedule_version": self._schedule.schedule_version,
            "schedule_window": asdict(self._schedule.schedule_window),
            "enrollment_window": asdict(self._schedule.enrollment_window),
            "sessions": [asdict(session) for session in self._schedule.sessions],
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
