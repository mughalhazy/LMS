from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SessionModality(str, Enum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class ScheduleWindow:
    start_date: datetime
    end_date: datetime


@dataclass(frozen=True)
class EnrollmentWindow:
    opens_at: datetime
    closes_at: datetime


@dataclass(frozen=True)
class Session:
    session_id: str
    title: str
    start_at: datetime
    end_at: datetime
    instructor_id: str
    modality: SessionModality


@dataclass
class CohortSchedule:
    cohort_id: str
    schedule_window: ScheduleWindow | None = None
    enrollment_window: EnrollmentWindow | None = None
    sessions: list[Session] = field(default_factory=list)
    schedule_version: int = 1
