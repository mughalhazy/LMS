from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from service import EnterpriseControlService, IdentityContext


def run_qc() -> dict[str, object]:
    service = EnterpriseControlService()
    service.set_role_permissions(tenant_id="tenant_qc", role="security-admin", permissions={"rbac.manage"})
    service.set_role_permissions(tenant_id="tenant_qc", role="auditor", permissions={"audit.read"})

    security_admin = IdentityContext(tenant_id="tenant_qc", actor_id="sec_admin", roles=("security-admin",))
    auditor = IdentityContext(tenant_id="tenant_qc", actor_id="aud_1", roles=("auditor",))
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

    strict_access_control = (
        assign_status == 200
        and allow_status == 200
        and allow_payload.get("allowed") is True
        and deny_status == 403
        and deny_payload.get("reason") == "tenant_context_mismatch"
    )
    audit_logging_ok = audit_status == 200 and audit_payload.get("count", 0) >= 3
    api_contract_ok = "audit_event_id" in allow_payload

    passed = strict_access_control and audit_logging_ok and api_contract_ok and service.has_strict_access_control()
    return {
        "checks": {
            "strict_access_control": strict_access_control,
            "audit_logging": audit_logging_ok,
            "api_contract": api_contract_ok,
        },
        "score": 10 if passed else 0,
    }


if __name__ == "__main__":
    print(json.dumps(run_qc(), indent=2))
