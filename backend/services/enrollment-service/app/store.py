"""Storage contract and in-memory implementation for enrollment records."""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from .models import AuditLogEntry, Enrollment, EnrollmentStatus


class EnrollmentStore(Protocol):
    def create(self, enrollment: Enrollment) -> Enrollment: ...

    def get(self, tenant_id: str, enrollment_id: str) -> Enrollment | None: ...

    def list(
        self,
        tenant_id: str,
        learner_id: str | None = None,
        course_id: str | None = None,
        status: str | None = None,
    ) -> list[Enrollment]: ...

    def update(self, enrollment: Enrollment) -> Enrollment: ...

    def active_for_learner_course(self, tenant_id: str, learner_id: str, course_id: str) -> Enrollment | None: ...


class AuditLogStore(Protocol):
    def append(self, entry: AuditLogEntry) -> None: ...

    def list(self, tenant_id: str) -> list[AuditLogEntry]: ...


class InMemoryEnrollmentStore:
    def __init__(self) -> None:
        self._by_tenant: dict[str, dict[str, Enrollment]] = defaultdict(dict)

    def create(self, enrollment: Enrollment) -> Enrollment:
        self._by_tenant[enrollment.tenant_id][enrollment.id] = enrollment
        return enrollment

    def get(self, tenant_id: str, enrollment_id: str) -> Enrollment | None:
        return self._by_tenant[tenant_id].get(enrollment_id)

    def list(
        self,
        tenant_id: str,
        learner_id: str | None = None,
        course_id: str | None = None,
        status: str | None = None,
    ) -> list[Enrollment]:
        rows = list(self._by_tenant[tenant_id].values())
        if learner_id:
            rows = [r for r in rows if r.learner_id == learner_id]
        if course_id:
            rows = [r for r in rows if r.course_id == course_id]
        if status:
            rows = [r for r in rows if r.status.value == status]
        return rows

    def update(self, enrollment: Enrollment) -> Enrollment:
        self._by_tenant[enrollment.tenant_id][enrollment.id] = enrollment
        return enrollment

    def active_for_learner_course(self, tenant_id: str, learner_id: str, course_id: str) -> Enrollment | None:
        for enrollment in self._by_tenant[tenant_id].values():
            if enrollment.learner_id == learner_id and enrollment.course_id == course_id and enrollment.status in {EnrollmentStatus.ASSIGNED, EnrollmentStatus.ACTIVE}:
                return enrollment
        return None


class InMemoryAuditLogStore:
    def __init__(self) -> None:
        self._entries: dict[str, list[AuditLogEntry]] = defaultdict(list)

    def append(self, entry: AuditLogEntry) -> None:
        self._entries[entry.tenant_id].append(entry)

    def list(self, tenant_id: str) -> list[AuditLogEntry]:
        return list(self._entries[tenant_id])
