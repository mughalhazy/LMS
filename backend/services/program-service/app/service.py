from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from .audit import AuditLogger
from .events import EventPublisher
from .models import (
    ALLOWED_TRANSITIONS,
    LinkStatus,
    MappingStatus,
    Program,
    ProgramCourseMap,
    ProgramInstitutionLink,
    ProgramStatus,
    ProgramStatusHistory,
)
from .observability import ObservabilityHooks
from .schemas import (
    CreateProgramRequest,
    InstitutionLinkResponse,
    ProgramCourseInput,
    ProgramCourseResponse,
    ProgramCoursesMapResponse,
    ProgramDetailResponse,
    ProgramListResponse,
    ProgramResponse,
    ProgramUpdateResult,
    ReplaceProgramCoursesRequest,
    StatusTransitionResponse,
    TransitionProgramStatusRequest,
    UpdateProgramRequest,
    UpsertInstitutionLinkRequest,
)
from .store import ProgramStore


class ProgramService:
    def __init__(self, store: ProgramStore, known_courses: set[str] | None = None) -> None:
        self.store = store
        self.audit_logger = AuditLogger("program.audit")
        self.event_publisher = EventPublisher()
        self.observability = ObservabilityHooks()
        self.known_courses = known_courses or set()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create_program(self, request: CreateProgramRequest) -> ProgramResponse:
        if self.store.code_exists(request.tenant_id, request.code):
            raise HTTPException(status_code=409, detail="program_code_already_exists")
        now = self._now()
        program = Program(
            program_id=str(uuid4()),
            tenant_id=request.tenant_id,
            institution_id=request.institution_id,
            code=request.code,
            title=request.title,
            description=request.description,
            status=ProgramStatus.DRAFT,
            version=1,
            visibility=request.visibility,
            start_date=request.start_date,
            end_date=request.end_date,
            metadata=request.metadata,
            created_by=request.created_by,
            updated_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        self.store.create(program)
        self.audit_logger.log(event_type="program.creation", tenant_id=request.tenant_id, actor_id=request.created_by, details={"program_id": program.program_id, "code": request.code})
        self.event_publisher.publish(event_type="lms.program.program_created.v1", tenant_id=request.tenant_id, payload={"program_id": program.program_id, "institution_id": request.institution_id, "code": request.code, "status": program.status.value, "version": 1, "created_at": now.isoformat()})
        self.observability.increment("program_create_total")
        return self._program_response(program)

    def get_program(self, tenant_id: str, program_id: str) -> ProgramDetailResponse:
        program = self._get_tenant_program(tenant_id, program_id)
        return ProgramDetailResponse(
            program=self._program_response(program),
            institution_link=self._link_response(program.institution_link),
            mapped_courses=[self._course_response(c) for c in sorted(program.course_mappings, key=lambda item: item.sequence_order)],
            status_history=[
                StatusTransitionResponse(
                    program_id=history.program_id,
                    from_status=history.from_status,
                    to_status=history.to_status,
                    changed_at=history.changed_at,
                )
                for history in program.status_history[-10:]
            ],
        )

    def list_programs(self, tenant_id: str, institution_id: str | None, status: ProgramStatus | None, page: int, page_size: int) -> ProgramListResponse:
        programs = self.store.list_by_tenant(tenant_id)
        if institution_id:
            programs = [p for p in programs if p.institution_id == institution_id]
        if status:
            programs = [p for p in programs if p.status == status]
        total = len(programs)
        start = (page - 1) * page_size
        end = start + page_size
        return ProgramListResponse(items=[self._program_response(p) for p in programs[start:end]], page=page, page_size=page_size, total=total)

    def update_program(self, program_id: str, request: UpdateProgramRequest) -> ProgramUpdateResult:
        program = self._get_tenant_program(request.tenant_id, program_id)
        updates = request.model_dump(exclude_none=True, exclude={"tenant_id", "updated_by"})
        if not updates:
            return ProgramUpdateResult(program_id=program.program_id, version=program.version, status=program.status, updated_fields=[], updated_at=program.updated_at)

        for field, value in updates.items():
            setattr(program, field, value)
        program.version += 1
        program.updated_by = request.updated_by
        program.updated_at = self._now()
        self.store.update(program)
        updated_fields = sorted(updates.keys())
        self.audit_logger.log(event_type="program.updated", tenant_id=program.tenant_id, actor_id=request.updated_by, details={"program_id": program_id, "updated_fields": updated_fields, "version": program.version})
        self.event_publisher.publish(event_type="lms.program.program_updated.v1", tenant_id=program.tenant_id, payload={"program_id": program.program_id, "updated_fields": updated_fields, "version": program.version, "updated_at": program.updated_at.isoformat()})
        self.observability.increment("program_update_total")
        return ProgramUpdateResult(program_id=program.program_id, version=program.version, status=program.status, updated_fields=updated_fields, updated_at=program.updated_at)

    def transition_status(self, program_id: str, request: TransitionProgramStatusRequest) -> StatusTransitionResponse:
        program = self._get_tenant_program(request.tenant_id, program_id)
        if request.target_status not in ALLOWED_TRANSITIONS[program.status]:
            raise HTTPException(status_code=400, detail="invalid_status_transition")
        if request.target_status == ProgramStatus.ACTIVE and not program.course_mappings:
            raise HTTPException(status_code=400, detail="program_requires_mapped_courses_before_activation")

        from_status = program.status
        program.status = request.target_status
        program.version += 1
        changed_at = self._now()
        program.updated_at = changed_at
        program.updated_by = request.changed_by
        program.status_history.append(ProgramStatusHistory(program_id=program.program_id, from_status=from_status, to_status=request.target_status, changed_by=request.changed_by, change_reason=request.change_reason, changed_at=changed_at))
        self.store.update(program)
        self.audit_logger.log(event_type="program.status.changed", tenant_id=program.tenant_id, actor_id=request.changed_by, details={"program_id": program.program_id, "from_status": from_status.value, "to_status": request.target_status.value, "reason": request.change_reason})
        self.event_publisher.publish(event_type="lms.program.program_status_changed.v1", tenant_id=program.tenant_id, payload={"program_id": program.program_id, "from_status": from_status.value, "to_status": request.target_status.value, "change_reason": request.change_reason, "changed_by": request.changed_by, "changed_at": changed_at.isoformat()})
        self.observability.increment("program_status_transition_total")
        return StatusTransitionResponse(program_id=program.program_id, from_status=from_status, to_status=request.target_status, changed_at=changed_at)

    def upsert_institution_link(self, program_id: str, request: UpsertInstitutionLinkRequest) -> InstitutionLinkResponse:
        program = self._get_tenant_program(request.tenant_id, program_id)
        now = self._now()
        program.institution_link = ProgramInstitutionLink(program_id=program.program_id, institution_id=request.institution_id, link_status=request.link_status, linked_at=now if request.link_status == LinkStatus.LINKED else None, unlinked_at=now if request.link_status == LinkStatus.UNLINKED else None, link_metadata=request.link_metadata)
        program.updated_by = request.updated_by
        program.updated_at = now
        program.version += 1
        self.store.update(program)
        self.audit_logger.log(event_type="program.institution_link.updated", tenant_id=program.tenant_id, actor_id=request.updated_by, details={"program_id": program.program_id, "institution_id": request.institution_id, "link_status": request.link_status.value})
        if request.link_status == LinkStatus.LINKED:
            self.event_publisher.publish(event_type="lms.program.program_institution_linked.v1", tenant_id=program.tenant_id, payload={"program_id": program.program_id, "institution_id": request.institution_id, "link_status": request.link_status.value, "linked_at": now.isoformat()})
        self.observability.increment("program_link_upsert_total")
        return self._link_response(program.institution_link)

    def replace_program_courses(self, program_id: str, request: ReplaceProgramCoursesRequest) -> ProgramCoursesMapResponse:
        program = self._get_tenant_program(request.tenant_id, program_id)
        if program.status not in {ProgramStatus.DRAFT, ProgramStatus.ACTIVE}:
            raise HTTPException(status_code=400, detail="mapping_updates_not_allowed_for_program_status")
        self._validate_course_map(request.courses)

        now = self._now()
        program.course_mappings = [
            ProgramCourseMap(
                program_id=program.program_id,
                course_id=course.course_id,
                sequence_order=course.sequence_order,
                is_required=course.is_required,
                minimum_completion_pct=course.minimum_completion_pct,
                availability_rule=course.availability_rule,
                mapping_status=MappingStatus.MAPPED,
                mapped_at=now,
            )
            for course in sorted(request.courses, key=lambda item: item.sequence_order)
        ]
        program.mapping_version += 1
        program.version += 1
        program.updated_by = request.updated_by
        program.updated_at = now
        self.store.update(program)
        self.audit_logger.log(event_type="program.courses.mapped", tenant_id=program.tenant_id, actor_id=request.updated_by, details={"program_id": program.program_id, "mapping_version": program.mapping_version, "course_count": len(program.course_mappings)})
        self.event_publisher.publish(event_type="lms.program.program_courses_mapped.v1", tenant_id=program.tenant_id, payload={"program_id": program.program_id, "mapping_version": program.mapping_version, "courses": [c.course_id for c in program.course_mappings], "updated_by": request.updated_by, "updated_at": now.isoformat()})
        self.observability.increment("program_course_map_replace_total")
        return ProgramCoursesMapResponse(program_id=program.program_id, mapping_version=program.mapping_version, mapped_courses=[self._course_response(c) for c in program.course_mappings], updated_at=program.updated_at)

    def remove_course(self, tenant_id: str, program_id: str, course_id: str, updated_by: str) -> None:
        program = self._get_tenant_program(tenant_id, program_id)
        existing = [c for c in program.course_mappings if c.course_id == course_id]
        if not existing:
            raise HTTPException(status_code=404, detail="program_course_mapping_not_found")
        program.course_mappings = [c for c in program.course_mappings if c.course_id != course_id]
        for index, course in enumerate(program.course_mappings, start=1):
            course.sequence_order = index
        program.mapping_version += 1
        program.version += 1
        program.updated_by = updated_by
        program.updated_at = self._now()
        self.store.update(program)
        self.audit_logger.log(event_type="program.course.unmapped", tenant_id=program.tenant_id, actor_id=updated_by, details={"program_id": program_id, "course_id": course_id})
        self.observability.increment("program_course_map_delete_total")

    def _validate_course_map(self, courses: list[ProgramCourseInput]) -> None:
        ids = [course.course_id for course in courses]
        if len(ids) != len(set(ids)):
            raise HTTPException(status_code=400, detail="duplicate_course_ids_not_allowed")

        orders = sorted(course.sequence_order for course in courses)
        if orders != list(range(1, len(courses) + 1)):
            raise HTTPException(status_code=400, detail="sequence_order_must_be_contiguous_starting_at_1")

        missing = [course_id for course_id in ids if course_id not in self.known_courses]
        if missing:
            raise HTTPException(status_code=422, detail=f"course_not_found:{missing[0]}")

    def _get_tenant_program(self, tenant_id: str, program_id: str) -> Program:
        program = self.store.get(program_id)
        if not program or program.tenant_id != tenant_id or program.deleted:
            raise HTTPException(status_code=404, detail="program_not_found")
        return program

    @staticmethod
    def _program_response(program: Program) -> ProgramResponse:
        return ProgramResponse(
            program_id=program.program_id,
            tenant_id=program.tenant_id,
            institution_id=program.institution_id,
            code=program.code,
            title=program.title,
            description=program.description,
            status=program.status,
            version=program.version,
            visibility=program.visibility,
            start_date=program.start_date,
            end_date=program.end_date,
            metadata=program.metadata,
            mapping_version=program.mapping_version,
            created_at=program.created_at,
            updated_at=program.updated_at,
        )

    @staticmethod
    def _course_response(course: ProgramCourseMap) -> ProgramCourseResponse:
        return ProgramCourseResponse(course_id=course.course_id, sequence_order=course.sequence_order, is_required=course.is_required, minimum_completion_pct=course.minimum_completion_pct)

    @staticmethod
    def _link_response(link: ProgramInstitutionLink | None) -> InstitutionLinkResponse | None:
        if not link:
            return None
        return InstitutionLinkResponse(program_id=link.program_id, institution_id=link.institution_id, link_status=link.link_status, linked_at=link.linked_at, unlinked_at=link.unlinked_at, link_metadata=link.link_metadata)
