from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(_ROOT))

from shared.models.config import ConfigResolutionContext


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
        self._audit_log: list[AuditLogEntry] = []

    def set_role_permissions(self, *, tenant_id: str, role: str, permissions: set[str]) -> None:
        key = (tenant_id.strip(), role.strip().lower())
        self._role_permissions[key] = {permission.strip().lower() for permission in permissions if permission.strip()}

    def grant_role_permission(self, *, tenant_id: str, role: str, permission: str) -> None:
        key = (tenant_id.strip(), role.strip().lower())
        self._role_permissions.setdefault(key, set()).add(permission.strip().lower())

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
        for role in normalized.roles:
            allowed_permissions = self._role_permissions.get((normalized.tenant_id, role), set())
            if normalized_permission in allowed_permissions:
                return True, f"role:{role}"

        if strict:
            return False, "strict_access_control_denied"

        return False, "permission_not_granted"

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
        normalized = identity.normalized()
        target_tenant = tenant_id.strip()

        if normalized.tenant_id != target_tenant:
            audit = self._append_audit(
                identity=normalized,
                action=action,
                resource=resource,
                decision="deny",
                reason="tenant_context_mismatch",
                metadata={"target_tenant": target_tenant},
            )
            return 403, {"allowed": False, "reason": audit.reason, "audit_event_id": audit.event_id}

        allowed, reason = self._evaluate_permission(identity=normalized, permission=permission)
        audit = self._append_audit(
            identity=normalized,
            action=action,
            resource=resource,
            decision="allow" if allowed else "deny",
            reason=reason,
            metadata={"permission": permission.strip().lower()},
        )

        if not allowed:
            return 403, {"allowed": False, "reason": reason, "audit_event_id": audit.event_id}

        return 200, {"allowed": True, "reason": reason, "audit_event_id": audit.event_id}

    def api_list_audit_logs(
        self,
        *,
        identity: IdentityContext,
        tenant_id: str,
        limit: int = 50,
    ) -> tuple[int, dict[str, Any]]:
        normalized = identity.normalized()
        if normalized.tenant_id != tenant_id.strip():
            return 403, {"error": "tenant_context_mismatch"}

        allowed, reason = self._evaluate_permission(identity=normalized, permission="audit.read")
        self._append_audit(
            identity=normalized,
            action="audit.list",
            resource="audit_log",
            decision="allow" if allowed else "deny",
            reason=reason,
        )
        if not allowed:
            return 403, {"error": reason}

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

    def api_assign_role_permission(
        self,
        *,
        identity: IdentityContext,
        tenant_id: str,
        role: str,
        permission: str,
    ) -> tuple[int, dict[str, Any]]:
        normalized = identity.normalized()
        if normalized.tenant_id != tenant_id.strip():
            return 403, {"error": "tenant_context_mismatch"}

        allowed, reason = self._evaluate_permission(identity=normalized, permission="rbac.manage")
        self._append_audit(
            identity=normalized,
            action="rbac.assign_permission",
            resource=f"role:{role.strip().lower()}",
            decision="allow" if allowed else "deny",
            reason=reason,
            metadata={"permission": permission.strip().lower()},
        )
        if not allowed:
            return 403, {"error": reason}

        self.grant_role_permission(tenant_id=tenant_id, role=role, permission=permission)
        return 200, {
            "tenant_id": tenant_id.strip(),
            "role": role.strip().lower(),
            "permissions": self.list_role_permissions(tenant_id=tenant_id, role=role),
        }

    def has_strict_access_control(self) -> bool:
        return hasattr(self, "_evaluate_permission") and hasattr(self, "api_authorize")
