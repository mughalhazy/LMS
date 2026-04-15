"""Persistence contracts for progress service."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import Protocol

from .models import (
    CompletionMetricDaily,
    CourseProgressSnapshot,
    LearningPathProgressSnapshot,
    ProgressAuditEntry,
    ProgressRecord,
)


class ProgressStore(Protocol):
    def get_progress(self, tenant_id: str, enrollment_id: str, lesson_id: str | None) -> ProgressRecord | None: ...
    def save_progress(self, record: ProgressRecord) -> None: ...
    def list_lesson_progress(self, tenant_id: str, learner_id: str, course_id: str) -> list[ProgressRecord]: ...
    def list_learner_progress(self, tenant_id: str, learner_id: str) -> list[ProgressRecord]: ...

    def save_course_snapshot(self, snapshot: CourseProgressSnapshot) -> None: ...
    def get_course_snapshot(self, tenant_id: str, learner_id: str, course_id: str) -> CourseProgressSnapshot | None: ...
    def list_course_snapshots(self, tenant_id: str, learner_id: str) -> list[CourseProgressSnapshot]: ...

    def save_path_snapshot(self, snapshot: LearningPathProgressSnapshot) -> None: ...
    def list_path_snapshots(self, tenant_id: str, learner_id: str) -> list[LearningPathProgressSnapshot]: ...

    def append_audit(self, entry: ProgressAuditEntry) -> None: ...
    def save_metric(self, metric: CompletionMetricDaily) -> None: ...


class IdempotencyStore(Protocol):
    def seen(self, tenant_id: str, key: str) -> bool: ...
    def remember(self, tenant_id: str, key: str) -> None: ...


class InMemoryProgressStore:
    def __init__(self) -> None:
        self._progress: dict[tuple[str, str, str | None], ProgressRecord] = {}
        self._course: dict[tuple[str, str, str], CourseProgressSnapshot] = {}
        self._paths: dict[tuple[str, str, str], LearningPathProgressSnapshot] = {}
        self._audit: list[ProgressAuditEntry] = []
        self._metrics: list[CompletionMetricDaily] = []

    def get_progress(self, tenant_id: str, enrollment_id: str, lesson_id: str | None) -> ProgressRecord | None:
        return self._progress.get((tenant_id, enrollment_id, lesson_id))

    def save_progress(self, record: ProgressRecord) -> None:
        self._progress[(record.tenant_id, record.enrollment_id, record.lesson_id)] = replace(record)

    def list_lesson_progress(self, tenant_id: str, learner_id: str, course_id: str) -> list[ProgressRecord]:
        return [
            replace(row)
            for row in self._progress.values()
            if row.tenant_id == tenant_id and row.learner_id == learner_id and row.course_id == course_id and row.lesson_id
        ]

    def list_learner_progress(self, tenant_id: str, learner_id: str) -> list[ProgressRecord]:
        return [replace(row) for row in self._progress.values() if row.tenant_id == tenant_id and row.learner_id == learner_id]

    def save_course_snapshot(self, snapshot: CourseProgressSnapshot) -> None:
        self._course[(snapshot.tenant_id, snapshot.learner_id, snapshot.course_id)] = replace(snapshot)

    def get_course_snapshot(self, tenant_id: str, learner_id: str, course_id: str) -> CourseProgressSnapshot | None:
        row = self._course.get((tenant_id, learner_id, course_id))
        return replace(row) if row else None

    def list_course_snapshots(self, tenant_id: str, learner_id: str) -> list[CourseProgressSnapshot]:
        return [replace(row) for row in self._course.values() if row.tenant_id == tenant_id and row.learner_id == learner_id]

    def save_path_snapshot(self, snapshot: LearningPathProgressSnapshot) -> None:
        self._paths[(snapshot.tenant_id, snapshot.learner_id, snapshot.learning_path_id)] = replace(snapshot)

    def list_path_snapshots(self, tenant_id: str, learner_id: str) -> list[LearningPathProgressSnapshot]:
        return [replace(row) for row in self._paths.values() if row.tenant_id == tenant_id and row.learner_id == learner_id]

    def append_audit(self, entry: ProgressAuditEntry) -> None:
        self._audit.append(replace(entry))

    def save_metric(self, metric: CompletionMetricDaily) -> None:
        self._metrics.append(replace(metric))


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._keys: dict[str, set[str]] = defaultdict(set)

    def seen(self, tenant_id: str, key: str) -> bool:
        return key in self._keys[tenant_id]

    def remember(self, tenant_id: str, key: str) -> None:
        self._keys[tenant_id].add(key)
