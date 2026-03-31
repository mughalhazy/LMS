from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from fastapi import HTTPException

from .audit import AuditLogger
from backend.services.shared.context.correlation import ensure_correlation_id
from backend.services.shared.events.envelope import build_event
from shared.control_plane import ConfigService, EntitlementService
from shared.utils.entitlement import TenantEntitlementContext
from backend.services.shared.utils.tenant_context import tenant_contract_from_inputs

from .schemas import (
    CourseMetadata,
    CourseResponse,
    CourseStatus,
    DeliveryRole,
    EventEnvelope,
    ProgramLink,
    PublishCourseRequest,
    PublishStatus,
    SessionLink,
    UpsertProgramLinksRequest,
    UpsertSessionLinksRequest,
    UpdateCourseRequest,
    CreateCourseRequest,
    ArchiveCourseRequest,
)


class CourseStorageContract(Protocol):
    def save(self, record: "CourseRecord") -> None: ...

    def get(self, course_id: str) -> "CourseRecord | None": ...

    def delete(self, course_id: str) -> None: ...

    def list_by_tenant(self, tenant_id: str) -> list["CourseRecord"]: ...


class EventPublisher:
    def __init__(self) -> None:
        self._events: list[EventEnvelope] = []

    def publish(self, event: EventEnvelope) -> None:
        self._events.append(event)

    def list_events(self) -> list[EventEnvelope]:
        return list(self._events)


class InMemoryCourseStorage(CourseStorageContract):
    def __init__(self) -> None:
        self._records: dict[str, CourseRecord] = {}
        self._course_ids_by_tenant: dict[str, set[str]] = {}

    def save(self, record: "CourseRecord") -> None:
        self._records[record.course_id] = record
        self._course_ids_by_tenant.setdefault(record.tenant_id, set()).add(record.course_id)

    def get(self, course_id: str) -> "CourseRecord | None":
        return self._records.get(course_id)

    def delete(self, course_id: str) -> None:
        record = self._records[course_id]
        del self._records[course_id]
        self._course_ids_by_tenant[record.tenant_id].discard(course_id)

    def list_by_tenant(self, tenant_id: str) -> list["CourseRecord"]:
        return [self._records[cid] for cid in self._course_ids_by_tenant.get(tenant_id, set())]


@dataclass
class CourseRecord:
    course_id: str
    tenant_id: str
    institution_id: str | None
    created_at: datetime
    updated_at: datetime
    status: CourseStatus
    publish_status: PublishStatus
    published_at: datetime | None
    published_by: str | None
    created_by: str
    course_code: str | None
    title: str
    description: str | None
    language_code: str | None
    credit_value: float | None
    grading_scheme: str | None
    metadata: CourseMetadata = field(default_factory=CourseMetadata)
    program_links: list[ProgramLink] = field(default_factory=list)
    session_links: list[SessionLink] = field(default_factory=list)


class CourseService:
    def __init__(self, storage: CourseStorageContract | None = None) -> None:
        self.storage = storage or InMemoryCourseStorage()
        self.audit_logger = AuditLogger("course.audit")
        self.event_publisher = EventPublisher()
        self._config_service = ConfigService()
        self._entitlement_service = EntitlementService(config_service=self._config_service)
        self.metrics: dict[str, int] = {
            "courses_created_total": 0,
            "workforce_mandatory_courses_total": 0,
            "courses_published_total": 0,
            "courses_archived_total": 0,
            "course_link_updates_total": 0,
        }

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create_course(self, request: CreateCourseRequest) -> CourseResponse:
        self._assert_capability(request, "course.write")
        now = self._now()
        record = CourseRecord(
            course_id=str(uuid4()),
            tenant_id=request.tenant_id,
            institution_id=request.institution_id,
            created_at=now,
            updated_at=now,
            status=CourseStatus.DRAFT,
            publish_status=PublishStatus.UNPUBLISHED,
            published_at=None,
            published_by=None,
            created_by=request.created_by,
            course_code=request.course_code,
            title=request.title,
            description=request.description,
            language_code=request.language_code,
            credit_value=request.credit_value,
            grading_scheme=request.grading_scheme,
            metadata=request.metadata,
        )
        self.storage.save(record)
        self.metrics["courses_created_total"] += 1
        if request.metadata.audience == "workforce" and request.metadata.mandatory_training:
            self.metrics["workforce_mandatory_courses_total"] += 1
        self.audit_logger.log(event_type="course.created", tenant_id=request.tenant_id, actor_id=request.created_by, details={"course_id": record.course_id})
        self._publish_event(
            "course.lifecycle.created.v1",
            record,
            request.created_by,
            {
                "status": record.status.value,
                "audience": request.metadata.audience,
                "mandatory_training": request.metadata.mandatory_training,
                "compliance_policy_id": request.metadata.compliance_policy_id,
            },
        )
        return self._to_response(record)

    def list_courses(self, tenant_id: str) -> list[CourseResponse]:
        return [self._to_response(record) for record in self.storage.list_by_tenant(tenant_id)]

    def get_course(self, tenant_id: str, course_id: str) -> CourseResponse:
        return self._to_response(self._get_tenant_course(tenant_id, course_id))

    def update_course(self, course_id: str, request: UpdateCourseRequest) -> CourseResponse:
        self._assert_capability(request, "course.write")
        record = self._get_tenant_course(request.tenant_id, course_id)
        updated_fields: list[str] = []
        for field_name in ["title", "course_code", "description", "language_code", "credit_value", "grading_scheme"]:
            value = getattr(request, field_name)
            if value is not None:
                setattr(record, field_name, value)
                updated_fields.append(field_name)

        if request.metadata is not None:
            record.metadata = request.metadata
            updated_fields.append("metadata")

        record.updated_at = self._now()
        self.storage.save(record)
        self.audit_logger.log(event_type="course.updated", tenant_id=request.tenant_id, actor_id=request.updated_by, details={"course_id": course_id, "updated_fields": updated_fields})
        self._publish_event("course.lifecycle.updated.v1", record, request.updated_by, {"updated_fields": updated_fields})
        return self._to_response(record)

    def publish_course(self, course_id: str, request: PublishCourseRequest) -> CourseResponse:
        self._assert_capability(request, "course.write")
        record = self._get_tenant_course(request.tenant_id, course_id)
        if record.status == CourseStatus.ARCHIVED:
            raise HTTPException(status_code=409, detail="Archived courses cannot be published")
        if not record.title:
            raise HTTPException(status_code=422, detail="Course must have title before publishing")

        now = self._now()
        record.status = CourseStatus.PUBLISHED
        record.publish_status = PublishStatus.SCHEDULED if request.scheduled_publish_at and request.scheduled_publish_at > now else PublishStatus.PUBLISHED
        record.published_at = now
        record.published_by = request.requested_by
        record.updated_at = now
        self.storage.save(record)

        self.metrics["courses_published_total"] += 1
        self.audit_logger.log(event_type="course.published", tenant_id=request.tenant_id, actor_id=request.requested_by, details={"course_id": course_id, "publish_status": record.publish_status.value})
        self._publish_event("course.lifecycle.published.v1", record, request.requested_by, {"publish_status": record.publish_status.value, "publish_notes": request.publish_notes})
        return self._to_response(record)

    def archive_course(self, course_id: str, request: ArchiveCourseRequest) -> CourseResponse:
        self._assert_capability(request, "course.write")
        record = self._get_tenant_course(request.tenant_id, course_id)
        record.status = CourseStatus.ARCHIVED
        record.updated_at = self._now()
        self.storage.save(record)
        self.metrics["courses_archived_total"] += 1
        self.audit_logger.log(event_type="course.archived", tenant_id=request.tenant_id, actor_id=request.requested_by, details={"course_id": course_id})
        self._publish_event("course.lifecycle.archived.v1", record, request.requested_by, {"status": record.status.value})
        return self._to_response(record)

    def upsert_program_links(self, course_id: str, request: UpsertProgramLinksRequest) -> list[ProgramLink]:
        record = self._get_tenant_course(request.tenant_id, course_id)
        deduped: dict[str, ProgramLink] = {}
        for link in request.program_links:
            deduped[link.program_id] = link
        primary_links = [link for link in deduped.values() if link.is_primary]
        if len(primary_links) > 1:
            raise HTTPException(status_code=422, detail="Only one primary program link is allowed")
        normalized_links = sorted(deduped.values(), key=lambda item: (not item.is_primary, item.program_id))
        record.program_links = normalized_links
        university_meta = dict(record.metadata.extra.get("university", {}))
        university_meta["program_link_count"] = len(normalized_links)
        university_meta["has_primary_program"] = bool(primary_links)
        record.metadata.extra["university"] = university_meta
        record.updated_at = self._now()
        self.storage.save(record)
        self.metrics["course_link_updates_total"] += 1
        self.audit_logger.log(event_type="course.program_links.updated", tenant_id=request.tenant_id, actor_id=request.updated_by, details={"course_id": course_id, "link_count": len(request.program_links)})
        self._publish_event("course.linkage.program.updated.v1", record, request.updated_by, {"program_links": [link.model_dump() for link in normalized_links]})
        return normalized_links

    def upsert_session_links(self, course_id: str, request: UpsertSessionLinksRequest) -> list[SessionLink]:
        record = self._get_tenant_course(request.tenant_id, course_id)
        normalized_links = [SessionLink(session_id=link.session_id, delivery_role=DeliveryRole(link.delivery_role)) for link in request.session_links]
        record.session_links = normalized_links
        record.updated_at = self._now()
        self.storage.save(record)
        self.metrics["course_link_updates_total"] += 1
        self.audit_logger.log(event_type="course.session_links.updated", tenant_id=request.tenant_id, actor_id=request.updated_by, details={"course_id": course_id, "link_count": len(normalized_links)})
        self._publish_event("course.linkage.session.updated.v1", record, request.updated_by, {"session_links": [link.model_dump() for link in normalized_links]})
        return normalized_links

    def delete_course(self, tenant_id: str, course_id: str) -> None:
        self._get_tenant_course(tenant_id, course_id)
        self.storage.delete(course_id)

    def _get_tenant_course(self, tenant_id: str, course_id: str) -> CourseRecord:
        record = self.storage.get(course_id)
        if not record or record.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Course not found for tenant")
        return record

    def _publish_event(self, event_type: str, record: CourseRecord, actor_id: str, payload: dict, correlation_id: str | None = None) -> None:
        event = build_event(
            event_type=event_type,
            tenant_id=record.tenant_id,
            correlation_id=ensure_correlation_id(correlation_id),
            payload=payload,
            metadata={"aggregate_id": record.course_id, "actor_id": actor_id, "producer": "course-service"},
        )
        self.event_publisher.publish(EventEnvelope(**event.__dict__))


    @staticmethod
    def _tenant_from_request(request: object) -> TenantEntitlementContext:
        tenant = tenant_contract_from_inputs(
            tenant_id=request.tenant_id,
            tenant_name=getattr(request, "tenant_name", None),
            country_code=getattr(request, "country_code", None),
            segment_type=getattr(request, "segment_type", None),
            plan_type=getattr(request, "plan_type", None),
            addon_flags=getattr(request, "addon_flags", []),
        )
        return TenantEntitlementContext(
            tenant_id=tenant.tenant_id,
            country_code=tenant.country_code,
            segment_id=tenant.segment_type,
            plan_type=tenant.plan_type,
            add_ons=tuple(tenant.addon_flags),
        )

    def _assert_capability(self, request: object, capability: str) -> None:
        tenant = self._tenant_from_request(request)
        if not self._entitlement_service.is_enabled(tenant, capability):
            raise HTTPException(status_code=403, detail=f"capability disabled: {capability}")

    @staticmethod
    def _to_response(record: CourseRecord) -> CourseResponse:
        return CourseResponse(
            course_id=record.course_id,
            tenant_id=record.tenant_id,
            institution_id=record.institution_id,
            status=record.status,
            publish_status=record.publish_status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            published_at=record.published_at,
            published_by=record.published_by,
            course_code=record.course_code,
            title=record.title,
            description=record.description,
            language_code=record.language_code,
            credit_value=record.credit_value,
            grading_scheme=record.grading_scheme,
            metadata=record.metadata,
            program_links=record.program_links,
            session_links=record.session_links,
        )
