from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/enterprise-control/service.py"
_service_spec = importlib.util.spec_from_file_location("enterprise_control_service_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load service module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)
EnterpriseControlService = _service_module.EnterpriseControlService
IdentityContext = _service_module.IdentityContext
from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope


def test_api_authorize_enforces_tenant_scope_and_rbac() -> None:
    service = EnterpriseControlService()
    service.set_role_permissions(tenant_id="tenant_1", role="admin", permissions={"report.read"})

    ok_identity = IdentityContext(tenant_id="tenant_1", actor_id="user_1", roles=("admin",))
    denied_identity = IdentityContext(tenant_id="tenant_2", actor_id="user_2", roles=("admin",))

    ok_status, ok_payload = service.api_authorize(
        identity=ok_identity,
        action="read",
        resource="report:finance",
        permission="report.read",
        tenant_id="tenant_1",
    )
    denied_status, denied_payload = service.api_authorize(
        identity=denied_identity,
        action="read",
        resource="report:finance",
        permission="report.read",
        tenant_id="tenant_1",
    )

    assert ok_status == 200
    assert ok_payload["allowed"] is True
    assert ok_payload["audit_event_id"]
    assert denied_status == 403
    assert denied_payload["reason"] == "tenant_context_mismatch"
    assert denied_payload["audit_event_id"]


def test_api_list_audit_logs_requires_audit_read_permission() -> None:
    service = EnterpriseControlService()
    service.set_role_permissions(tenant_id="tenant_1", role="auditor", permissions={"audit.read"})
    service.set_role_permissions(tenant_id="tenant_1", role="viewer", permissions={"report.read"})

    auditor = IdentityContext(tenant_id="tenant_1", actor_id="aud_1", roles=("auditor",))
    viewer = IdentityContext(tenant_id="tenant_1", actor_id="view_1", roles=("viewer",))

    service.api_authorize(
        identity=auditor,
        action="read",
        resource="report:finance",
        permission="report.read",
        tenant_id="tenant_1",
    )

    ok_status, ok_payload = service.api_list_audit_logs(identity=auditor, tenant_id="tenant_1")
    denied_status, denied_payload = service.api_list_audit_logs(identity=viewer, tenant_id="tenant_1")

    assert ok_status == 200
    assert ok_payload["count"] >= 1
    assert denied_status == 403
    assert denied_payload["error"] == "strict_access_control_denied"
    assert denied_payload["audit_event_id"]


def test_api_assign_role_permission_requires_rbac_manage() -> None:
    service = EnterpriseControlService()
    service.set_role_permissions(tenant_id="tenant_1", role="security-admin", permissions={"rbac.manage"})
    service.set_role_permissions(tenant_id="tenant_1", role="viewer", permissions={"report.read"})

    admin = IdentityContext(tenant_id="tenant_1", actor_id="sec_1", roles=("security-admin",))
    viewer = IdentityContext(tenant_id="tenant_1", actor_id="view_1", roles=("viewer",))

    ok_status, ok_payload = service.api_assign_role_permission(
        identity=admin,
        tenant_id="tenant_1",
        role="viewer",
        permission="audit.read",
    )
    denied_status, denied_payload = service.api_assign_role_permission(
        identity=viewer,
        tenant_id="tenant_1",
        role="viewer",
        permission="rbac.manage",
    )

    assert ok_status == 200
    assert "audit.read" in ok_payload["permissions"]
    assert denied_status == 403
    assert denied_payload["error"] == "strict_access_control_denied"
    assert denied_payload["audit_event_id"]


def test_tenant_mismatch_is_audited_for_critical_endpoints() -> None:
    service = EnterpriseControlService()
    service.set_role_permissions(tenant_id="tenant_1", role="security-admin", permissions={"rbac.manage", "audit.read"})
    outsider = IdentityContext(tenant_id="tenant_2", actor_id="user_2", roles=("security-admin",))

    assign_status, assign_payload = service.api_assign_role_permission(
        identity=outsider,
        tenant_id="tenant_1",
        role="viewer",
        permission="report.read",
    )
    audit_status, audit_payload = service.api_list_audit_logs(identity=outsider, tenant_id="tenant_1")

    assert assign_status == 403
    assert assign_payload["error"] == "tenant_context_mismatch"
    assert assign_payload["audit_event_id"]
    assert audit_status == 403
    assert audit_payload["error"] == "tenant_context_mismatch"
    assert audit_payload["audit_event_id"]


def test_config_integration_can_disable_strict_reason_path() -> None:
    service = EnterpriseControlService()
    service._config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_1"),
            capability_enabled={},
            behavior_tuning={"enterprise_control": {"strict_access_control": False}},
        )
    )

    identity = IdentityContext(tenant_id="tenant_1", actor_id="user_1", roles=("viewer",))

    status, payload = service.api_authorize(
        identity=identity,
        action="delete",
        resource="policy:tenant",
        permission="policy.delete",
        tenant_id="tenant_1",
    )

    assert status == 403
    assert payload["reason"] == "permission_not_granted"
