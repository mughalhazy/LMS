from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from .audit import AuditLogger
from .events import EventPublisher
from .models import CohortRecord, MembershipRecord, ObservabilityState
from .schemas import (
    AddMembershipRequest,
    CohortKind,
    CohortResponse,
    CohortWithMembershipsResponse,
    CreateCohortRequest,
    LinkProgramRequest,
    MembershipResponse,
    UpdateCohortRequest,
)
from .store import CohortStore, InMemoryCohortStore


class CohortService:
    def __init__(
        self,
        store: CohortStore | None = None,
        audit_logger: AuditLogger | None = None,
        event_publisher: EventPublisher | None = None,
        observability: ObservabilityState | None = None,
    ) -> None:
        self.store = store or InMemoryCohortStore()
        self.audit = audit_logger or AuditLogger("cohort.audit")
        self.event_publisher = event_publisher or EventPublisher()
        self.observability = observability or ObservabilityState()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create_cohort(self, tenant_id: str, request: CreateCohortRequest) -> CohortResponse:
        now = self._now()
        if request.schedule.starts_at and request.schedule.ends_at and request.schedule.ends_at < request.schedule.starts_at:
            raise HTTPException(status_code=422, detail="schedule.ends_at must be >= schedule.starts_at")
        if request.kind == CohortKind.ACADEMY_BATCH and not request.program_id:
            raise HTTPException(status_code=422, detail="academy_batch cohorts require a program_id")

        cohort = CohortRecord(
            cohort_id=str(uuid4()),
            tenant_id=tenant_id,
            name=request.name,
            code=request.code,
            kind=request.kind,
            status=request.status,
            schedule=request.schedule,
            program_id=request.program_id,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
            created_by=request.created_by,
        )
        self.store.save_cohort(cohort)
        self.observability.inc("cohorts_created_total")
        self.audit.log(
            event_type="cohort.created",
            tenant_id=tenant_id,
            actor_id=request.created_by,
            details={"cohort_id": cohort.cohort_id, "kind": cohort.kind.value},
        )
        self.event_publisher.publish(
            event_type="cohort.lifecycle.changed",
            topic="lms.cohort.lifecycle.v1",
            tenant_id=tenant_id,
            aggregate_id=cohort.cohort_id,
            payload={
                "action": "created",
                "status": cohort.status.value,
                "kind": cohort.kind.value,
            },
        )
        return CohortResponse.model_validate(cohort)

    def create_batch(self, tenant_id: str, request: CreateCohortRequest) -> CohortResponse:
        request.kind = CohortKind.ACADEMY_BATCH
        return self.create_cohort(tenant_id, request)

    def list_cohorts(self, tenant_id: str) -> list[CohortResponse]:
        self.observability.inc("cohort_reads_total")
        return [CohortResponse.model_validate(record) for record in self.store.list_cohorts(tenant_id)]

    def get_cohort(self, tenant_id: str, cohort_id: str) -> CohortWithMembershipsResponse:
        cohort = self._require_cohort(tenant_id, cohort_id)
        memberships = self.store.list_memberships(tenant_id, cohort_id)
        self.observability.inc("cohort_reads_total")
        return CohortWithMembershipsResponse(
            cohort=CohortResponse.model_validate(cohort),
            memberships=[MembershipResponse.model_validate(m) for m in memberships],
        )

    def update_cohort(self, tenant_id: str, cohort_id: str, request: UpdateCohortRequest) -> CohortResponse:
        cohort = self._require_cohort(tenant_id, cohort_id)

        if request.name is not None:
            cohort.name = request.name
        if request.program_id is not None:
            cohort.program_id = request.program_id
        if request.schedule is not None:
            if request.schedule.starts_at and request.schedule.ends_at and request.schedule.ends_at < request.schedule.starts_at:
                raise HTTPException(status_code=422, detail="schedule.ends_at must be >= schedule.starts_at")
            cohort.schedule = request.schedule
        if request.metadata is not None:
            cohort.metadata = request.metadata
        if request.status is not None:
            cohort.status = request.status
            self.event_publisher.publish(
                event_type="cohort.lifecycle.changed",
                topic="lms.cohort.lifecycle.v1",
                tenant_id=tenant_id,
                aggregate_id=cohort.cohort_id,
                payload={"action": "status_updated", "status": cohort.status.value, "kind": cohort.kind.value},
            )

        cohort.updated_at = self._now()
        self.store.save_cohort(cohort)
        self.observability.inc("cohorts_updated_total")
        self.audit.log(
            event_type="cohort.updated",
            tenant_id=tenant_id,
            actor_id=request.updated_by,
            details={"cohort_id": cohort.cohort_id},
        )
        return CohortResponse.model_validate(cohort)

    def link_program(self, tenant_id: str, cohort_id: str, request: LinkProgramRequest) -> CohortResponse:
        cohort = self._require_cohort(tenant_id, cohort_id)
        cohort.program_id = request.program_id
        cohort.updated_at = self._now()
        self.store.save_cohort(cohort)
        self.observability.inc("program_links_total")
        self.audit.log(
            event_type="cohort.program_linked",
            tenant_id=tenant_id,
            actor_id=request.linked_by,
            details={"cohort_id": cohort.cohort_id, "program_id": request.program_id},
        )
        self.event_publisher.publish(
            event_type="cohort.program.linked",
            topic="lms.cohort.program_linked.v1",
            tenant_id=tenant_id,
            aggregate_id=cohort.cohort_id,
            payload={"program_id": request.program_id, "kind": cohort.kind.value},
        )
        return CohortResponse.model_validate(cohort)

    def add_membership(self, tenant_id: str, cohort_id: str, request: AddMembershipRequest) -> MembershipResponse:
        cohort = self._require_cohort(tenant_id, cohort_id)
        if cohort.kind == CohortKind.ACADEMY_BATCH and request.role not in {"learner", "instructor", "mentor"}:
            raise HTTPException(status_code=422, detail="academy_batch role must be learner, instructor, or mentor")
        joined_at = request.joined_at or self._now()
        membership = MembershipRecord(
            membership_id=str(uuid4()),
            cohort_id=cohort.cohort_id,
            tenant_id=tenant_id,
            user_id=request.user_id,
            role=request.role,
            joined_at=joined_at,
            added_by=request.added_by,
        )
        self.store.save_membership(membership)
        self.observability.inc("cohort_memberships_added_total")
        self.audit.log(
            event_type="cohort.membership_added",
            tenant_id=tenant_id,
            actor_id=request.added_by,
            details={"cohort_id": cohort_id, "membership_id": membership.membership_id},
        )
        return MembershipResponse.model_validate(membership)

    def remove_membership(self, tenant_id: str, cohort_id: str, membership_id: str, removed_by: str) -> None:
        self._require_cohort(tenant_id, cohort_id)
        self.store.remove_membership(tenant_id, cohort_id, membership_id)
        self.observability.inc("cohort_memberships_removed_total")
        self.audit.log(
            event_type="cohort.membership_removed",
            tenant_id=tenant_id,
            actor_id=removed_by,
            details={"cohort_id": cohort_id, "membership_id": membership_id},
        )

    def archive_batch(self, tenant_id: str, batch_id: str, archived_by: str) -> CohortResponse:
        cohort = self._require_cohort(tenant_id, batch_id)
        if cohort.kind != CohortKind.ACADEMY_BATCH:
            raise HTTPException(status_code=422, detail="archive_batch only supports academy_batch cohorts")
        cohort.status = CohortStatus.ARCHIVED
        cohort.updated_at = self._now()
        self.store.save_cohort(cohort)
        self.audit.log(
            event_type="cohort.batch_archived",
            tenant_id=tenant_id,
            actor_id=archived_by,
            details={"cohort_id": cohort.cohort_id},
        )
        return CohortResponse.model_validate(cohort)

    def list_batch_roster(self, tenant_id: str, batch_id: str) -> dict[str, list[str]]:
        cohort = self._require_cohort(tenant_id, batch_id)
        if cohort.kind != CohortKind.ACADEMY_BATCH:
            raise HTTPException(status_code=422, detail="list_batch_roster only supports academy_batch cohorts")
        memberships = self.store.list_memberships(tenant_id, batch_id)
        return {
            "learner_ids": [m.user_id for m in memberships if m.role == "learner"],
            "teacher_ids": [m.user_id for m in memberships if m.role in {"instructor", "mentor"}],
        }

    def delete_cohort(self, tenant_id: str, cohort_id: str, deleted_by: str) -> None:
        cohort = self._require_cohort(tenant_id, cohort_id)
        self.store.delete_cohort(tenant_id, cohort_id)
        self.observability.inc("cohorts_deleted_total")
        self.audit.log(
            event_type="cohort.deleted",
            tenant_id=tenant_id,
            actor_id=deleted_by,
            details={"cohort_id": cohort_id, "kind": cohort.kind.value},
        )

    def _require_cohort(self, tenant_id: str, cohort_id: str) -> CohortRecord:
        cohort = self.store.get_cohort(tenant_id, cohort_id)
        if not cohort:
            raise HTTPException(status_code=404, detail="Cohort not found")
        return cohort
