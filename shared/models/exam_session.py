from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

ExamSessionStatus = Literal["scheduled", "active", "submitted", "expired", "cancelled"]


@dataclass
class ExamSessionRecord:
    exam_session_id: str
    tenant_id: str
    exam_id: str
    student_id: str
    attempt_id: str
    status: ExamSessionStatus
    started_at: datetime | None
    expires_at: datetime | None
    submitted_at: datetime | None
    assigned_capacity_profile: str
    isolation_key: str
    metadata: dict[str, Any] = field(default_factory=dict)
