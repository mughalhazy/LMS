from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(_ROOT))

from shared.models.config import ConfigResolutionContext
from shared.models.teacher_network import CrossInstitutionAssignment, TeacherTenantAffiliation


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ConfigModule = _load_module("config_service_module_for_enterprise_control", "services/config-service/service.py")
ConfigService = _ConfigModule.ConfigService
_EnterpriseModelsModule = _load_module("enterprise_control_models_module", "services/enterprise-control/models.py")
AuditQuery = _EnterpriseModelsModule.AuditQuery
ComplianceRecord = _EnterpriseModelsModule.ComplianceRecord


@dataclass(frozen=True)
class IdentityContext:
    tenant_id: str
    actor_id: str
    roles: tuple[str, ...] = ()
    country_code: str = "global"
    segment_id: str = "global"

    def normalized(self) -> "IdentityContext":
        return IdentityContext(
            tenant_id=self.tenant_id.strip(),
            actor_id=self.actor_id.strip(),
            roles=tuple(sorted({role.strip().lower() for role in self.roles if role.strip()})),
            country_code=(self.country_code or "global").strip() or "global",
            segment_id=(self.segment_id or "global").strip() or "global",
        )


@dataclass(frozen=True)
class AuditLogEntry:
    event_id: str
    tenant_id: str
    actor_id: str
    action: str
    resource: str
    decision: str
    reason: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class EnterpriseControlService:
    """Enterprise control plane for RBAC enforcement, audit logs, and API guards."""

    def __init__(self, *, config_service: ConfigService | None = None) -> None:
        self._config_service = config_service or ConfigService()
        self._role_permissions: dict[tuple[str, str], set[str]] = {}
        self._role_inheritance: dict[tuple[str, str], set[str]] = {}
        self._permission_inheritance: dict[str, set[str]] = {}
        self._audit_log: list[AuditLogEntry] = []
        self._compliance_records: dict[tuple[str, str, str], ComplianceRecord] = {}
        self._teacher_affiliations: dict[tuple[str, str, str], TeacherTenantAffiliation] = {}
        self._cross_institution_assignments: dict[tuple[str, str, str], list[CrossInstitutionAssignment]] = {}
        # CGAP-052: SSO identity federation — map tenant_id → sso_provider instance.
        self._sso_providers: dict[str, Any] = {}

    def set_role_permissions(self, *, tenant_id: str, role: str, permissions: set[str]) -> None:
        key = (tenant_id.strip(), role.strip().lower())
        self._role_permissions[key] = {permission.strip().lower() for permission in permissions if permission.strip()}

    def grant_role_permission(self, *, tenant_id: str, role: str, permission: str) -> None:
        key = (tenant_id.strip(), role.strip().lower())
        self._role_permissions.setdefault(key, set()).add(permission.strip().lower())

    def set_role_inheritance(self, *, tenant_id: str, role: str, inherits_from: set[str]) -> None:
        key = (tenant_id.strip(), role.strip().lower())
        self._role_inheritance[key] = {value.strip().lower() for value in inherits_from if value.strip()}

    def grant_permission_inheritance(self, *, permission: str, includes: str) -> None:
        parent = permission.strip().lower()
        child = includes.strip().lower()
        if parent and child:
            self._permission_inheritance.setdefault(parent, set()).add(child)

    def list_role_permissions(self, *, tenant_id: str, role: str) -> tuple[str, ...]:
        key = (tenant_id.strip(), role.strip().lower())
        return tuple(sorted(self._role_permissions.get(key, set())))

    def _strict_access_control_enabled(self, identity: IdentityContext) -> bool:
        config = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=identity.tenant_id,
                country_code=identity.country_code,
                segment_id=identity.segment_id,
            )
        )
        policy = config.behavior_tuning.get("enterprise_control", {})
        return bool(policy.get("strict_access_control", True))

    def _evaluate_permission(self, *, identity: IdentityContext, permission: str) -> tuple[bool, str]:
        normalized = identity.normalized()
        normalized_permission = permission.strip().lower()

        if not normalized.actor_id or not normalized.tenant_id:
            return False, "missing_identity_context"

        if normalized_permission == "":
            return False, "missing_permission"

        if not normalized.roles:
            return False, "no_roles_assigned"

        strict = self._strict_access_control_enabled(normalized)
        resolved_roles = self._expand_roles(tenant_id=normalized.tenant_id, roles=normalized.roles)
        for role in normalized.roles:
            allowed_permissions = self._expand_permissions(self._role_permissions.get((normalized.tenant_id, role), set()))
            if self._permission_matches(allowed_permissions=allowed_permissions, requested_permission=normalized_permission):
                return True, f"role:{role}"

        for role in resolved_roles:
            allowed_permissions = self._role_permissions.get((normalized.tenant_id, role), set())
            expanded_permissions = self._expand_permissions(allowed_permissions)
            if self._permission_matches(allowed_permissions=expanded_permissions, requested_permission=normalized_permission):
                return True, f"role_inherited:{role}"

        if strict:
            return False, "strict_access_control_denied"

        return False, "permission_not_granted"

    def _expand_roles(self, *, tenant_id: str, roles: tuple[str, ...]) -> tuple[str, ...]:
        queue = [role.strip().lower() for role in roles if role.strip()]
        discovered: set[str] = set()
        while queue:
            role = queue.pop(0)
            for inherited in self._role_inheritance.get((tenant_id.strip(), role), set()):
                if inherited not in discovered:
                    discovered.add(inherited)
                    queue.append(inherited)
        return tuple(sorted(discovered))

    def _expand_permissions(self, permissions: set[str]) -> set[str]:
        discovered = {value.strip().lower() for value in permissions if value.strip()}
        queue = list(discovered)
        while queue:
            permission = queue.pop(0)
            for included in self._permission_inheritance.get(permission, set()):
                if included not in discovered:
                    discovered.add(included)
                    queue.append(included)
        return discovered

    def _permission_matches(self, *, allowed_permissions: set[str], requested_permission: str) -> bool:
        if requested_permission in allowed_permissions:
            return True
        for allowed in allowed_permissions:
            if allowed.endswith(".*") and requested_permission.startswith(f"{allowed[:-2]}."):
                return True
        return False

    def _append_audit(
        self,
        *,
        identity: IdentityContext,
        action: str,
        resource: str,
        decision: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            event_id=f"ec_audit_{len(self._audit_log) + 1}",
            tenant_id=identity.tenant_id,
            actor_id=identity.actor_id,
            action=action,
            resource=resource,
            decision=decision,
            reason=reason,
            metadata=metadata or {},
        )
        self._audit_log.append(entry)
        return entry

    def _authorize_and_audit(
        self,
        *,
        identity: IdentityContext,
        tenant_id: str,
        permission: str,
        action: str,
        resource: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, str, AuditLogEntry]:
        normalized = identity.normalized()
        target_tenant = tenant_id.strip()
        normalized_metadata = metadata or {}

        if normalized.tenant_id != target_tenant:
            audit = self._append_audit(
                identity=normalized,
                action=action,
                resource=resource,
                decision="deny",
                reason="tenant_context_mismatch",
                metadata={**normalized_metadata, "target_tenant": target_tenant, "permission": permission.strip().lower()},
            )
            return False, "tenant_context_mismatch", audit

        allowed, reason = self._evaluate_permission(identity=normalized, permission=permission)
        audit = self._append_audit(
            identity=normalized,
            action=action,
            resource=resource,
            decision="allow" if allowed else "deny",
            reason=reason,
            metadata={**normalized_metadata, "permission": permission.strip().lower()},
        )
        return allowed, reason, audit

    # ------------------------------------------------------------------ #
    # BC-GATE-01 (CGAP-051) — Machine-readable deny reason codes        #
    # ------------------------------------------------------------------ #

    # Map internal RBAC evaluation reasons → BC-GATE-01 machine-readable deny codes
    _RBAC_TO_GATE_CODE: dict[str, str] = {
        "tenant_context_mismatch": "suspended",
        "missing_identity_context": "suspended",
        "no_roles_assigned": "not_entitled_plan",
        "permission_not_granted": "not_entitled_plan",
        "strict_access_control_denied": "flag_disabled",
        "missing_permission": "flag_disabled",
    }

    # BC-GATE-01 user-facing messages + action links per spec table
    _GATE_CODE_UX: dict[str, dict[str, str]] = {
        "not_entitled_plan": {
            "user_message": "This feature requires a higher-tier plan.",
            "action_link": "/upgrade",
        },
        "not_entitled_addon": {
            "user_message": "This feature requires an add-on.",
            "action_link": "/add-ons",
        },
        "flag_disabled": {
            # Hidden from UI — must not surface to non-technical users (BC-GATE-01 §rule 1)
            "user_message": "",
            "action_link": "",
        },
        "suspended": {
            "user_message": "Your account is currently suspended. Contact your administrator.",
            "action_link": "/support",
        },
        "quota_exceeded": {
            "user_message": "You've reached your usage limit for this period.",
            "action_link": "/upgrade",
        },
    }

    @classmethod
    def _gate_deny_code(cls, rbac_reason: str) -> str:
        """BC-GATE-01 (CGAP-051): map internal RBAC reason to BC-GATE-01 machine-readable deny code."""
        return cls._RBAC_TO_GATE_CODE.get(rbac_reason, "not_entitled_plan")

    # ------------------------------------------------------------------ #
    # CGAP-052 — SSO identity federation                                 #
    # ------------------------------------------------------------------ #

    def register_sso_provider(self, *, tenant_id: str, provider: Any) -> None:
        """CGAP-052: register an SSO provider for a tenant.

        The provider must implement:
          - `consume_callback(code_or_assertion, correlation_id) -> dict`
            returning at minimum: {user_id, email, roles: list[str], tenant_id, ...}
        This allows enterprise tenants to authenticate via SAML/OIDC federation
        instead of (or in addition to) credential-based login.
        """
        self._sso_providers[tenant_id.strip()] = provider

    def federate_sso_identity(
        self,
        *,
        tenant_id: str,
        code_or_assertion: str,
        correlation_id: str | None = None,
    ) -> IdentityContext | None:
        """CGAP-052: validate an SSO assertion/code and return a federated IdentityContext.

        Returns None if no SSO provider is registered for the tenant or if the assertion
        is invalid. Callers must treat None as authentication failure.
        """
        normalized_tenant = tenant_id.strip()
        provider = self._sso_providers.get(normalized_tenant)
        if provider is None:
            return None  # no SSO provider registered — fall through to credential auth

        try:
            claims = provider.consume_callback(code_or_assertion, correlation_id or "")
        except Exception:
            return None  # invalid assertion or provider error — treat as auth failure

        user_id = str(claims.get("user_id") or claims.get("sub") or "").strip()
        roles = [str(r).strip().lower() for r in claims.get("roles", []) if str(r).strip()]
        if not user_id:
            return None  # assertion did not yield a resolvable identity

        return IdentityContext(
            tenant_id=normalized_tenant,
            actor_id=user_id,
            roles=tuple(sorted(set(roles))),
        )

    def api_sso_authorize(
        self,
        *,
        tenant_id: str,
        code_or_assertion: str,
        correlation_id: str | None = None,
        action: str,
        resource: str,
        permission: str,
    ) -> tuple[int, dict[str, Any]]:
        """CGAP-052: federate SSO identity and then run standard RBAC authorization.

        If SSO federation fails (no provider or invalid assertion), returns 401.
        If federation succeeds, delegates to api_authorize() with the derived IdentityContext.
        """
        identity = self.federate_sso_identity(
            tenant_id=tenant_id,
            code_or_assertion=code_or_assertion,
            correlation_id=correlation_id,
        )
        if identity is None:
            return 401, {
                "allowed": False,
                "reason": "sso_identity_federation_failed",
                "deny_reason_code": "sso_auth_failure",
                "user_message": "SSO authentication could not be completed. Please try again or contact your administrator.",
                "action_link": "",
            }

        return self.api_authorize(
            identity=identity,
            action=action,
            resource=resource,
            permission=permission,
            tenant_id=tenant_id,
        )

    # API layer
    def api_authorize(
        self,
        *,
        identity: IdentityContext,
        action: str,
        resource: str,
        permission: str,
        tenant_id: str,
    ) -> tuple[int, dict[str, Any]]:
        allowed, reason, audit = self._authorize_and_audit(
            identity=identity,
            tenant_id=tenant_id,
            permission=permission,
            action=action,
            resource=resource,
        )

        if not allowed:
            deny_code = self._gate_deny_code(reason)
            ux = self._GATE_CODE_UX.get(deny_code, {"user_message": "", "action_link": ""})
            return 403, {
                "allowed": False,
                "reason": reason,
                # BC-GATE-01 (CGAP-051): machine-readable deny code so API consumers can
                # differentiate not_entitled_plan / not_entitled_addon / suspended / flag_disabled
                "deny_reason_code": deny_code,
                "user_message": ux["user_message"],
                "action_link": ux["action_link"],
                "audit_event_id": audit.event_id,
            }

        return 200, {"allowed": True, "reason": reason, "audit_event_id": audit.event_id}

    def api_list_audit_logs(
        self,
        *,
        identity: IdentityContext,
        tenant_id: str,
        limit: int = 50,
    ) -> tuple[int, dict[str, Any]]:
        normalized = identity.normalized()
        allowed, reason, audit = self._authorize_and_audit(
            identity=normalized,
            tenant_id=tenant_id,
            permission="audit.read",
            action="audit.list",
            resource="audit_log",
            metadata={"limit": max(limit, 0)},
        )
        if not allowed:
            return 403, {"error": reason, "audit_event_id": audit.event_id}

        tenant_logs = [entry for entry in self._audit_log if entry.tenant_id == normalized.tenant_id]
        rows = [
            {
                "event_id": row.event_id,
                "tenant_id": row.tenant_id,
                "actor_id": row.actor_id,
                "action": row.action,
                "resource": row.resource,
                "decision": row.decision,
                "reason": row.reason,
                "created_at": row.created_at.isoformat(),
                "metadata": row.metadata,
            }
            for row in tenant_logs[-max(limit, 0) :]
        ]
        return 200, {"data": rows, "count": len(rows)}

    def api_query_audit_trail(
        self,
        *,
        identity: IdentityContext,
        tenant_id: str,
        query: AuditQuery,
    ) -> tuple[int, dict[str, Any]]:
        normalized = identity.normalized()
        allowed, reason, audit = self._authorize_and_audit(
            identity=normalized,
            tenant_id=tenant_id,
            permission="audit.query",
            action="audit.query",
            resource="audit_log",
            metadata={"limit": query.limit, "offset": query.offset},
        )
        if not allowed:
            return 403, {"error": reason, "audit_event_id": audit.event_id}

        rows = [entry for entry in self._audit_log if entry.tenant_id == normalized.tenant_id]
        if query.actor_id:
            rows = [entry for entry in rows if entry.actor_id == query.actor_id.strip()]
        if query.action:
            rows = [entry for entry in rows if entry.action == query.action.strip().lower()]
        if query.resource_prefix:
            rows = [entry for entry in rows if entry.resource.startswith(query.resource_prefix.strip().lower())]
        if query.decision:
            rows = [entry for entry in rows if entry.decision == query.decision.strip().lower()]
        if query.permission:
            requested = query.permission.strip().lower()
            rows = [entry for entry in rows if str(entry.metadata.get("permission", "")).lower() == requested]
        if query.created_from:
            rows = [entry for entry in rows if entry.created_at >= query.created_from]
        if query.created_to:
            rows = [entry for entry in rows if entry.created_at <= query.created_to]

        ordered = sorted(rows, key=lambda row: row.created_at, reverse=query.descending)
        start = max(query.offset, 0)
        end = start + max(query.limit, 0)
        page = ordered[start:end]

        data = [
            {
                "event_id": row.event_id,
                "tenant_id": row.tenant_id,
                "actor_id": row.actor_id,
                "action": row.action,
                "resource": row.resource,
                "decision": row.decision,
                "reason": row.reason,
                "created_at": row.created_at.isoformat(),
                "metadata": row.metadata,
            }
            for row in page
        ]
        return 200, {"data": data, "count": len(data), "total": len(ordered)}

    def api_assign_role_permission(
        self,
        *,
        identity: IdentityContext,
        tenant_id: str,
        role: str,
        permission: str,
    ) -> tuple[int, dict[str, Any]]:
        normalized = identity.normalized()
        allowed, reason, audit = self._authorize_and_audit(
            identity=normalized,
            tenant_id=tenant_id,
            permission="rbac.manage",
            action="rbac.assign_permission",
            resource=f"role:{role.strip().lower()}",
            metadata={"permission": permission.strip().lower()},
        )
        if not allowed:
            return 403, {"error": reason, "audit_event_id": audit.event_id}

        self.grant_role_permission(tenant_id=tenant_id, role=role, permission=permission)
        return 200, {
            "tenant_id": tenant_id.strip(),
            "role": role.strip().lower(),
            "permissions": self.list_role_permissions(tenant_id=tenant_id, role=role),
        }

    def api_upsert_compliance_record(
        self,
        *,
        identity: IdentityContext,
        tenant_id: str,
        framework: str,
        control_id: str,
        status: str,
        evidence: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        normalized = identity.normalized()
        allowed, reason, audit = self._authorize_and_audit(
            identity=normalized,
            tenant_id=tenant_id,
            permission="compliance.manage",
            action="compliance.upsert",
            resource=f"compliance:{framework.strip().lower()}:{control_id.strip().lower()}",
        )
        if not allowed:
            return 403, {"error": reason, "audit_event_id": audit.event_id}

        normalized_framework = framework.strip().lower()
        normalized_control = control_id.strip().lower()
        normalized_status = status.strip().lower()
        key = (tenant_id.strip(), normalized_framework, normalized_control)
        record = ComplianceRecord(
            record_id=f"cmp_{len(self._compliance_records) + 1}",
            tenant_id=tenant_id.strip(),
            framework=normalized_framework,
            control_id=normalized_control,
            status=normalized_status,
            assessed_by_actor_id=normalized.actor_id,
            created_at=datetime.now(timezone.utc),
            evidence=evidence or {},
        )
        self._compliance_records[key] = record
        self._append_audit(
            identity=normalized,
            action="compliance.recorded",
            resource=f"compliance:{normalized_framework}:{normalized_control}",
            decision="allow",
            reason="compliance_record_updated",
            metadata={"status": normalized_status},
        )
        return 200, {"record_id": record.record_id, "framework": record.framework, "control_id": record.control_id, "status": record.status}

    def api_list_compliance_records(self, *, identity: IdentityContext, tenant_id: str) -> tuple[int, dict[str, Any]]:
        normalized = identity.normalized()
        allowed, reason, audit = self._authorize_and_audit(
            identity=normalized,
            tenant_id=tenant_id,
            permission="compliance.read",
            action="compliance.list",
            resource="compliance_records",
        )
        if not allowed:
            return 403, {"error": reason, "audit_event_id": audit.event_id}

        rows = [row for row in self._compliance_records.values() if row.tenant_id == tenant_id.strip()]
        data = [
            {
                "record_id": row.record_id,
                "tenant_id": row.tenant_id,
                "framework": row.framework,
                "control_id": row.control_id,
                "status": row.status,
                "assessed_by_actor_id": row.assessed_by_actor_id,
                "created_at": row.created_at.isoformat(),
                "evidence": row.evidence,
            }
            for row in sorted(rows, key=lambda item: (item.framework, item.control_id))
        ]
        return 200, {"data": data, "count": len(data)}

    def has_strict_access_control(self) -> bool:
        return hasattr(self, "_evaluate_permission") and hasattr(self, "api_authorize")

    def link_teacher_to_external_tenant(
        self,
        *,
        identity: IdentityContext,
        home_tenant_id: str,
        teacher_id: str,
        external_tenant_id: str,
        permission_scope: tuple[str, ...] = ("academy.teacher_assignment.cross_institution",),
        max_concurrent_batches: int = 1,
        payout_tenant_id: str | None = None,
        payout_account_ref: str = "",
    ) -> TeacherTenantAffiliation:
        normalized = identity.normalized()
        target_home_tenant = home_tenant_id.strip()
        target_external_tenant = external_tenant_id.strip()
        if not teacher_id.strip():
            raise ValueError("teacher_id is required")
        if target_home_tenant == "" or target_external_tenant == "":
            raise ValueError("tenant ids are required")
        if target_home_tenant == target_external_tenant:
            raise ValueError("external tenant must differ from home tenant")
        if max_concurrent_batches < 1:
            raise ValueError("max_concurrent_batches must be at least 1")

        allowed, reason, audit = self._authorize_and_audit(
            identity=normalized,
            tenant_id=target_home_tenant,
            permission="teacher.network.manage",
            action="teacher.link_external_tenant",
            resource=f"teacher:{teacher_id.strip()}",
            metadata={"external_tenant_id": target_external_tenant},
        )
        if not allowed:
            raise PermissionError(f"{reason}:{audit.event_id}")

        normalized_scope = tuple(sorted({scope.strip().lower() for scope in permission_scope if scope.strip()}))
        payout_tenant = (payout_tenant_id or target_external_tenant).strip()
        if payout_tenant != target_external_tenant:
            raise ValueError("payout tenant must match external tenant to preserve tenant economics")
        affiliation = TeacherTenantAffiliation(
            teacher_id=teacher_id.strip(),
            home_tenant_id=target_home_tenant,
            external_tenant_id=target_external_tenant,
            linked_by_actor_id=normalized.actor_id,
            permission_scope=normalized_scope,
            max_concurrent_batches=max_concurrent_batches,
            payout_tenant_id=payout_tenant,
            payout_account_ref=payout_account_ref.strip(),
        )
        self._teacher_affiliations[(affiliation.home_tenant_id, affiliation.external_tenant_id, affiliation.teacher_id)] = affiliation
        return affiliation

    def assign_teacher_cross_institution(
        self,
        *,
        identity: IdentityContext,
        target_tenant_id: str,
        home_tenant_id: str,
        teacher_id: str,
        branch_id: str,
        batch_id: str,
        payout_rate: float = 0.0,
    ) -> CrossInstitutionAssignment:
        normalized = identity.normalized()
        target_tenant = target_tenant_id.strip()
        key = (home_tenant_id.strip(), target_tenant, teacher_id.strip())
        affiliation = self._teacher_affiliations.get(key)
        if affiliation is None or not affiliation.is_active:
            raise PermissionError("teacher is not linked to target tenant")

        allowed, reason, audit = self._authorize_and_audit(
            identity=normalized,
            tenant_id=target_tenant,
            permission="academy.teacher_assignment.cross_institution",
            action="teacher.cross_institution_assign",
            resource=f"batch:{batch_id.strip()}",
            metadata={"teacher_id": teacher_id.strip(), "home_tenant_id": home_tenant_id.strip(), "branch_id": branch_id.strip()},
        )
        if not allowed:
            raise PermissionError(f"{reason}:{audit.event_id}")

        if "academy.teacher_assignment.cross_institution" not in affiliation.permission_scope:
            raise PermissionError("affiliation_scope_denied")

        assignment_key = (target_tenant, branch_id.strip(), batch_id.strip())
        assignments = self._cross_institution_assignments.setdefault(assignment_key, [])
        active_teacher_assignments = [
            row
            for rows in self._cross_institution_assignments.values()
            for row in rows
            if row.teacher_id == teacher_id.strip()
            and row.home_tenant_id == home_tenant_id.strip()
            and row.target_tenant_id == target_tenant
        ]
        if len(active_teacher_assignments) >= affiliation.max_concurrent_batches:
            raise ValueError("cross-institution assignment batch limit reached")

        assignment = CrossInstitutionAssignment(
            teacher_id=teacher_id.strip(),
            home_tenant_id=home_tenant_id.strip(),
            target_tenant_id=target_tenant,
            branch_id=branch_id.strip(),
            batch_id=batch_id.strip(),
            assigned_by_actor_id=normalized.actor_id,
            payout_tenant_id=affiliation.payout_tenant_id or target_tenant,
            payout_rate=Decimal(str(max(float(payout_rate), 0.0))),
        )
        assignments.append(assignment)
        return assignment

    def list_teacher_tenant_affiliations(
        self,
        *,
        identity: IdentityContext,
        tenant_id: str,
        teacher_id: str,
    ) -> tuple[TeacherTenantAffiliation, ...]:
        normalized = identity.normalized()
        target_tenant = tenant_id.strip()
        allowed, reason, audit = self._authorize_and_audit(
            identity=normalized,
            tenant_id=target_tenant,
            permission="teacher.network.read",
            action="teacher.list_affiliations",
            resource=f"teacher:{teacher_id.strip()}",
        )
        if not allowed:
            raise PermissionError(f"{reason}:{audit.event_id}")

        rows = [
            affiliation
            for (home_tenant, external_tenant, linked_teacher_id), affiliation in self._teacher_affiliations.items()
            if linked_teacher_id == teacher_id.strip() and target_tenant in {home_tenant, external_tenant}
        ]
        return tuple(sorted(rows, key=lambda row: (row.home_tenant_id, row.external_tenant_id, row.teacher_id)))
