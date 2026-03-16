from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4

from .audit import AuditLogger
from .models import (
    Assignment,
    AssignmentCreate,
    AuthorizationAuditEvent,
    AuthorizeDecision,
    Permission,
    Role,
    RolePermission,
    ScopeType,
    SubjectType,
)

ROLE_DEFINITIONS: dict[str, tuple[str, list[str]]] = {
    "platform-super-admin": (
        "Platform Super Admin",
        [
            "tenant.create",
            "tenant.update",
            "tenant.suspend",
            "tenant.delete",
            "tenant.view_all",
            "platform.config.manage",
            "audit.view_all",
            "support.impersonate_readonly",
        ],
    ),
    "tenant-admin": (
        "Tenant Admin",
        [
            "tenant.settings.manage",
            "org.user.invite",
            "org.user.disable",
            "org.role.assign",
            "catalog.manage",
            "program.manage",
            "report.view_tenant",
            "integration.manage_tenant",
        ],
    ),
    "compliance-officer": (
        "Compliance Officer",
        [
            "audit.view_tenant",
            "audit.export",
            "policy.view",
            "policy.enforce.override_with_reason",
            "report.compliance.view",
        ],
    ),
    "instructor": (
        "Instructor",
        [
            "course.create",
            "course.update_owned",
            "course.publish_owned",
            "content.upload",
            "assessment.create_owned",
            "grade.manage_owned",
            "learner.progress.view_assigned",
        ],
    ),
    "teaching-assistant": (
        "Teaching Assistant",
        [
            "course.update_assigned",
            "assessment.grade_assigned",
            "learner.progress.view_assigned",
            "discussion.moderate_assigned",
        ],
    ),
    "learner": (
        "Learner",
        [
            "course.view_enrolled",
            "content.consume_enrolled",
            "assessment.submit_enrolled",
            "grade.view_self",
            "certificate.view_self",
        ],
    ),
    "hr-people-manager": (
        "HR/People Manager",
        [
            "learner.assign_training",
            "learner.progress.view_team",
            "report.team_completion.view",
            "skill.gap.view_team",
        ],
    ),
    "external-auditor": (
        "External Auditor (Read Only)",
        [
            "audit.view_scoped",
            "report.compliance.view_scoped",
            "evidence.download_scoped",
        ],
    ),
    "service-account": (
        "Service Account (Integration)",
        [
            "api.client_credentials.use",
            "user.provision",
            "enrollment.sync",
            "report.extract_scoped",
        ],
    ),
}

CONFLICTING_ROLE_PAIRS = {
    frozenset({"tenant-admin", "external-auditor"}),
}


class InMemoryRBACStore:
    def __init__(self) -> None:
        self.roles: dict[str, Role] = {}
        self.permissions: dict[str, Permission] = {}
        self.role_permissions: list[RolePermission] = []
        self.assignments: dict[str, Assignment] = {}
        self.audit_log: list[AuthorizationAuditEvent] = []
        self._audit_logger = AuditLogger("rbac.audit")
        self._seed()

    def _seed(self) -> None:
        for role_id, (display_name, perms) in ROLE_DEFINITIONS.items():
            self.roles[role_id] = Role(
                role_id=role_id,
                role_name=display_name,
                description=f"Default LMS role for {display_name}.",
            )
            for permission_action in perms:
                permission_id = permission_action.replace(".", "_")
                if permission_id not in self.permissions:
                    resource_type = permission_action.split(".", maxsplit=1)[0]
                    self.permissions[permission_id] = Permission(
                        permission_id=permission_id,
                        action=permission_action,
                        resource_type=resource_type,
                    )
                self.role_permissions.append(
                    RolePermission(role_id=role_id, permission_id=permission_id)
                )

    def list_roles(self) -> list[Role]:
        return list(self.roles.values())

    def list_permissions(self) -> list[Permission]:
        return list(self.permissions.values())

    def list_assignments(self) -> list[Assignment]:
        return list(self.assignments.values())

    def create_assignment(self, payload: AssignmentCreate) -> Assignment:
        if payload.role_id not in self.roles:
            raise ValueError(f"Unknown role_id: {payload.role_id}")

        existing_roles = {
            a.role_id
            for a in self.assignments.values()
            if a.subject_id == payload.subject_id and self._active(a)
        }
        for existing_role in existing_roles:
            if frozenset({existing_role, payload.role_id}) in CONFLICTING_ROLE_PAIRS:
                raise ValueError(
                    f"Separation-of-duties conflict between {existing_role} and {payload.role_id}"
                )

        assignment_id = str(uuid4())
        created = Assignment(
            assignment_id=assignment_id,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            role_id=payload.role_id,
            scope_type=payload.scope_type,
            scope_id=payload.scope_id,
            starts_at=payload.starts_at or datetime.now(timezone.utc),
            ends_at=payload.ends_at,
            assigned_by=payload.assigned_by,
            assignment_model=payload.assignment_model,
        )
        self.assignments[assignment_id] = created
        self._audit_logger.log(
            event_type="rbac.role.assignment.changed",
            tenant_id=created.scope_id if created.scope_type.value == "tenant" else "platform",
            actor_id=created.assigned_by,
            details={"subject_id": created.subject_id, "role_id": created.role_id, "scope_type": created.scope_type.value, "scope_id": created.scope_id},
        )
        return created

    def effective_permissions(
        self,
        principal_id: str,
        principal_type: SubjectType,
        scope_type: ScopeType,
        scope_id: str,
    ) -> list[str]:
        active = [
            a
            for a in self.assignments.values()
            if a.subject_id == principal_id
            and a.subject_type == principal_type
            and self._active(a)
            and self._scope_matches(a.scope_type, a.scope_id, scope_type, scope_id)
        ]
        role_ids = {a.role_id for a in active}
        perm_ids = [
            rp.permission_id for rp in self.role_permissions if rp.role_id in role_ids
        ]
        return sorted({self.permissions[pid].action for pid in perm_ids})

    def authorize(
        self,
        principal_id: str,
        principal_type: SubjectType,
        permission: str,
        scope_type: ScopeType,
        scope_id: str,
        correlation_id: str | None = None,
    ) -> AuthorizeDecision:
        perms = self.effective_permissions(
            principal_id=principal_id,
            principal_type=principal_type,
            scope_type=scope_type,
            scope_id=scope_id,
        )
        allowed = permission in perms
        decision = AuthorizeDecision(
            decision="ALLOW" if allowed else "DENY",
            reason="permission_granted" if allowed else "default_deny",
            effective_permissions=perms,
        )
        self.audit_log.append(
            AuthorizationAuditEvent(
                event_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                principal=principal_id,
                action=permission,
                resource=permission.split(".", maxsplit=1)[0],
                scope=f"{scope_type.value}:{scope_id}",
                decision=decision.decision,
                reason=decision.reason,
                correlation_id=correlation_id,
            )
        )
        return decision

    def list_audit_events(self) -> Iterable[AuthorizationAuditEvent]:
        return self.audit_log

    @staticmethod
    def _active(assignment: Assignment) -> bool:
        now = datetime.now(timezone.utc)
        if assignment.starts_at > now:
            return False
        if assignment.ends_at and assignment.ends_at < now:
            return False
        return True

    @staticmethod
    def _scope_matches(
        assignment_scope_type: ScopeType,
        assignment_scope_id: str,
        requested_scope_type: ScopeType,
        requested_scope_id: str,
    ) -> bool:
        if assignment_scope_type == ScopeType.PLATFORM:
            return True
        if assignment_scope_type == requested_scope_type and assignment_scope_id == requested_scope_id:
            return True
        return False
