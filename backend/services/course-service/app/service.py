from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from .schemas import (
    CourseResponse,
    CourseStatus,
    CreateCourseRequest,
    CreateCourseVersionRequest,
    PublishCourseRequest,
    UpdateCourseRequest,
    VersionResponse,
)


@dataclass
class CourseVersion:
    version: int
    status: CourseStatus
    created_at: datetime
    created_by: str
    change_summary: str
    content_refs: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class CourseRecord:
    course_id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    status: CourseStatus
    active_version: int
    published_version: int | None = None
    published_at: datetime | None = None
    effective_from: datetime | None = None
    versions: dict[int, CourseVersion] = field(default_factory=dict)


class CourseService:
    def __init__(self) -> None:
        self._courses: dict[str, CourseRecord] = {}
        self._course_ids_by_tenant: dict[str, set[str]] = {}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _dump_model(model: Any, **kwargs: Any) -> dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump(**kwargs)
        return model.dict(**kwargs)

    def create_course(self, request: CreateCourseRequest) -> CourseResponse:
        now = self._now()
        course_id = str(uuid4())
        payload = self._dump_model(request, exclude={"tenant_id", "created_by"})
        version = CourseVersion(
            version=1,
            status=CourseStatus.DRAFT,
            created_at=now,
            created_by=request.created_by,
            change_summary="Initial course draft",
            payload=payload,
        )
        record = CourseRecord(
            course_id=course_id,
            tenant_id=request.tenant_id,
            created_at=now,
            updated_at=now,
            created_by=request.created_by,
            status=CourseStatus.DRAFT,
            active_version=1,
            versions={1: version},
        )
        self._courses[course_id] = record
        self._course_ids_by_tenant.setdefault(request.tenant_id, set()).add(course_id)
        return self._to_response(record)

    def get_course(self, tenant_id: str, course_id: str) -> CourseResponse:
        record = self._get_tenant_course(tenant_id, course_id)
        return self._to_response(record)

    def list_courses(self, tenant_id: str) -> list[CourseResponse]:
        tenant_course_ids = self._course_ids_by_tenant.get(tenant_id, set())
        return [self._to_response(self._courses[course_id]) for course_id in tenant_course_ids]

    def update_course(self, course_id: str, request: UpdateCourseRequest) -> CourseResponse:
        record = self._get_tenant_course(request.tenant_id, course_id)
        current_version = record.versions[record.active_version]
        updates = self._dump_model(request, exclude_none=True, exclude={"tenant_id", "updated_by"})
        if not updates:
            return self._to_response(record)

        current_version.payload.update(updates)
        record.updated_at = self._now()
        return self._to_response(record)

    def publish_course(self, course_id: str, request: PublishCourseRequest) -> CourseResponse:
        record = self._get_tenant_course(request.tenant_id, course_id)
        now = self._now()

        effective_from = request.scheduled_publish_at or now
        status = CourseStatus.SCHEDULED if request.scheduled_publish_at and request.scheduled_publish_at > now else CourseStatus.PUBLISHED

        record.status = status
        record.published_version = record.active_version
        record.published_at = now
        record.effective_from = effective_from
        record.updated_at = now
        record.versions[record.active_version].status = status
        return self._to_response(record)

    def create_course_version(
        self,
        course_id: str,
        request: CreateCourseVersionRequest,
    ) -> VersionResponse:
        record = self._get_tenant_course(request.tenant_id, course_id)
        if request.based_on_version not in record.versions:
            raise HTTPException(status_code=404, detail="Base version not found")

        now = self._now()
        base_version = record.versions[request.based_on_version]
        new_version_number = max(record.versions.keys()) + 1

        new_payload = dict(base_version.payload)
        if request.metadata_overrides:
            current_metadata = dict(new_payload.get("metadata") or {})
            current_metadata.update(request.metadata_overrides)
            new_payload["metadata"] = current_metadata

        new_version = CourseVersion(
            version=new_version_number,
            status=CourseStatus.DRAFT,
            created_at=now,
            created_by=request.created_by,
            change_summary=request.change_summary,
            content_refs=request.cloned_content_refs or [],
            payload=new_payload,
        )

        record.versions[new_version_number] = new_version
        record.active_version = new_version_number
        record.status = CourseStatus.DRAFT
        record.updated_at = now

        return VersionResponse(
            course_id=record.course_id,
            version_id=f"{record.course_id}:v{new_version_number}",
            new_version=new_version_number,
            status=CourseStatus.DRAFT,
            created_at=now,
        )

    def delete_course(self, tenant_id: str, course_id: str) -> None:
        _ = self._get_tenant_course(tenant_id, course_id)
        del self._courses[course_id]
        tenant_course_ids = self._course_ids_by_tenant.get(tenant_id)
        if tenant_course_ids is not None:
            tenant_course_ids.discard(course_id)
            if not tenant_course_ids:
                del self._course_ids_by_tenant[tenant_id]

    def _get_tenant_course(self, tenant_id: str, course_id: str) -> CourseRecord:
        record = self._courses.get(course_id)
        if not record or record.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Course not found for tenant")
        return record

    def _to_response(self, record: CourseRecord) -> CourseResponse:
        version_payload = record.versions[record.active_version].payload
        return CourseResponse(
            course_id=record.course_id,
            tenant_id=record.tenant_id,
            status=record.status,
            version=record.active_version,
            created_at=record.created_at,
            updated_at=record.updated_at,
            published_version=record.published_version,
            published_at=record.published_at,
            effective_from=record.effective_from,
            title=version_payload["title"],
            description=version_payload.get("description"),
            category_id=version_payload.get("category_id"),
            language=version_payload.get("language"),
            delivery_mode=version_payload.get("delivery_mode"),
            duration_minutes=version_payload.get("duration_minutes"),
            tags=version_payload.get("tags") or [],
            objectives=version_payload.get("objectives") or [],
            metadata=version_payload.get("metadata") or {},
        )
