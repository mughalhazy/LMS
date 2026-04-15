"""Storage contract and in-memory implementation for lesson-service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict

from .models import AuditRecord, Lesson, OutboxEvent


class LessonStore(ABC):
    @abstractmethod
    def create(self, lesson: Lesson) -> Lesson: ...

    @abstractmethod
    def get(self, tenant_id: str, lesson_id: str) -> Lesson | None: ...

    @abstractmethod
    def list(self, tenant_id: str, course_id: str | None = None) -> list[Lesson]: ...

    @abstractmethod
    def update(self, lesson: Lesson) -> Lesson: ...

    @abstractmethod
    def delete(self, tenant_id: str, lesson_id: str) -> None: ...

    @abstractmethod
    def append_audit(self, record: AuditRecord) -> None: ...

    @abstractmethod
    def append_event(self, event: OutboxEvent) -> None: ...


class InMemoryLessonStore(LessonStore):
    def __init__(self) -> None:
        self._lessons: dict[str, dict[str, Lesson]] = defaultdict(dict)
        self.audit_log: list[AuditRecord] = []
        self.events: list[OutboxEvent] = []

    def create(self, lesson: Lesson) -> Lesson:
        self._lessons[lesson.tenant_id][lesson.lesson_id] = lesson
        return lesson

    def get(self, tenant_id: str, lesson_id: str) -> Lesson | None:
        return self._lessons[tenant_id].get(lesson_id)

    def list(self, tenant_id: str, course_id: str | None = None) -> list[Lesson]:
        lessons = list(self._lessons[tenant_id].values())
        if course_id:
            lessons = [lesson for lesson in lessons if lesson.course_id == course_id]
        return sorted(lessons, key=lambda x: (x.course_id, x.order_index, x.created_at))

    def update(self, lesson: Lesson) -> Lesson:
        self._lessons[lesson.tenant_id][lesson.lesson_id] = lesson
        return lesson

    def delete(self, tenant_id: str, lesson_id: str) -> None:
        self._lessons[tenant_id].pop(lesson_id, None)

    def append_audit(self, record: AuditRecord) -> None:
        self.audit_log.append(record)

    def append_event(self, event: OutboxEvent) -> None:
        self.events.append(event)
