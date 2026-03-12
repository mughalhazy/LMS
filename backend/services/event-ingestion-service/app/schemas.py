from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


SUPPORTED_EVENT_FIELDS: Dict[str, List[str]] = {
    "LearningActivityCaptured": [
        "activity_id",
        "learner_id",
        "course_id",
        "module_id",
        "activity_type",
        "activity_status",
        "device_type",
        "platform",
        "event_timestamp",
        "session_id",
        "duration_seconds",
    ],
    "ContentInteractionRecorded": [
        "interaction_id",
        "learner_id",
        "content_id",
        "content_type",
        "interaction_action",
        "percent_consumed",
        "playback_position_seconds",
        "event_timestamp",
    ],
    "AssessmentAttemptSubmitted": [
        "attempt_id",
        "learner_id",
        "assessment_id",
        "course_id",
        "attempt_number",
        "score",
        "max_score",
        "passed_flag",
        "submitted_at",
        "time_spent_seconds",
    ],
    "ProgressSnapshotUpdated": [
        "snapshot_id",
        "learner_id",
        "course_id",
        "learning_path_id",
        "progress_percent",
        "completed_modules",
        "total_modules",
        "overdue_flag",
        "snapshot_timestamp",
    ],
    "CourseCompletionRecorded": [
        "completion_id",
        "learner_id",
        "course_id",
        "completion_timestamp",
        "total_time_spent_seconds",
        "completion_source",
        "certificate_issued_flag",
    ],
}


@dataclass(slots=True)
class EventIngestRequest:
    tenant_id: str
    event_type: str
    actor_id: str
    occurred_at: str
    payload: Dict[str, Any]
    schema_version: str = "v1"
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex}")
    source_system: str = "lms"
    session_id: Optional[str] = None
    ingestion_channel: str = "api"


@dataclass(slots=True)
class BatchIngestRequest:
    tenant_id: str
    events: List[EventIngestRequest]


class SchemaValidationError(ValueError):
    def __init__(self, reason_code: str, detail: str, failed_field: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        self.failed_field = failed_field
        super().__init__(detail)


def ensure_iso8601(timestamp_value: str, field_name: str) -> None:
    try:
        datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise SchemaValidationError(
            "invalid_timestamp",
            f"{field_name} must be an ISO-8601 timestamp",
            field_name,
        ) from exc


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
