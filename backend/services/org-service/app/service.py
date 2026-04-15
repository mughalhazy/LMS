from __future__ import annotations

from dataclasses import asdict

from fastapi import HTTPException

from .models import Department, Organization, ReparentAuditLog, Status, Team, utc_now
from .repository import InMemoryOrgRepository


class OrganizationService:
    def __init__(self, repo: InMemoryOrgRepository) -> None:
        self.repo = repo

    def _require_org(self, organization_id: str) -> Organization:
        org = self.repo.get_organization(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="organization not found")
        return org

    def _require_department(self, department_id: str) -> Department:
        dep = self.repo.get_department(department_id)
        if not dep:
            raise HTTPException(status_code=404, detail="department not found")
        return dep

    def _require_team(self, team_id: str) -> Team:
        team = self.repo.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="team not found")
        return team

    def create_organization(self, payload: dict) -> Organization:
        if payload.get("parent_organization_id"):
            self._require_org(payload["parent_organization_id"])
        org = Organization(**payload)
        self.repo.organizations[org.organization_id] = org
        if org.parent_organization_id:
            self.repo.org_children[org.parent_organization_id].add(org.organization_id)
        return org

    def create_department(self, payload: dict) -> Department:
        org = self._require_org(payload["organization_id"])
        if org.status != Status.ACTIVE:
            raise HTTPException(status_code=400, detail="cannot create department in inactive organization")
        for dep_id in self.repo.departments_by_org[org.organization_id]:
            dep = self.repo.departments[dep_id]
            if dep.name == payload["name"]:
                raise HTTPException(status_code=409, detail="department name must be unique within organization")

        if payload.get("parent_department_id"):
            parent = self._require_department(payload["parent_department_id"])
            if parent.organization_id != org.organization_id:
                raise HTTPException(status_code=400, detail="parent department must belong to same organization")

        dep = Department(**payload)
        self.repo.departments[dep.department_id] = dep
        self.repo.departments_by_org[dep.organization_id].add(dep.department_id)
        if dep.parent_department_id:
            self.repo.department_children[dep.parent_department_id].add(dep.department_id)
        return dep

    def create_team(self, payload: dict) -> Team:
        dep = self._require_department(payload["department_id"])
        if dep.status != Status.ACTIVE:
            raise HTTPException(status_code=400, detail="cannot create team in inactive department")
        for team_id in self.repo.teams_by_department[dep.department_id]:
            team = self.repo.teams[team_id]
            if team.name == payload["name"]:
                raise HTTPException(status_code=409, detail="team name must be unique within department")

        team = Team(**payload)
        self.repo.teams[team.team_id] = team
        self.repo.teams_by_department[team.department_id].add(team.team_id)
        return team

    def patch_organization(self, organization_id: str, changes: dict, actor_user_id: str) -> Organization:
        org = self._require_org(organization_id)
        if "parent_organization_id" in changes and changes["parent_organization_id"] != org.parent_organization_id:
            parent_id = changes["parent_organization_id"]
            if parent_id:
                self._require_org(parent_id)
            self.repo.reparent_audit_logs.append(
                ReparentAuditLog(
                    actor_user_id=actor_user_id,
                    entity_type="organization",
                    entity_id=organization_id,
                    old_parent_id=org.parent_organization_id,
                    new_parent_id=parent_id,
                )
            )
            if org.parent_organization_id:
                self.repo.org_children[org.parent_organization_id].discard(organization_id)
            if parent_id:
                self.repo.org_children[parent_id].add(organization_id)

        for key, value in changes.items():
            setattr(org, key, value)
        org.updated_at = utc_now()
        return org

    def patch_department(self, department_id: str, changes: dict, actor_user_id: str) -> Department:
        dep = self._require_department(department_id)

        if "parent_department_id" in changes and changes["parent_department_id"] != dep.parent_department_id:
            parent_id = changes["parent_department_id"]
            if parent_id:
                parent_dep = self._require_department(parent_id)
                if parent_dep.organization_id != dep.organization_id:
                    raise HTTPException(status_code=400, detail="parent department must be in same organization")
            self.repo.reparent_audit_logs.append(
                ReparentAuditLog(
                    actor_user_id=actor_user_id,
                    entity_type="department",
                    entity_id=department_id,
                    old_parent_id=dep.parent_department_id,
                    new_parent_id=parent_id,
                )
            )
            if dep.parent_department_id:
                self.repo.department_children[dep.parent_department_id].discard(dep.department_id)
            if parent_id:
                self.repo.department_children[parent_id].add(dep.department_id)

        for key, value in changes.items():
            setattr(dep, key, value)
        dep.updated_at = utc_now()
        return dep

    def patch_team(self, team_id: str, changes: dict, actor_user_id: str) -> Team:
        team = self._require_team(team_id)

        if "department_id" in changes and changes["department_id"] != team.department_id:
            new_department = self._require_department(changes["department_id"])
            self.repo.reparent_audit_logs.append(
                ReparentAuditLog(
                    actor_user_id=actor_user_id,
                    entity_type="team",
                    entity_id=team_id,
                    old_parent_id=team.department_id,
                    new_parent_id=new_department.department_id,
                )
            )
            self.repo.teams_by_department[team.department_id].discard(team_id)
            self.repo.teams_by_department[new_department.department_id].add(team_id)

        for key, value in changes.items():
            setattr(team, key, value)
        team.updated_at = utc_now()
        return team

    def deactivate_organization(self, organization_id: str, cascade: bool) -> Organization:
        org = self._require_org(organization_id)
        dep_ids = list(self.repo.departments_by_org[organization_id])

        has_active_children = any(self.repo.departments[d].status == Status.ACTIVE for d in dep_ids)
        if has_active_children and not cascade:
            raise HTTPException(status_code=400, detail="active child departments exist; use cascade=true")

        if cascade:
            for dep_id in dep_ids:
                dep = self.repo.departments[dep_id]
                dep.status = Status.INACTIVE
                dep.updated_at = utc_now()
                for team_id in self.repo.teams_by_department[dep_id]:
                    team = self.repo.teams[team_id]
                    team.status = Status.INACTIVE
                    team.updated_at = utc_now()

        org.status = Status.INACTIVE
        org.updated_at = utc_now()
        return org

    def hierarchy(self, organization_id: str) -> dict:
        org = self._require_org(organization_id)
        dep_ids = sorted(self.repo.departments_by_org[organization_id])
        departments = [self.repo.departments[d] for d in dep_ids]
        teams = []
        for dep in departments:
            for team_id in sorted(self.repo.teams_by_department[dep.department_id]):
                teams.append(self.repo.teams[team_id])

        return {
            "organization": asdict(org),
            "departments": [asdict(d) for d in departments],
            "teams": [asdict(t) for t in teams],
        }
