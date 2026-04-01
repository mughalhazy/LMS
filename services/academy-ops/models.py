from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import Enum
from typing import Any


class BatchStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Batch:
    tenant_id: str
    batch_id: str
    branch_id: str
    course_id: str
    teacher_ids: tuple[str, ...]
    student_ids: tuple[str, ...]
    timetable_id: str
    capacity: int
    status: BatchStatus
    start_date: date
    end_date: date
    metadata: dict[str, Any]
    academy_id: str = ""
    title: str = ""

    def with_updates(self, **changes: Any) -> "Batch":
        return replace(self, **changes)
