from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.schemas import EventIngestRequest
from app.service import EventIngestionService
from app.store import InMemoryEventStore


def make_service() -> EventIngestionService:
    return EventIngestionService(InMemoryEventStore())


def test_ingests_valid_event_and_persists_validated_stream() -> None:
    service = make_service()

    status, payload = service.ingest_event(
        EventIngestRequest(
            tenant_id="tenant-acme",
            event_type="LearningActivityCaptured",
            actor_id="user-100",
            occurred_at="2026-01-11T10:00:00Z",
            payload={
                "activity_id": "activity-1",
                "learner_id": "user-100",
                "course_id": "course-1",
                "module_id": "module-1",
                "activity_type": "lesson_view",
                "activity_status": "completed",
                "device_type": "desktop",
                "platform": "web",
                "event_timestamp": "2026-01-11T10:00:00Z",
                "session_id": "sess-1",
                "duration_seconds": 320,
            },
        )
    )

    assert status == 202
    assert payload["status"] == "accepted"

    _, stream = service.get_tenant_stream("tenant-acme")
    assert len(stream["raw"]) == 1
    assert len(stream["validated"]) == 1
    assert len(stream["rejected"]) == 0


def test_rejects_event_with_missing_required_field() -> None:
    service = make_service()

    status, payload = service.ingest_event(
        EventIngestRequest(
            tenant_id="tenant-acme",
            event_type="LearningActivityCaptured",
            actor_id="user-100",
            occurred_at="2026-01-11T10:00:00Z",
            payload={
                "activity_id": "activity-1",
                "learner_id": "user-100",
            },
        )
    )

    assert status == 422
    assert payload["status"] == "rejected"
    assert payload["event"]["rejection_reason_code"] == "missing_required_field"


def test_batch_ingestion_supports_partial_success_and_tenant_scope() -> None:
    service = make_service()
    valid_event = EventIngestRequest(
        tenant_id="tenant-acme",
        event_type="CourseCompletionRecorded",
        actor_id="user-100",
        occurred_at="2026-01-11T12:00:00Z",
        payload={
            "completion_id": "completion-1",
            "learner_id": "user-100",
            "course_id": "course-9",
            "completion_timestamp": "2026-01-11T12:00:00Z",
            "total_time_spent_seconds": 5400,
            "completion_source": "self_paced",
            "certificate_issued_flag": True,
        },
    )
    invalid_event = EventIngestRequest(
        tenant_id="tenant-acme",
        event_type="CourseCompletionRecorded",
        actor_id="user-101",
        occurred_at="2026-01-11T12:10:00Z",
        payload={"completion_id": "completion-2"},
    )

    status, payload = service.ingest_batch("tenant-acme", [valid_event, invalid_event])
    assert status == 207
    assert payload["accepted"] == 1
    assert payload["rejected"] == 1

    cross_tenant = EventIngestRequest(
        tenant_id="tenant-other",
        event_type="CourseCompletionRecorded",
        actor_id="user-300",
        occurred_at="2026-01-11T12:10:00Z",
        payload={
            "completion_id": "completion-3",
            "learner_id": "user-300",
            "course_id": "course-3",
            "completion_timestamp": "2026-01-11T12:10:00Z",
            "total_time_spent_seconds": 100,
            "completion_source": "assigned",
            "certificate_issued_flag": False,
        },
    )
    status, payload = service.ingest_batch("tenant-acme", [cross_tenant])
    assert status == 400
    assert payload["error"] == "tenant_scope_violation"
