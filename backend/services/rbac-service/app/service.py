from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from .contracts import EventPublisher, ObservabilityHook, RBACStorage
from .events import (
    RBAC_ASSIGNMENT_CREATED,
    RBAC_ASSIGNMENT_REVOKED,
    RBAC_POLICY_RULE_CHANGED,
    RBAC_ROLE_CREATED,
    RBAC_ROLE_UPDATED,
)
from .models import AuthorizationDecisionLog, PolicyRule, RoleDefinition, RoleStatus, SubjectRoleAssignment
from .schemas import (
    AssignmentCreateRequest,
    AssignmentUpdateRequest,
    AuthorizeRequest,
    AuthorizeResponse,
    PolicyRuleCreateRequest,
    PolicyRuleUpdateRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)


class RBACService:
    def __init__(self, storage: RBACStorage, publisher: EventPublisher, observability: ObservabilityHook) -> None:
        self.storage = storage
        self.publisher = publisher
        self.observability = observability

    def create_role(self, tenant_id: str, request: RoleCreateRequest) -> RoleDefinition:
        role = RoleDefinition(tenant_id=tenant_id, **request.model_dump())
        saved = self.storage.create_role(role)
        self.publisher.publish(RBAC_ROLE_CREATED, tenant_id, {"role_id": saved.role_id, "role_key": saved.role_key})
        self.observability.increment("rbac_role_create_total", {"tenant_id": tenant_id})
        return saved

    def list_roles(self, tenant_id: str):
        return self.storage.list_roles(tenant_id)

    def update_role(self, tenant_id: str, role_id: str, request: RoleUpdateRequest) -> RoleDefinition:
        role = self._require_role(tenant_id, role_id)
        payload = request.model_dump(exclude_none=True)
        for key, value in payload.items():
            if key == "status":
                role.status = RoleStatus(value)
            else:
                setattr(role, key, value)
        role.version += 1
        role.updated_at = datetime.now(timezone.utc)
        saved = self.storage.update_role(role)
        self.publisher.publish(RBAC_ROLE_UPDATED, tenant_id, {"role_id": role_id, "version": saved.version})
        return saved

    def replace_role_permissions(self, tenant_id: str, role_id: str, permission_keys: list[str]) -> None:
        self._require_role(tenant_id, role_id)
        known_permissions = {p.permission_key for p in self.storage.list_permissions()}
        unknown = sorted(set(permission_keys) - known_permissions)
        if unknown:
            raise HTTPException(status_code=400, detail={"error": "unknown_permissions", "permission_keys": unknown})
        self.storage.put_role_permissions(tenant_id, role_id, permission_keys)

    def create_assignment(self, tenant_id: str, request: AssignmentCreateRequest) -> SubjectRoleAssignment:
        self._require_role(tenant_id, request.role_id)
        assignment = SubjectRoleAssignment(
            tenant_id=tenant_id,
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            role_id=request.role_id,
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            starts_at=request.starts_at or datetime.now(timezone.utc),
            ends_at=request.ends_at,
            source=request.source,
            created_by=request.created_by,
        )
        saved = self.storage.create_assignment(assignment)
        self.publisher.publish(RBAC_ASSIGNMENT_CREATED, tenant_id, {"assignment_id": saved.assignment_id, "subject_id": saved.subject_id})
        return saved

    def list_assignments(self, tenant_id: str):
        return self.storage.list_assignments(tenant_id)

    def update_assignment(self, tenant_id: str, assignment_id: str, request: AssignmentUpdateRequest) -> SubjectRoleAssignment:
        assignment = self._require_assignment(tenant_id, assignment_id)
        if request.ends_at is not None:
            assignment.ends_at = request.ends_at
        if request.scope_type is not None:
            assignment.scope_type = request.scope_type
        if request.scope_id is not None:
            assignment.scope_id = request.scope_id
        return self.storage.update_assignment(assignment)

    def revoke_assignment(self, tenant_id: str, assignment_id: str) -> None:
        assignment = self._require_assignment(tenant_id, assignment_id)
        assignment.revoked_at = datetime.now(timezone.utc)
        self.storage.update_assignment(assignment)
        self.publisher.publish(RBAC_ASSIGNMENT_REVOKED, tenant_id, {"assignment_id": assignment_id})

    def effective_permissions(self, tenant_id: str, subject_type: str, subject_id: str) -> list[str]:
        now = datetime.now(timezone.utc)
        role_ids = {
            a.role_id
            for a in self.storage.list_assignments(tenant_id)
            if a.subject_type.value == subject_type and a.subject_id == subject_id and a.revoked_at is None and a.starts_at <= now and (a.ends_at is None or a.ends_at >= now)
        }
        permissions: set[str] = set()
        for role_id in role_ids:
            permissions.update(self.storage.get_role_permissions(tenant_id, role_id))
        return sorted(permissions)

    def create_policy_rule(self, tenant_id: str, request: PolicyRuleCreateRequest) -> PolicyRule:
        rule = PolicyRule(tenant_id=tenant_id, rule_type=request.rule_type, expression=request.expression, priority=request.priority)
        saved = self.storage.create_policy_rule(rule)
        self.publisher.publish(RBAC_POLICY_RULE_CHANGED, tenant_id, {"policy_rule_id": saved.policy_rule_id, "action": "created"})
        return saved

    def list_policy_rules(self, tenant_id: str):
        return self.storage.list_policy_rules(tenant_id)

    def update_policy_rule(self, tenant_id: str, rule_id: str, request: PolicyRuleUpdateRequest) -> PolicyRule:
        rule = self._require_policy_rule(tenant_id, rule_id)
        payload = request.model_dump(exclude_none=True)
        for key, value in payload.items():
            setattr(rule, key, value)
        saved = self.storage.update_policy_rule(rule)
        self.publisher.publish(RBAC_POLICY_RULE_CHANGED, tenant_id, {"policy_rule_id": saved.policy_rule_id, "action": "updated"})
        return saved

    def disable_policy_rule(self, tenant_id: str, rule_id: str) -> None:
        rule = self._require_policy_rule(tenant_id, rule_id)
        rule.enabled = False
        self.storage.update_policy_rule(rule)
        self.publisher.publish(RBAC_POLICY_RULE_CHANGED, tenant_id, {"policy_rule_id": rule_id, "action": "disabled"})

    def authorize(self, tenant_id: str, request: AuthorizeRequest, correlation_id: str | None = None) -> AuthorizeResponse:
        permissions = self.effective_permissions(tenant_id, request.subject.type.value, request.subject.id)
        reason_codes = ["default_deny"]
        trace = []
        decision = "deny"

        for rule in self.storage.list_policy_rules(tenant_id):
            if not rule.enabled:
                continue
            if rule.rule_type.value == "explicit_deny" and rule.expression.get("permission_key") == request.permission_key:
                reason_codes = ["explicit_deny_rule"]
                trace.append(f"policy:{rule.policy_rule_id}")
                decision = "deny"
                break

        if request.permission_key in permissions and reason_codes == ["default_deny"]:
            decision = "allow"
            reason_codes = ["role_permission_granted"]
            trace.append("role_binding")

        self.storage.log_decision(
            AuthorizationDecisionLog(
                tenant_id=tenant_id,
                principal_subject=f"{request.subject.type.value}:{request.subject.id}",
                permission_key=request.permission_key,
                resource_type=request.resource.type,
                resource_id=request.resource.id,
                decision=decision,
                reason_codes=reason_codes,
                policy_trace=trace,
                correlation_id=correlation_id,
            )
        )
        self.observability.increment("rbac_authorize_total", {"tenant_id": tenant_id, "decision": decision})
        return AuthorizeResponse(decision=decision, reason_codes=reason_codes, policy_trace=trace)

    def _require_role(self, tenant_id: str, role_id: str) -> RoleDefinition:
        role = self.storage.get_role(tenant_id, role_id)
        if not role:
            raise HTTPException(status_code=404, detail="role_not_found")
        return role

    def _require_assignment(self, tenant_id: str, assignment_id: str) -> SubjectRoleAssignment:
        assignment = self.storage.get_assignment(tenant_id, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="assignment_not_found")
        return assignment

    def _require_policy_rule(self, tenant_id: str, rule_id: str) -> PolicyRule:
        rule = self.storage.get_policy_rule(tenant_id, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="policy_rule_not_found")
        return rule
