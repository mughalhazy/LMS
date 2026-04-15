from __future__ import annotations

from collections import defaultdict
from typing import Optional

from .models import Department, Organization, ReparentAuditLog, Team


class InMemoryOrgRepository:
    def __init__(self) -> None:
        self.organizations: dict[str, Organization] = {}
        self.departments: dict[str, Department] = {}
        self.teams: dict[str, Team] = {}
        self.department_children: dict[str, set[str]] = defaultdict(set)
        self.org_children: dict[str, set[str]] = defaultdict(set)
        self.teams_by_department: dict[str, set[str]] = defaultdict(set)
        self.departments_by_org: dict[str, set[str]] = defaultdict(set)
        self.reparent_audit_logs: list[ReparentAuditLog] = []

    def get_organization(self, organization_id: str) -> Optional[Organization]:
        return self.organizations.get(organization_id)

    def get_department(self, department_id: str) -> Optional[Department]:
        return self.departments.get(department_id)

    def get_team(self, team_id: str) -> Optional[Team]:
        return self.teams.get(team_id)
