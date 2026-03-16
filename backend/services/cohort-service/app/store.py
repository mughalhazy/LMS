from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .models import CohortRecord, MembershipRecord


class CohortStore(Protocol):
    def save_cohort(self, cohort: CohortRecord) -> CohortRecord: ...

    def get_cohort(self, tenant_id: str, cohort_id: str) -> CohortRecord | None: ...

    def list_cohorts(self, tenant_id: str) -> list[CohortRecord]: ...

    def delete_cohort(self, tenant_id: str, cohort_id: str) -> None: ...

    def save_membership(self, membership: MembershipRecord) -> MembershipRecord: ...

    def remove_membership(self, tenant_id: str, cohort_id: str, membership_id: str) -> None: ...

    def list_memberships(self, tenant_id: str, cohort_id: str) -> list[MembershipRecord]: ...


@dataclass
class InMemoryCohortStore:
    cohorts: dict[str, CohortRecord] = field(default_factory=dict)
    tenant_to_cohort_ids: dict[str, set[str]] = field(default_factory=dict)
    memberships: dict[str, MembershipRecord] = field(default_factory=dict)
    cohort_to_membership_ids: dict[str, set[str]] = field(default_factory=dict)

    def save_cohort(self, cohort: CohortRecord) -> CohortRecord:
        self.cohorts[cohort.cohort_id] = cohort
        self.tenant_to_cohort_ids.setdefault(cohort.tenant_id, set()).add(cohort.cohort_id)
        return cohort

    def get_cohort(self, tenant_id: str, cohort_id: str) -> CohortRecord | None:
        cohort = self.cohorts.get(cohort_id)
        if not cohort or cohort.tenant_id != tenant_id:
            return None
        return cohort

    def list_cohorts(self, tenant_id: str) -> list[CohortRecord]:
        ids = self.tenant_to_cohort_ids.get(tenant_id, set())
        return [self.cohorts[cohort_id] for cohort_id in ids]

    def delete_cohort(self, tenant_id: str, cohort_id: str) -> None:
        cohort = self.get_cohort(tenant_id, cohort_id)
        if not cohort:
            return
        del self.cohorts[cohort_id]
        self.tenant_to_cohort_ids.get(tenant_id, set()).discard(cohort_id)

    def save_membership(self, membership: MembershipRecord) -> MembershipRecord:
        self.memberships[membership.membership_id] = membership
        self.cohort_to_membership_ids.setdefault(membership.cohort_id, set()).add(membership.membership_id)
        return membership

    def remove_membership(self, tenant_id: str, cohort_id: str, membership_id: str) -> None:
        membership = self.memberships.get(membership_id)
        if not membership:
            return
        if membership.tenant_id != tenant_id or membership.cohort_id != cohort_id:
            return
        del self.memberships[membership_id]
        self.cohort_to_membership_ids.get(cohort_id, set()).discard(membership_id)

    def list_memberships(self, tenant_id: str, cohort_id: str) -> list[MembershipRecord]:
        membership_ids = self.cohort_to_membership_ids.get(cohort_id, set())
        records = [self.memberships[membership_id] for membership_id in membership_ids]
        return [record for record in records if record.tenant_id == tenant_id]
