"""Lesson domain service logic."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from uuid import uuid4

from .models import AuditRecord, LifecycleAction, Lesson, LessonStatus, OutboxEvent
from .store import LessonStore


class NotFoundError(Exception):
    """Domain-specific exception."""


class ValidationError(Exception):
    """Domain-specific exception."""


class LessonService:
    def __init__(self, store: LessonStore) -> None:
        self.store = store

    def create_lesson(self, tenant_id: str, actor_id: str, payload: dict[str, Any]) -> Lesson:
        lesson = Lesson(tenant_id=tenant_id, created_by=actor_id, **payload)
        self.store.create(lesson)
        self._record(tenant_id, actor_id, lesson.lesson_id, LifecycleAction.CREATE, {"course_id": lesson.course_id})
        self._emit("lms.lesson.created.v1", tenant_id, "lesson_created", lesson)
        return lesson

    def get_lesson(self, tenant_id: str, lesson_id: str) -> Lesson:
        lesson = self.store.get(tenant_id, lesson_id)
        if not lesson:
            raise NotFoundError("lesson_not_found")
        return lesson

    def list_lessons(self, tenant_id: str, course_id: str | None) -> list[Lesson]:
        return self.store.list(tenant_id, course_id)

    def update_lesson(self, tenant_id: str, actor_id: str, lesson_id: str, payload: dict[str, Any]) -> Lesson:
        lesson = self.get_lesson(tenant_id, lesson_id)
        if lesson.status == LessonStatus.ARCHIVED:
            raise ValidationError("archived_lessons_are_read_only")
        for key, value in payload.items():
            setattr(lesson, key, value)
        lesson.version += 1
        lesson.updated_at = datetime.now(timezone.utc)
        self.store.update(lesson)
        self._record(tenant_id, actor_id, lesson.lesson_id, LifecycleAction.UPDATE, {"updated_fields": list(payload.keys())})
        self._emit("lms.lesson.updated.v1", tenant_id, "lesson_updated", lesson)
        return lesson

    def publish_lesson(self, tenant_id: str, actor_id: str, lesson_id: str) -> Lesson:
        lesson = self.get_lesson(tenant_id, lesson_id)
        if lesson.status == LessonStatus.ARCHIVED:
            raise ValidationError("cannot_publish_archived_lesson")
        lesson.status = LessonStatus.PUBLISHED
        lesson.published_version = lesson.version
        lesson.published_at = datetime.now(timezone.utc)
        lesson.updated_at = lesson.published_at
        self.store.update(lesson)
        self._record(tenant_id, actor_id, lesson.lesson_id, LifecycleAction.PUBLISH, {"published_version": lesson.published_version})
        self._emit("lms.lesson.published.v1", tenant_id, "lesson_published", lesson)
        return lesson

    def unpublish_lesson(self, tenant_id: str, actor_id: str, lesson_id: str) -> Lesson:
        lesson = self.get_lesson(tenant_id, lesson_id)
        if lesson.status != LessonStatus.PUBLISHED:
            raise ValidationError("lesson_not_published")
        lesson.status = LessonStatus.DRAFT
        lesson.updated_at = datetime.now(timezone.utc)
        self.store.update(lesson)
        self._record(tenant_id, actor_id, lesson.lesson_id, LifecycleAction.UNPUBLISH, {})
        self._emit("lms.lesson.unpublished.v1", tenant_id, "lesson_unpublished", lesson)
        return lesson

    def archive_lesson(self, tenant_id: str, actor_id: str, lesson_id: str) -> Lesson:
        lesson = self.get_lesson(tenant_id, lesson_id)
        lesson.status = LessonStatus.ARCHIVED
        lesson.archived_at = datetime.now(timezone.utc)
        lesson.updated_at = lesson.archived_at
        self.store.update(lesson)
        self._record(tenant_id, actor_id, lesson.lesson_id, LifecycleAction.ARCHIVE, {})
        self._emit("lms.lesson.archived.v1", tenant_id, "lesson_archived", lesson)
        return lesson

    def set_delivery_state(self, tenant_id: str, actor_id: str, lesson_id: str, state: dict[str, Any]) -> Lesson:
        lesson = self.get_lesson(tenant_id, lesson_id)
        lesson.delivery_state = state
        lesson.version += 1
        lesson.updated_at = datetime.now(timezone.utc)
        self.store.update(lesson)
        self._record(tenant_id, actor_id, lesson.lesson_id, LifecycleAction.DELIVERY_STATE, {"keys": sorted(state.keys())})
        self._emit("lms.lesson.delivery_state_changed.v1", tenant_id, "lesson_delivery_state_changed", lesson)
        return lesson

    def trigger_progression_hook(
        self,
        tenant_id: str,
        actor_id: str,
        lesson_id: str,
        hook_type: str,
        payload: dict[str, Any],
    ) -> None:
        lesson = self.get_lesson(tenant_id, lesson_id)
        detail = {"hook_type": hook_type, "payload": payload, "course_id": lesson.course_id}
        self._record(tenant_id, actor_id, lesson.lesson_id, LifecycleAction.PROGRESSION_HOOK, detail)
        self.store.append_event(
            OutboxEvent(
                event_id=str(uuid4()),
                event_type="lesson_progression_hook_triggered",
                timestamp=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                correlation_id=str(uuid4()),
                payload={"lesson_id": lesson_id, "hook_type": hook_type, "payload": payload, "course_id": lesson.course_id},
                metadata={"topic": "lms.lesson.progression_hook.v1", "producer": "lesson-service"},
            )
        )

    def delete_lesson(self, tenant_id: str, actor_id: str, lesson_id: str) -> None:
        _ = self.get_lesson(tenant_id, lesson_id)
        self.store.delete(tenant_id, lesson_id)
        self._record(tenant_id, actor_id, lesson_id, LifecycleAction.DELETE, {})
        self.store.append_event(
            OutboxEvent(
                event_id=str(uuid4()),
                event_type="lesson_deleted",
                timestamp=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                correlation_id=str(uuid4()),
                payload={"lesson_id": lesson_id},
                metadata={"topic": "lms.lesson.deleted.v1", "producer": "lesson-service"},
            )
        )

    def _record(self, tenant_id: str, actor_id: str, lesson_id: str, action: LifecycleAction, detail: dict[str, Any]) -> None:
        self.store.append_audit(
            AuditRecord(tenant_id=tenant_id, actor_id=actor_id, lesson_id=lesson_id, action=action, detail=detail)
        )

    def _emit(self, topic: str, tenant_id: str, event_type: str, lesson: Lesson) -> None:
        payload = asdict(lesson)
        payload["status"] = lesson.status.value
        self.store.append_event(OutboxEvent(event_id=str(uuid4()), event_type=event_type, timestamp=datetime.now(timezone.utc), tenant_id=tenant_id, correlation_id=str(uuid4()), payload=payload, metadata={"topic": topic, "producer": "lesson-service"}))
