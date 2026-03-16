from __future__ import annotations

from collections import defaultdict

from .models import (
    AuthorizationDecisionLog,
    PermissionDefinition,
    PolicyRule,
    RoleDefinition,
    SubjectRoleAssignment,
)


class InMemoryRBACStore:
    """Tenant-partitioned storage. No cross-tenant mutable writes."""

    def __init__(self) -> None:
        self._roles: dict[str, dict[str, RoleDefinition]] = defaultdict(dict)
        self._role_permissions: dict[str, dict[str, list[str]]] = defaultdict(dict)
        self._assignments: dict[str, dict[str, SubjectRoleAssignment]] = defaultdict(dict)
        self._policy_rules: dict[str, dict[str, PolicyRule]] = defaultdict(dict)
        self._decision_logs: dict[str, list[AuthorizationDecisionLog]] = defaultdict(list)
        self._permissions = self._seed_permission_catalog()

    @staticmethod
    def _seed_permission_catalog() -> dict[str, PermissionDefinition]:
        seeded = [
            PermissionDefinition(permission_key="audit.view_tenant", resource_type="audit", action="view", risk_tier="moderate"),
            PermissionDefinition(permission_key="tenant.settings.manage", resource_type="tenant", action="manage", risk_tier="high"),
            PermissionDefinition(permission_key="course.publish", resource_type="course", action="publish", risk_tier="high"),
            PermissionDefinition(permission_key="course.view", resource_type="course", action="view", risk_tier="low"),
        ]
        return {p.permission_key: p for p in seeded}

    def create_role(self, role: RoleDefinition) -> RoleDefinition:
        self._roles[role.tenant_id][role.role_id] = role
        self._role_permissions[role.tenant_id][role.role_id] = []
        return role

    def list_roles(self, tenant_id: str) -> list[RoleDefinition]:
        return list(self._roles[tenant_id].values())

    def get_role(self, tenant_id: str, role_id: str) -> RoleDefinition | None:
        return self._roles[tenant_id].get(role_id)

    def update_role(self, role: RoleDefinition) -> RoleDefinition:
        self._roles[role.tenant_id][role.role_id] = role
        return role

    def list_permissions(self) -> list[PermissionDefinition]:
        return list(self._permissions.values())

    def put_role_permissions(self, tenant_id: str, role_id: str, permission_keys: list[str]) -> None:
        self._role_permissions[tenant_id][role_id] = permission_keys

    def get_role_permissions(self, tenant_id: str, role_id: str) -> list[str]:
        return self._role_permissions[tenant_id].get(role_id, [])

    def create_assignment(self, assignment: SubjectRoleAssignment) -> SubjectRoleAssignment:
        self._assignments[assignment.tenant_id][assignment.assignment_id] = assignment
        return assignment

    def list_assignments(self, tenant_id: str) -> list[SubjectRoleAssignment]:
        return list(self._assignments[tenant_id].values())

    def get_assignment(self, tenant_id: str, assignment_id: str) -> SubjectRoleAssignment | None:
        return self._assignments[tenant_id].get(assignment_id)

    def update_assignment(self, assignment: SubjectRoleAssignment) -> SubjectRoleAssignment:
        self._assignments[assignment.tenant_id][assignment.assignment_id] = assignment
        return assignment

    def create_policy_rule(self, rule: PolicyRule) -> PolicyRule:
        self._policy_rules[rule.tenant_id][rule.policy_rule_id] = rule
        return rule

    def list_policy_rules(self, tenant_id: str) -> list[PolicyRule]:
        return sorted(self._policy_rules[tenant_id].values(), key=lambda r: r.priority, reverse=True)

    def get_policy_rule(self, tenant_id: str, rule_id: str) -> PolicyRule | None:
        return self._policy_rules[tenant_id].get(rule_id)

    def update_policy_rule(self, rule: PolicyRule) -> PolicyRule:
        self._policy_rules[rule.tenant_id][rule.policy_rule_id] = rule
        return rule

    def log_decision(self, log: AuthorizationDecisionLog) -> None:
        self._decision_logs[log.tenant_id].append(log)

    def list_decision_logs(self, tenant_id: str) -> list[AuthorizationDecisionLog]:
        return self._decision_logs[tenant_id]
