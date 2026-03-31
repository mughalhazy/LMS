"""Progress service business logic."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Protocol
from uuid import uuid4

from .models import (
    CompletionMetricDaily,
    CourseProgressSnapshot,
    LearningPathProgressSnapshot,
    ProgressAuditEntry,
    ProgressEvent,
    ProgressRecord,
    utc_now,
)
from .schemas import (
    CourseProgressResponse,
    LearnerProgressSummaryResponse,
    LearningPathAssignmentRequest,
    LearningPathAssignmentResponse,
    LessonCompleteResponse,
    LessonProgressCompleteRequest,
    LessonProgressUpsertRequest,
    ProgressRecordResponse,
)
from .store import IdempotencyStore, ProgressStore


class EnrollmentGateway(Protocol):
    def is_active(self, tenant_id: str, enrollment_id: str) -> bool: ...


class EventPublisher(Protocol):
    def publish(self, event: ProgressEvent) -> None: ...


class MetricsHook(Protocol):
    def increment(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None: ...


class AllowAllEnrollmentGateway:
    def is_active(self, tenant_id: str, enrollment_id: str) -> bool:
        return True


class InMemoryEventPublisher:
    def __init__(self) -> None:
        self.events: list[ProgressEvent] = []

    def publish(self, event: ProgressEvent) -> None:
        self.events.append(event)


class NoopMetricsHook:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def increment(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        self.counters[name] = self.counters.get(name, 0) + value


class EnrollmentInactiveError(ValueError):
    pass


class ProgressService:
    def __init__(
        self,
        store: ProgressStore,
        idempotency: IdempotencyStore,
        publisher: EventPublisher,
        metrics: MetricsHook,
        enrollment_gateway: EnrollmentGateway | None = None,
    ) -> None:
        self.store = store
        self.idempotency = idempotency
        self.publisher = publisher
        self.metrics = metrics
        self.enrollment_gateway = enrollment_gateway or AllowAllEnrollmentGateway()

    def upsert_lesson_progress(self, lesson_id: str, request: LessonProgressUpsertRequest, actor_id: str) -> ProgressRecordResponse:
        if not self.enrollment_gateway.is_active(request.tenant_id, request.enrollment_id):
            raise EnrollmentInactiveError("enrollment_not_active")
        self.metrics.increment("progress.write.attempt")
        if self.idempotency.seen(request.tenant_id, request.idempotency_key):
            self.metrics.increment("progress.write.idempotent_hit")
            existing = self.store.get_progress(request.tenant_id, request.enrollment_id, lesson_id)
            if existing:
                return self._record_response(existing)

        now = request.occurred_at
        existing = self.store.get_progress(request.tenant_id, request.enrollment_id, lesson_id)
        status = request.status
        completed_at = now if status in {"completed", "passed"} else None
        row = existing or ProgressRecord(
            tenant_id=request.tenant_id,
            enrollment_id=request.enrollment_id,
            learner_id=request.learner_id,
            course_id=request.course_id,
            lesson_id=lesson_id,
            progress_percentage=request.progress_percentage,
            status=status,
            last_activity_at=now,
        )
        row.progress_percentage = request.progress_percentage
        row.status = status
        row.last_activity_at = now
        row.completed_at = completed_at
        row.updated_at = utc_now()
        self.store.save_progress(row)
        self.idempotency.remember(request.tenant_id, request.idempotency_key)
        self._write_audit(request.tenant_id, actor_id, "lesson_progress_upserted", row.progress_id, request.idempotency_key, {"lesson_id": lesson_id})
        self._publish_progress_updated(row)
        snapshot = self._recompute_course_snapshot(request.tenant_id, request.learner_id, request.course_id, request.enrollment_id)
        self._update_metrics_daily(snapshot)
        self.metrics.increment("progress.write.success")
        return self._record_response(row)

    def complete_lesson(self, lesson_id: str, request: LessonProgressCompleteRequest, actor_id: str) -> LessonCompleteResponse:
        upsert = LessonProgressUpsertRequest(
            tenant_id=request.tenant_id,
            learner_id=request.learner_id,
            course_id=request.course_id,
            enrollment_id=request.enrollment_id,
            progress_percentage=100.0,
            status="completed",
            time_spent_seconds_delta=request.time_spent_seconds,
            attempt_count=request.attempt_count,
            occurred_at=request.completed_at,
            idempotency_key=request.idempotency_key,
        )
        lesson_progress = self.upsert_lesson_progress(lesson_id, upsert, actor_id)
        course = self.store.get_course_snapshot(request.tenant_id, request.learner_id, request.course_id)
        assert course is not None
        if request.score is not None:
            course.final_score = request.score
            self.store.save_course_snapshot(course)
        self.publisher.publish(
            ProgressEvent(
                event_id=str(uuid4()),
                event_type="LessonCompletionTracked",
                timestamp=utc_now(),
                tenant_id=request.tenant_id,
                correlation_id=str(uuid4()),
                payload={
                    "tenant_id": request.tenant_id,
                    "learner_id": request.learner_id,
                    "course_id": request.course_id,
                    "lesson_id": lesson_id,
                    "enrollment_id": request.enrollment_id,
                    "completion_status": "completed",
                    "score": request.score,
                    "time_spent_seconds": request.time_spent_seconds,
                    "completed_at": request.completed_at.isoformat(),
                    "attempt_count": request.attempt_count,
                },
                metadata={"producer": "progress-service"},
            )
        )
        return LessonCompleteResponse(lesson_progress=lesson_progress, course_progress=self._course_response(course))

    def assign_learning_path(self, learning_path_id: str, request: LearningPathAssignmentRequest, actor_id: str) -> LearningPathAssignmentResponse:
        if self.idempotency.seen(request.tenant_id, request.idempotency_key):
            existing = [
                row
                for row in self.store.list_path_snapshots(request.tenant_id, request.learner_id)
                if row.learning_path_id == learning_path_id
            ]
            if existing:
                row = existing[0]
                return LearningPathAssignmentResponse(
                    learning_path_id=learning_path_id,
                    status=row.status,
                    progress_percentage=row.progress_percentage,
                    current_course_id=row.current_course_id,
                )
        row = LearningPathProgressSnapshot(
            tenant_id=request.tenant_id,
            learner_id=request.learner_id,
            learning_path_id=learning_path_id,
            assigned_course_ids=request.assigned_course_ids,
            completed_course_ids=[],
            progress_percentage=0.0 if request.assigned_course_ids else 100.0,
            current_course_id=request.assigned_course_ids[0] if request.assigned_course_ids else None,
            status="in_progress" if request.assigned_course_ids else "completed",
            expected_completion_date=request.expected_completion_date,
            last_activity_at=utc_now(),
        )
        self.store.save_path_snapshot(row)
        self.idempotency.remember(request.tenant_id, request.idempotency_key)
        self._write_audit(request.tenant_id, actor_id, "learning_path_assigned", None, request.idempotency_key, asdict(row))
        self.publisher.publish(ProgressEvent(event_id=str(uuid4()), event_type="LearningPathProgressUpdated", timestamp=utc_now(), tenant_id=request.tenant_id, correlation_id=str(uuid4()), payload=asdict(row), metadata={"producer": "progress-service"}))
        return LearningPathAssignmentResponse(
            learning_path_id=learning_path_id,
            status=row.status,
            progress_percentage=row.progress_percentage,
            current_course_id=row.current_course_id,
        )

    def get_learner_summary(self, tenant_id: str, learner_id: str) -> LearnerProgressSummaryResponse:
        lessons = [self._record_response(r) for r in self.store.list_learner_progress(tenant_id, learner_id) if r.lesson_id]
        courses = [self._course_response(row) for row in self.store.list_course_snapshots(tenant_id, learner_id)]
        paths = [self._path_response(row) for row in self.store.list_path_snapshots(tenant_id, learner_id)]
        return LearnerProgressSummaryResponse(tenant_id=tenant_id, learner_id=learner_id, courses=courses, lessons=lessons, learning_paths=paths)

    def get_course_progress(self, tenant_id: str, learner_id: str, course_id: str) -> CourseProgressResponse | None:
        row = self.store.get_course_snapshot(tenant_id, learner_id, course_id)
        if not row:
            return None
        return self._course_response(row)

    def _recompute_course_snapshot(self, tenant_id: str, learner_id: str, course_id: str, enrollment_id: str) -> CourseProgressSnapshot:
        lesson_rows = self.store.list_lesson_progress(tenant_id, learner_id, course_id)
        total = len(lesson_rows)
        completed = len([r for r in lesson_rows if r.status in {"completed", "passed"}])
        progress = round((completed / total) * 100, 2) if total else 0.0
        status = "completed" if total and completed == total else "in_progress"
        existing = self.store.get_course_snapshot(tenant_id, learner_id, course_id)
        started_at = existing.started_at if existing else utc_now()
        completed_at = utc_now() if status == "completed" else None
        snapshot = CourseProgressSnapshot(
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            enrollment_id=enrollment_id,
            completed_lessons=completed,
            total_lessons=total,
            progress_percentage=progress,
            completion_status=status,
            started_at=started_at,
            completed_at=completed_at,
            last_activity_at=utc_now(),
            final_score=existing.final_score if existing else None,
            certificate_id=existing.certificate_id if existing else None,
            total_time_spent_seconds=(existing.total_time_spent_seconds if existing else 0),
        )
        self.store.save_course_snapshot(snapshot)
        self._refresh_learning_paths_for_course(tenant_id, learner_id, course_id)
        if status == "completed":
            self.publisher.publish(ProgressEvent(event_id=str(uuid4()), event_type="CourseCompletionTracked", timestamp=utc_now(), tenant_id=tenant_id, correlation_id=str(uuid4()), payload=asdict(snapshot), metadata={"producer": "progress-service"}))
            self.publisher.publish(
                ProgressEvent(
                    event_id=str(uuid4()),
                    event_type="progress.completed",
                    timestamp=utc_now(),
                    tenant_id=tenant_id,
                    correlation_id=str(uuid4()),
                    payload={
                        "progress_id": f"course:{enrollment_id}:{course_id}",
                        "enrollment_id": enrollment_id,
                        "user_id": learner_id,
                        "course_id": course_id,
                        "completed_at": snapshot.completed_at.isoformat() if snapshot.completed_at else None,
                    },
                    metadata={"producer": "progress-service"},
                )
            )
        return snapshot

    def _refresh_learning_paths_for_course(self, tenant_id: str, learner_id: str, course_id: str) -> None:
        courses = self.store.list_course_snapshots(tenant_id, learner_id)
        completed_ids = {c.course_id for c in courses if c.completion_status == "completed"}
        for path in self.store.list_path_snapshots(tenant_id, learner_id):
            if course_id not in path.assigned_course_ids:
                continue
            path.completed_course_ids = [cid for cid in path.assigned_course_ids if cid in completed_ids]
            total = len(path.assigned_course_ids)
            path.progress_percentage = round((len(path.completed_course_ids) / total) * 100, 2) if total else 100.0
            remaining = [cid for cid in path.assigned_course_ids if cid not in completed_ids]
            path.current_course_id = remaining[0] if remaining else None
            path.status = "completed" if not remaining else "in_progress"
            path.last_activity_at = utc_now()
            self.store.save_path_snapshot(path)
            self.publisher.publish(ProgressEvent(event_id=str(uuid4()), event_type="LearningPathProgressUpdated", timestamp=utc_now(), tenant_id=tenant_id, correlation_id=str(uuid4()), payload=asdict(path), metadata={"producer": "progress-service"}))

    def _publish_progress_updated(self, row: ProgressRecord) -> None:
        payload = {
            "progress_id": row.progress_id,
            "enrollment_id": row.enrollment_id,
            "learner_id": row.learner_id,
            "user_id": row.learner_id,
            "course_id": row.course_id,
            "lesson_id": row.lesson_id,
            "percent_complete": row.progress_percentage,
            "status": row.status,
            "last_activity_at": row.last_activity_at.isoformat(),
        }
        self.publisher.publish(ProgressEvent(event_id=str(uuid4()), event_type="progress.updated", timestamp=utc_now(), tenant_id=row.tenant_id, correlation_id=str(uuid4()), payload=payload, metadata={"producer": "progress-service"}))

    def _update_metrics_daily(self, snapshot: CourseProgressSnapshot) -> None:
        started_count = 1 if snapshot.total_lessons > 0 else 0
        completed_count = 1 if snapshot.completion_status == "completed" else 0
        metric = CompletionMetricDaily(
            tenant_id=snapshot.tenant_id,
            metric_date=date.today().isoformat(),
            course_id=snapshot.course_id,
            learning_path_id=None,
            started_count=started_count,
            completed_count=completed_count,
            completion_rate=100.0 if started_count and completed_count else 0.0,
            avg_time_to_complete_seconds=float(snapshot.total_time_spent_seconds),
            avg_progress_percentage=snapshot.progress_percentage,
        )
        self.store.save_metric(metric)

    def _write_audit(self, tenant_id: str, actor_id: str, action: str, progress_id: str | None, idempotency_key: str | None, details: dict[str, object]) -> None:
        self.store.append_audit(
            ProgressAuditEntry(
                tenant_id=tenant_id,
                actor_id=actor_id,
                action=action,
                progress_id=progress_id,
                idempotency_key=idempotency_key,
                occurred_at=utc_now(),
                details=details,
            )
        )

    @staticmethod
    def _record_response(row: ProgressRecord) -> ProgressRecordResponse:
        return ProgressRecordResponse(
            progress_id=row.progress_id,
            tenant_id=row.tenant_id,
            learner_id=row.learner_id,
            user_id=row.learner_id,
            course_id=row.course_id,
            lesson_id=row.lesson_id,
            enrollment_id=row.enrollment_id,
            progress_percentage=row.progress_percentage,
            percent_complete=row.progress_percentage,
            status=row.status,
            last_activity_at=row.last_activity_at,
            completed_at=row.completed_at,
        )

    @staticmethod
    def _course_response(row: CourseProgressSnapshot) -> CourseProgressResponse:
        return CourseProgressResponse(
            tenant_id=row.tenant_id,
            learner_id=row.learner_id,
            course_id=row.course_id,
            enrollment_id=row.enrollment_id,
            completion_status=row.completion_status,
            progress_percentage=row.progress_percentage,
            final_score=row.final_score,
            started_at=row.started_at,
            completed_at=row.completed_at,
            total_time_spent_seconds=row.total_time_spent_seconds,
            certificate_id=row.certificate_id,
        )

    @staticmethod
    def _path_response(row: LearningPathProgressSnapshot):
        from .schemas import LearningPathProgressResponse

        return LearningPathProgressResponse(
            tenant_id=row.tenant_id,
            learner_id=row.learner_id,
            learning_path_id=row.learning_path_id,
            assigned_course_ids=row.assigned_course_ids,
            completed_course_ids=row.completed_course_ids,
            progress_percentage=row.progress_percentage,
            current_course_id=row.current_course_id,
            status=row.status,
            expected_completion_date=row.expected_completion_date,
            last_activity_at=row.last_activity_at,
        )
