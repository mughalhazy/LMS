from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from service import AuditQuery, EnterpriseControlService, IdentityContext


def run_qc() -> dict[str, object]:
    service = EnterpriseControlService()
    service.set_role_permissions(tenant_id="tenant_qc", role="security-admin", permissions={"rbac.manage"})
    service.set_role_permissions(tenant_id="tenant_qc", role="auditor", permissions={"audit.read", "compliance.read"})
    service.set_role_permissions(tenant_id="tenant_qc", role="compliance-admin", permissions={"compliance.manage"})
    service.set_role_inheritance(tenant_id="tenant_qc", role="security-admin", inherits_from={"auditor", "compliance-admin"})
    service.grant_permission_inheritance(permission="audit.read", includes="audit.query")

    security_admin = IdentityContext(tenant_id="tenant_qc", actor_id="sec_admin", roles=("security-admin",))
    auditor = IdentityContext(tenant_id="tenant_qc", actor_id="aud_1", roles=("auditor",))
    security_plus = IdentityContext(tenant_id="tenant_qc", actor_id="sec_plus", roles=("security-admin",))
    outsider = IdentityContext(tenant_id="tenant_other", actor_id="outsider", roles=("security-admin",))

    assign_status, _ = service.api_assign_role_permission(
        identity=security_admin,
        tenant_id="tenant_qc",
        role="auditor",
        permission="report.read",
    )

    allow_status, allow_payload = service.api_authorize(
        identity=auditor,
        action="read",
        resource="report:monthly",
        permission="report.read",
        tenant_id="tenant_qc",
    )

    deny_status, deny_payload = service.api_authorize(
        identity=outsider,
        action="read",
        resource="report:monthly",
        permission="report.read",
        tenant_id="tenant_qc",
    )

    audit_status, audit_payload = service.api_list_audit_logs(identity=auditor, tenant_id="tenant_qc")
    compliance_status, _ = service.api_upsert_compliance_record(
        identity=security_plus,
        tenant_id="tenant_qc",
        framework="soc2",
        control_id="cc6.1",
        status="pass",
    )
    query_status, query_payload = service.api_query_audit_trail(
        identity=security_plus,
        tenant_id="tenant_qc",
        query=AuditQuery(action="compliance.upsert", limit=10),
    )

    strict_access_control = (
        assign_status == 200
        and allow_status == 200
        and allow_payload.get("allowed") is True
        and deny_status == 403
        and deny_payload.get("reason") == "tenant_context_mismatch"
    )
    audit_logging_ok = audit_status == 200 and audit_payload.get("count", 0) >= 3
    compliance_ok = compliance_status == 200 and query_status == 200 and query_payload.get("count", 0) >= 1
    api_contract_ok = "audit_event_id" in allow_payload

    passed = strict_access_control and audit_logging_ok and compliance_ok and api_contract_ok and service.has_strict_access_control()
    return {
        "checks": {
            "strict_access_control": strict_access_control,
            "audit_logging": audit_logging_ok,
            "compliance_tracking": compliance_ok,
            "api_contract": api_contract_ok,
        },
        "score": 10 if passed else 0,
    }


if __name__ == "__main__":
    print(json.dumps(run_qc(), indent=2))
