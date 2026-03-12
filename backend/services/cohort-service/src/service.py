from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from .models import (
    AuditEvent,
    Cohort,
    CohortMembership,
    CohortStatus,
    DeliveryMode,
    MembershipState,
)
from .repository import InMemoryCohortRepository


class CohortServiceError(Exception):
    pass


class CohortNotFoundError(CohortServiceError):
    pass


class TenantScopeError(CohortServiceError):
    pass


class InvalidLifecycleTransitionError(CohortServiceError):
    pass


class CohortService:
    _valid_lifecycle_transitions = {
        CohortStatus.DRAFT: {CohortStatus.SCHEDULED, CohortStatus.ACTIVE, CohortStatus.ARCHIVED},
        CohortStatus.SCHEDULED: {CohortStatus.ACTIVE, CohortStatus.ARCHIVED},
        CohortStatus.ACTIVE: {CohortStatus.COMPLETED, CohortStatus.ARCHIVED},
        CohortStatus.COMPLETED: {CohortStatus.ARCHIVED},
        CohortStatus.ARCHIVED: set(),
    }

    def __init__(self, repository: InMemoryCohortRepository) -> None:
        self.repository = repository

    def create_cohort(
        self,
        *,
        tenant_id: str,
        program_id: str,
        cohort_name: str,
        description: str,
        start_date: datetime,
        end_date: datetime,
        capacity: int,
        delivery_mode: str,
        timezone: str,
        facilitator_ids: List[str],
        enrollment_rules: Optional[Dict] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict:
        if end_date <= start_date:
            raise CohortServiceError("cohort end_date must be after start_date")
        if capacity < 1:
            raise CohortServiceError("cohort capacity must be at least 1")

        now = datetime.utcnow()
        initial_status = CohortStatus.SCHEDULED if start_date > now else CohortStatus.ACTIVE
        cohort = Cohort(
            cohort_id=str(uuid4()),
            tenant_id=tenant_id,
            program_id=program_id,
            cohort_name=cohort_name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            capacity=capacity,
            delivery_mode=DeliveryMode(delivery_mode),
            timezone=timezone,
            facilitator_ids=facilitator_ids,
            enrollment_rules=enrollment_rules,
            metadata=metadata or {},
            status=initial_status,
        )
        self.repository.create_cohort(cohort)
        self._audit("CohortCreated", cohort.cohort_id, tenant_id, {"status": cohort.status.value})

        return {
            "cohort_id": cohort.cohort_id,
            "cohort_status": cohort.status.value,
            "normalized_schedule_window": {
                "start_date": cohort.start_date.isoformat(),
                "end_date": cohort.end_date.isoformat(),
                "timezone": cohort.timezone,
            },
            "assigned_facilitators": cohort.facilitator_ids,
            "enrollment_rule_set_id": (cohort.enrollment_rules or {}).get("rule_set_id"),
            "audit_event": "CohortCreated",
        }

    def transition_lifecycle(self, *, tenant_id: str, cohort_id: str, target_status: str, reason: str) -> Dict:
        cohort = self._get_tenant_cohort(tenant_id=tenant_id, cohort_id=cohort_id)
        target = CohortStatus(target_status)
        allowed = self._valid_lifecycle_transitions[cohort.status]
        if target not in allowed:
            raise InvalidLifecycleTransitionError(f"cannot transition {cohort.status.value} -> {target.value}")

        previous_status = cohort.status
        cohort = replace(cohort, status=target, updated_at=datetime.utcnow())
        self.repository.update_cohort(cohort)
        self._audit(
            "CohortLifecycleChanged",
            cohort_id,
            tenant_id,
            {"from": previous_status.value, "to": target.value, "reason": reason},
        )
        return {"cohort_id": cohort_id, "cohort_status": target.value, "reason": reason}

    def assign_members(
        self,
        *,
        tenant_id: str,
        cohort_id: str,
        assignment_mode: str,
        learner_ids: List[str],
        assigned_by: str,
        effective_date: datetime,
        override_flags: Optional[Dict[str, bool]] = None,
    ) -> Dict:
        cohort = self._get_tenant_cohort(tenant_id=tenant_id, cohort_id=cohort_id)
        override_flags = override_flags or {}

        assigned, skipped, failed = [], [], []
        waitlist_entries = []

        for learner_id in learner_ids:
            existing = self.repository.find_membership(cohort_id, learner_id)
            if existing and not override_flags.get("allow_duplicates", False):
                skipped.append({"learner_id": learner_id, "reason": "duplicate_membership"})
                continue

            current_active_count = self.repository.active_membership_count(cohort_id)
            state = MembershipState.ACTIVE
            if current_active_count >= cohort.capacity:
                state = MembershipState.WAITLISTED
                waitlist_entries.append({"learner_id": learner_id})

            membership = CohortMembership(
                cohort_membership_id=str(uuid4()),
                cohort_id=cohort_id,
                tenant_id=tenant_id,
                learner_id=learner_id,
                state=state,
                assigned_by=assigned_by,
                effective_date=effective_date,
            )
            self.repository.add_membership(membership)
            assigned.append(
                {
                    "cohort_membership_id": membership.cohort_membership_id,
                    "learner_id": learner_id,
                    "state": membership.state.value,
                }
            )

        summary = {"assigned": len(assigned), "skipped": len(skipped), "failed": len(failed)}
        conflict_report = {
            "capacity": "reached" if waitlist_entries else "ok",
            "eligibility": "not_evaluated",
            "duplicates": skipped,
        }

        self._audit(
            "CohortMembersAssigned",
            cohort_id,
            tenant_id,
            {"assignment_mode": assignment_mode, "summary": summary},
        )
        return {
            "membership_records": assigned,
            "assignment_summary": summary,
            "conflict_report": conflict_report,
            "waitlist_entries": waitlist_entries,
            "audit_event": "CohortMembersAssigned",
        }

    def remove_member(self, *, tenant_id: str, cohort_id: str, learner_id: str, removed_by: str) -> Dict:
        self._get_tenant_cohort(tenant_id=tenant_id, cohort_id=cohort_id)
        membership = self.repository.find_membership(cohort_id, learner_id)
        if membership is None:
            raise CohortServiceError("membership not found")
        if membership.tenant_id != tenant_id:
            raise TenantScopeError("cross-tenant membership mutation is forbidden")

        membership = replace(membership, state=MembershipState.REMOVED)
        self.repository.update_membership(membership)
        self._audit(
            "CohortMemberRemoved",
            cohort_id,
            tenant_id,
            {"learner_id": learner_id, "removed_by": removed_by},
        )
        return {"cohort_membership_id": membership.cohort_membership_id, "state": membership.state.value}

    def list_tenant_cohorts(self, tenant_id: str) -> List[Dict]:
        return [
            {
                "cohort_id": c.cohort_id,
                "program_id": c.program_id,
                "cohort_name": c.cohort_name,
                "status": c.status.value,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat(),
            }
            for c in self.repository.list_tenant_cohorts(tenant_id)
        ]

    def _get_tenant_cohort(self, *, tenant_id: str, cohort_id: str) -> Cohort:
        cohort = self.repository.get_cohort(cohort_id)
        if cohort is None:
            raise CohortNotFoundError("cohort not found")
        if cohort.tenant_id != tenant_id:
            raise TenantScopeError("cross-tenant cohort access is forbidden")
        return cohort

    def _audit(self, event_type: str, entity_id: str, tenant_id: str, payload: Dict) -> None:
        self.repository.append_event(
            AuditEvent(event_type=event_type, entity_id=entity_id, tenant_id=tenant_id, payload=payload)
        )
