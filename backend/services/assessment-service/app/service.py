from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from .audit import AuditLogger
from .events import DomainEvent, EventPublisher
from backend.services.shared.context.correlation import ensure_correlation_id
from backend.services.shared.events.envelope import build_event
from shared.control_plane import build_control_plane_clients
from shared.utils.entitlement import TenantEntitlementContext
from shared.models.capability import Capability
from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope
from backend.services.shared.utils.tenant_context import tenant_contract_from_inputs
from .models import AssessmentDefinition, AssessmentStatus, AssessmentType, AttemptRecord, AttemptStatus, SubmissionRecord
from .observability import ServiceMetrics
from .schemas import (
    AssessmentCreateRequest,
    AssessmentListResponse,
    AssessmentResponse,
    AssessmentUpdateRequest,
    AttemptResponse,
    AttemptStartRequest,
    GradeAttemptRequest,
    SubmissionCreateRequest,
    SubmissionResponse,
)
from .store import AssessmentStore


class AssessmentService:
    def __init__(
        self,
        store: AssessmentStore,
        event_publisher: EventPublisher,
        audit_logger: AuditLogger,
        metrics: ServiceMetrics,
    ) -> None:
        self.store = store
        self.event_publisher = event_publisher
        self.audit_logger = audit_logger
        self.metrics = metrics
        control_plane = build_control_plane_clients()
        self._config_service = control_plane.config_service
        self._entitlement_service = control_plane.entitlement_service
        self._capability_registry = control_plane.capability_registry
        self._register_default_capabilities()
        self._seed_default_entitlements()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _register_default_capabilities(self) -> None:
        for capability_id in ("assessment.author", "assessment.attempt"):
            if self._capability_registry.get_capability(capability_id):
                continue
            self._capability_registry.register_capability(
                Capability(
                    capability_id=capability_id,
                    name=capability_id,
                    description=f"Default capability for {capability_id}",
                    category="assessment",
                    default_enabled=True,
                    included_in_plans=("basic", "pro", "enterprise"),
                )
            )

    def _seed_default_entitlements(self) -> None:
        self._config_service.upsert_override(
            ConfigOverride(
                scope=ConfigScope(level=ConfigLevel.GLOBAL, scope_id="global"),
                capability_enabled={
                    "assessment.author": True,
                    "assessment.attempt": True,
                },
            )
        )

    def create_assessment(self, tenant_id: str, request: AssessmentCreateRequest) -> AssessmentResponse:
        self._assert_capability(tenant_id, "assessment.author")
        if request.passing_score > request.max_score:
            raise HTTPException(status_code=422, detail="passing_score cannot exceed max_score")

        record = AssessmentDefinition(
            assessment_id=str(uuid4()),
            tenant_id=tenant_id,
            course_id=request.course_id,
            lesson_id=request.lesson_id,
            title=request.title,
            description=request.description,
            assessment_type=request.assessment_type,
            status=AssessmentStatus.DRAFT,
            max_score=request.max_score,
            passing_score=request.passing_score,
            time_limit_minutes=request.time_limit_minutes,
            question_count=request.question_count,
            metadata=request.metadata,
            created_by=request.actor_id,
            created_at=self._now(),
            updated_at=self._now(),
        )
        created = self.store.create_assessment(record)
        self.metrics.inc("assessments_created")
        self._audit(tenant_id, request.actor_id, "assessment.created", created.assessment_id, {"type": created.assessment_type.value})
        self._event("assessment.created", tenant_id, created.assessment_id, {"status": created.status.value, "type": created.assessment_type.value})
        return self._to_assessment_response(created)

    def list_assessments(self, tenant_id: str) -> AssessmentListResponse:
        items = sorted(self.store.list_assessments(tenant_id), key=lambda item: item.created_at)
        return AssessmentListResponse(items=[self._to_assessment_response(item) for item in items])

    def get_assessment(self, tenant_id: str, assessment_id: str) -> AssessmentResponse:
        record = self.store.get_assessment(tenant_id, assessment_id)
        if not record:
            raise HTTPException(status_code=404, detail="assessment not found")
        return self._to_assessment_response(record)

    def update_assessment(self, tenant_id: str, assessment_id: str, request: AssessmentUpdateRequest) -> AssessmentResponse:
        self._assert_capability(tenant_id, "assessment.author")
        current = self.store.get_assessment(tenant_id, assessment_id)
        if not current:
            raise HTTPException(status_code=404, detail="assessment not found")

        updated = replace(
            current,
            title=request.title if request.title is not None else current.title,
            description=request.description if request.description is not None else current.description,
            max_score=request.max_score if request.max_score is not None else current.max_score,
            passing_score=request.passing_score if request.passing_score is not None else current.passing_score,
            time_limit_minutes=request.time_limit_minutes if request.time_limit_minutes is not None else current.time_limit_minutes,
            question_count=request.question_count if request.question_count is not None else current.question_count,
            metadata=request.metadata if request.metadata is not None else current.metadata,
            updated_at=self._now(),
        )
        if updated.passing_score > updated.max_score:
            raise HTTPException(status_code=422, detail="passing_score cannot exceed max_score")

        persisted = self.store.update_assessment(updated)
        self.metrics.inc("assessments_updated")
        self._audit(tenant_id, request.actor_id, "assessment.updated", assessment_id, {})
        self._event("assessment.updated", tenant_id, assessment_id, {"status": persisted.status.value})
        return self._to_assessment_response(persisted)

    def transition_assessment(
        self,
        tenant_id: str,
        assessment_id: str,
        actor_id: str,
        target_status: AssessmentStatus,
    ) -> AssessmentResponse:
        current = self.store.get_assessment(tenant_id, assessment_id)
        if not current:
            raise HTTPException(status_code=404, detail="assessment not found")

        allowed = {
            AssessmentStatus.DRAFT: {AssessmentStatus.PUBLISHED},
            AssessmentStatus.PUBLISHED: {AssessmentStatus.ACTIVE, AssessmentStatus.RETIRED},
            AssessmentStatus.ACTIVE: {AssessmentStatus.RETIRED},
            AssessmentStatus.RETIRED: set(),
        }
        if target_status not in allowed[current.status]:
            raise HTTPException(status_code=409, detail="invalid lifecycle transition")

        updated = replace(current, status=target_status, updated_at=self._now())
        persisted = self.store.update_assessment(updated)
        self._audit(tenant_id, actor_id, "assessment.lifecycle_changed", assessment_id, {"to": target_status.value})
        self._event("assessment.lifecycle_changed", tenant_id, assessment_id, {"from": current.status.value, "to": target_status.value})
        return self._to_assessment_response(persisted)

    def delete_assessment(self, tenant_id: str, assessment_id: str, actor_id: str) -> None:
        current = self.store.get_assessment(tenant_id, assessment_id)
        if not current:
            raise HTTPException(status_code=404, detail="assessment not found")
        self.store.delete_assessment(tenant_id, assessment_id)
        self._audit(tenant_id, actor_id, "assessment.deleted", assessment_id, {})
        self._event("assessment.deleted", tenant_id, assessment_id, {})

    def start_attempt(self, tenant_id: str, assessment_id: str, request: AttemptStartRequest) -> AttemptResponse:
        self._assert_capability(tenant_id, "assessment.attempt")
        assessment = self.store.get_assessment(tenant_id, assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="assessment not found")
        if assessment.status not in {AssessmentStatus.PUBLISHED, AssessmentStatus.ACTIVE}:
            raise HTTPException(status_code=409, detail="assessment not available for attempts")

        attempt = AttemptRecord(
            attempt_id=str(uuid4()),
            tenant_id=tenant_id,
            assessment_id=assessment_id,
            learner_id=request.learner_id,
            started_at=self._now(),
            status=AttemptStatus.STARTED,
            exam_session_id=request.exam_session_id,
            isolation_key=request.isolation_key,
        )
        persisted = self.store.create_attempt(attempt)
        self.metrics.inc("attempts_started")
        self._audit(tenant_id, request.learner_id, "assessment.attempt_started", persisted.attempt_id, {"assessment_id": assessment_id})
        self._event("assessment.attempt_started", tenant_id, persisted.attempt_id, {"assessment_id": assessment_id})
        return self._to_attempt_response(persisted)

    def submit_attempt(self, tenant_id: str, attempt_id: str, request: SubmissionCreateRequest) -> SubmissionResponse:
        self._assert_capability(tenant_id, "assessment.attempt")
        attempt = self.store.get_attempt(tenant_id, attempt_id)
        if not attempt:
            raise HTTPException(status_code=404, detail="attempt not found")
        if attempt.status == AttemptStatus.GRADED:
            raise HTTPException(status_code=409, detail="graded attempt cannot accept submissions")

        submission = SubmissionRecord(
            submission_id=str(uuid4()),
            attempt_id=attempt_id,
            tenant_id=tenant_id,
            payload=request.payload,
            submitted_by=request.submitted_by,
            submitted_at=self._now(),
        )
        persisted_submission = self.store.save_submission(submission)
        updated_attempt = replace(attempt, status=AttemptStatus.SUBMITTED, submitted_at=self._now())
        self.store.update_attempt(updated_attempt)

        self.metrics.inc("submissions_recorded")
        self._audit(tenant_id, request.submitted_by, "assessment.submitted", attempt_id, {"submission_id": persisted_submission.submission_id})
        self._event("assessment.submitted", tenant_id, attempt_id, {"submission_id": persisted_submission.submission_id})
        return self._to_submission_response(persisted_submission)

    def grade_attempt(self, tenant_id: str, attempt_id: str, request: GradeAttemptRequest) -> AttemptResponse:
        self._assert_capability(tenant_id, "assessment.author")
        attempt = self.store.get_attempt(tenant_id, attempt_id)
        if not attempt:
            raise HTTPException(status_code=404, detail="attempt not found")
        if not self.store.list_submissions(tenant_id, attempt_id):
            raise HTTPException(status_code=409, detail="attempt cannot be graded before submission")

        graded = replace(
            attempt,
            status=AttemptStatus.GRADED,
            grading_result_id=request.grading_result_id,
            submitted_at=attempt.submitted_at or self._now(),
        )
        persisted = self.store.update_attempt(graded)
        self.metrics.inc("attempts_graded")
        self._audit(tenant_id, request.actor_id, "assessment.graded", attempt_id, {"grading_result_id": request.grading_result_id})
        self._event("assessment.graded", tenant_id, attempt_id, {"grading_result_id": request.grading_result_id})
        return self._to_attempt_response(persisted)

    def get_attempt(self, tenant_id: str, attempt_id: str) -> AttemptResponse:
        attempt = self.store.get_attempt(tenant_id, attempt_id)
        if not attempt:
            raise HTTPException(status_code=404, detail="attempt not found")
        return self._to_attempt_response(attempt)

    def list_attempts(self, tenant_id: str, assessment_id: str) -> list[AttemptResponse]:
        attempts = sorted(self.store.list_attempts(tenant_id, assessment_id), key=lambda item: item.started_at)
        return [self._to_attempt_response(item) for item in attempts]

    def _event(self, event_type: str, tenant_id: str, entity_id: str, payload: dict[str, object]) -> None:
        self.event_publisher.publish(
            DomainEvent(**build_event(
                event_type=event_type,
                tenant_id=tenant_id,
                correlation_id=ensure_correlation_id(None),
                payload=payload,
                metadata={"entity_id": entity_id, "producer": "assessment-service"},
            ).__dict__)
        )

    def _audit(self, tenant_id: str, actor_id: str, action: str, entity_id: str, details: dict[str, object]) -> None:
        self.audit_logger.log(
            {
                "tenant_id": tenant_id,
                "actor_id": actor_id,
                "action": action,
                "entity_type": "assessment",
                "entity_id": entity_id,
                "timestamp": self._now().isoformat(),
                "details": details,
            }
        )


    def _tenant_context(self, tenant_id: str) -> TenantEntitlementContext:
        tenant = tenant_contract_from_inputs(tenant_id=tenant_id)
        return TenantEntitlementContext(
            tenant_id=tenant.tenant_id,
            country_code=tenant.country_code,
            segment_id=tenant.segment_type,
            plan_type=tenant.plan_type,
            add_ons=tuple(tenant.addon_flags),
        )

    def _assert_capability(self, tenant_id: str, capability: str) -> None:
        if not self._entitlement_service.is_enabled(self._tenant_context(tenant_id), capability):
            raise HTTPException(status_code=403, detail=f"capability disabled: {capability}")

    @staticmethod
    def _to_assessment_response(record: AssessmentDefinition) -> AssessmentResponse:
        return AssessmentResponse(**asdict(record))

    @staticmethod
    def _to_attempt_response(record: AttemptRecord) -> AttemptResponse:
        return AttemptResponse(**asdict(record))

    @staticmethod
    def _to_submission_response(record: SubmissionRecord) -> SubmissionResponse:
        return SubmissionResponse(**asdict(record))
