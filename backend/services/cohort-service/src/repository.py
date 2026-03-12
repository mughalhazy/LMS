from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Optional

from .models import AuditEvent, Cohort, CohortMembership


class InMemoryCohortRepository:
    def __init__(self) -> None:
        self._cohorts: Dict[str, Cohort] = {}
        self._memberships: Dict[str, CohortMembership] = {}
        self._events: List[AuditEvent] = []

    def create_cohort(self, cohort: Cohort) -> Cohort:
        self._cohorts[cohort.cohort_id] = cohort
        return cohort

    def get_cohort(self, cohort_id: str) -> Optional[Cohort]:
        cohort = self._cohorts.get(cohort_id)
        return replace(cohort) if cohort else None

    def update_cohort(self, cohort: Cohort) -> Cohort:
        self._cohorts[cohort.cohort_id] = cohort
        return cohort

    def list_tenant_cohorts(self, tenant_id: str) -> List[Cohort]:
        return [replace(c) for c in self._cohorts.values() if c.tenant_id == tenant_id]

    def add_membership(self, membership: CohortMembership) -> CohortMembership:
        self._memberships[membership.cohort_membership_id] = membership
        return membership

    def update_membership(self, membership: CohortMembership) -> CohortMembership:
        self._memberships[membership.cohort_membership_id] = membership
        return membership

    def find_membership(self, cohort_id: str, learner_id: str) -> Optional[CohortMembership]:
        for membership in self._memberships.values():
            if membership.cohort_id == cohort_id and membership.learner_id == learner_id:
                return replace(membership)
        return None

    def list_memberships(self, cohort_id: str, state: Optional[str] = None) -> List[CohortMembership]:
        records = [m for m in self._memberships.values() if m.cohort_id == cohort_id]
        if state:
            records = [m for m in records if m.state.value == state]
        return [replace(m) for m in records]

    def active_membership_count(self, cohort_id: str) -> int:
        return len([m for m in self._memberships.values() if m.cohort_id == cohort_id and m.state.value == "active"])

    def append_event(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_events(self) -> List[AuditEvent]:
        return [replace(e) for e in self._events]
