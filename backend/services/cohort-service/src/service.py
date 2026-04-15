from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from .models import (
    AuditEvent,
    Cohort,
    CohortMembership,
    CohortMilestoneDates,
    CohortSchedule,
    CohortSession,
    CohortStatus,
    DeliveryMode,
    MembershipState,
    SessionModality,
)
from .repository import InMemoryCohortRepository


class CohortServiceError(Exception):
    """Domain-specific exception."""


class CohortNotFoundError(CohortServiceError):
    """Domain-specific exception."""


class TenantScopeError(CohortServiceError):
    """Domain-specific exception."""


class InvalidLifecycleTransitionError(CohortServiceError):
    """Domain-specific exception."""


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
        self._get_tenant_cohort(tenant_id=tenant_id, cohort_id=cohort_id)
        override_flags = override_flags or {}

        assigned, skipped, failed = [], [], []
        waitlist_entries = []

        for learner_id in learner_ids:
            existing = self.repository.find_membership(cohort_id, learner_id)
            if existing and existing.state != MembershipState.REMOVED and not override_flags.get("allow_duplicates", False):
                skipped.append({"learner_id": learner_id, "reason": "duplicate_membership"})
                continue

            current_active_count = self.repository.active_membership_count(cohort_id)
            state = MembershipState.ACTIVE
            if current_active_count >= self._get_tenant_cohort(tenant_id=tenant_id, cohort_id=cohort_id).capacity:
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
        self._promote_waitlisted_member(cohort_id=cohort_id, tenant_id=tenant_id)
        self._audit(
            "CohortMemberRemoved",
            cohort_id,
            tenant_id,
            {"learner_id": learner_id, "removed_by": removed_by},
        )
        return {"cohort_membership_id": membership.cohort_membership_id, "state": membership.state.value}

    def update_schedule(
        self,
        *,
        tenant_id: str,
        cohort_id: str,
        session_plan: List[Dict],
        milestone_dates: Optional[Dict] = None,
        recurrence_rules: Optional[Dict] = None,
        holiday_blackouts: Optional[List[str]] = None,
        update_reason: str,
    ) -> Dict:
        cohort = self._get_tenant_cohort(tenant_id=tenant_id, cohort_id=cohort_id)
        if cohort.status == CohortStatus.ARCHIVED:
            raise CohortServiceError("cannot update schedule for archived cohort")

        parsed_sessions = self._parse_and_validate_sessions(
            session_plan=session_plan,
            cohort_start=cohort.start_date,
            cohort_end=cohort.end_date,
        )
        schedule = self.repository.get_schedule(cohort_id)
        version = 1 if schedule is None else schedule.schedule_version + 1

        new_schedule = CohortSchedule(
            cohort_id=cohort_id,
            tenant_id=tenant_id,
            session_plan=parsed_sessions,
            milestone_dates=self._parse_milestones(milestone_dates or {}),
            recurrence_rules=recurrence_rules,
            holiday_blackouts=holiday_blackouts or [],
            schedule_version=version,
            updated_at=datetime.utcnow(),
        )
        self.repository.upsert_schedule(new_schedule)

        conflict_warnings = self._build_schedule_conflicts(parsed_sessions)
        self._audit(
            "CohortScheduleUpdated",
            cohort_id,
            tenant_id,
            {"schedule_version": version, "update_reason": update_reason},
        )
        return {
            "published_cohort_calendar": {
                "cohort_id": cohort_id,
                "session_plan": [self._session_to_payload(s) for s in parsed_sessions],
                "milestone_dates": self._milestones_to_payload(new_schedule.milestone_dates),
                "recurrence_rules": new_schedule.recurrence_rules,
                "holiday_blackouts": new_schedule.holiday_blackouts,
            },
            "learner_notifications_queue": [
                {
                    "topic": "cohort.schedule.updated",
                    "cohort_id": cohort_id,
                    "schedule_version": version,
                }
            ],
            "updated_deadlines_by_member": {
                m.learner_id: self._milestones_to_payload(new_schedule.milestone_dates)
                for m in self.repository.list_memberships(cohort_id=cohort_id, state=MembershipState.ACTIVE.value)
            },
            "schedule_version": version,
            "conflict_warnings": conflict_warnings,
            "audit_event": "CohortScheduleUpdated",
        }

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

    def _promote_waitlisted_member(self, *, cohort_id: str, tenant_id: str) -> None:
        if self.repository.active_membership_count(cohort_id) >= self._get_tenant_cohort(tenant_id=tenant_id, cohort_id=cohort_id).capacity:
            return

        for membership in self.repository.list_memberships(cohort_id=cohort_id, state=MembershipState.WAITLISTED.value):
            promoted = replace(membership, state=MembershipState.ACTIVE)
            self.repository.update_membership(promoted)
            self._audit(
                "CohortMemberPromotedFromWaitlist",
                cohort_id,
                tenant_id,
                {"learner_id": promoted.learner_id},
            )
            return

    def _parse_and_validate_sessions(
        self,
        *,
        session_plan: List[Dict],
        cohort_start: datetime,
        cohort_end: datetime,
    ) -> List[CohortSession]:
        sessions = []
        seen_ids = set()
        for raw in sorted(session_plan, key=lambda value: value["start_at"]):
            start_at = raw["start_at"]
            end_at = raw["end_at"]
            if end_at <= start_at:
                raise CohortServiceError("session end_at must be after start_at")
            if start_at < cohort_start or end_at > cohort_end:
                raise CohortServiceError("session must be within cohort start/end")
            if raw["session_id"] in seen_ids:
                raise CohortServiceError(f"duplicate session_id: {raw['session_id']}")
            seen_ids.add(raw["session_id"])
            sessions.append(
                CohortSession(
                    session_id=raw["session_id"],
                    title=raw["title"],
                    start_at=start_at,
                    end_at=end_at,
                    instructor_id=raw["instructor_id"],
                    modality=SessionModality(raw["modality"]),
                )
            )
        return sessions

    def _build_schedule_conflicts(self, sessions: List[CohortSession]) -> List[Dict]:
        warnings = []
        for index, current in enumerate(sessions):
            for compare in sessions[index + 1 :]:
                overlaps = current.start_at < compare.end_at and current.end_at > compare.start_at
                if overlaps and current.instructor_id == compare.instructor_id:
                    warnings.append(
                        {
                            "type": "instructor_overlap",
                            "session_id": current.session_id,
                            "conflicts_with": compare.session_id,
                            "instructor_id": current.instructor_id,
                        }
                    )
                if overlaps and current.start_at.tzinfo != compare.start_at.tzinfo:
                    warnings.append(
                        {
                            "type": "timezone_collision",
                            "session_id": current.session_id,
                            "conflicts_with": compare.session_id,
                        }
                    )
        return warnings

    def _parse_milestones(self, milestone_dates: Dict) -> CohortMilestoneDates:
        return CohortMilestoneDates(
            enrollment_cutoff=milestone_dates.get("enrollment_cutoff"),
            assignment_due_dates=milestone_dates.get("assignment_due_dates", {}),
            assessments=milestone_dates.get("assessments", {}),
        )

    def _session_to_payload(self, session: CohortSession) -> Dict:
        return {
            "session_id": session.session_id,
            "title": session.title,
            "start_at": session.start_at.isoformat(),
            "end_at": session.end_at.isoformat(),
            "instructor_id": session.instructor_id,
            "modality": session.modality.value,
        }

    def _milestones_to_payload(self, milestones: CohortMilestoneDates) -> Dict:
        return {
            "enrollment_cutoff": milestones.enrollment_cutoff.isoformat() if milestones.enrollment_cutoff else None,
            "assignment_due_dates": {
                key: value.isoformat() for key, value in milestones.assignment_due_dates.items()
            },
            "assessments": {key: value.isoformat() for key, value in milestones.assessments.items()},
        }
