from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import ComplianceConfig, EnterpriseIntegration, RBACPolicy

COMPLIANCE_LEVELS = {"baseline", "enhanced", "strict"}
INTEGRATION_TYPES = {"hris", "sso", "webhook", "lti", "directory"}


class EnterpriseControlService:
    def __init__(self) -> None:
        self._compliance: Dict[str, ComplianceConfig] = {}
        self._integrations: Dict[str, EnterpriseIntegration] = {}
        self._rbac_policies: Dict[str, RBACPolicy] = {}

    # --- Compliance ---

    def get_compliance(self, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        config = self._compliance.get(tenant_id) or ComplianceConfig(
            tenant_id=tenant_id, compliance_level="baseline"
        )
        return 200, self._ser_compliance(config)

    def update_compliance(self, tenant_id: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        level = body.get("compliance_level", "baseline")
        if level not in COMPLIANCE_LEVELS:
            return 400, {"error": "invalid_compliance_level", "valid": list(COMPLIANCE_LEVELS)}
        config = self._compliance.get(tenant_id) or ComplianceConfig(tenant_id=tenant_id, compliance_level=level)
        config.compliance_level = level
        for field in ("data_minimisation", "encryption_at_rest", "audit_retention_days", "export_enabled"):
            if field in body:
                setattr(config, field, body[field])
        config.updated_at = datetime.now(timezone.utc)
        self._compliance[tenant_id] = config
        return 200, self._ser_compliance(config)

    # --- Integrations ---

    def register_integration(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        integration_type = body.get("integration_type", "")
        if integration_type not in INTEGRATION_TYPES:
            return 400, {"error": "invalid_integration_type", "valid": list(INTEGRATION_TYPES)}
        integration = EnterpriseIntegration(
            integration_id=f"int-{secrets.token_urlsafe(8)}",
            tenant_id=body.get("tenant_id", ""),
            integration_type=integration_type,
            name=body.get("name", ""),
            config=body.get("config", {}),
        )
        self._integrations[integration.integration_id] = integration
        return 201, self._ser_integration(integration)

    def list_integrations(self, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        results = [i for i in self._integrations.values() if i.tenant_id == tenant_id]
        return 200, {"integrations": [self._ser_integration(i) for i in results], "count": len(results)}

    def update_integration_status(self, integration_id: str, status: str) -> Tuple[int, Dict[str, Any]]:
        integration = self._integrations.get(integration_id)
        if not integration:
            return 404, {"error": "integration_not_found"}
        integration.status = status
        return 200, self._ser_integration(integration)

    # --- RBAC ---

    def set_rbac_policy(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        policy = RBACPolicy(
            policy_id=f"rbac-{secrets.token_urlsafe(8)}",
            tenant_id=body.get("tenant_id", ""),
            role=body.get("role", ""),
            permissions=body.get("permissions", []),
            delegatable=body.get("delegatable", False),
        )
        self._rbac_policies[policy.policy_id] = policy
        return 201, {"policy_id": policy.policy_id, "role": policy.role,
                     "permissions": policy.permissions, "delegatable": policy.delegatable}

    def get_rbac_policies(self, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        policies = [p for p in self._rbac_policies.values() if p.tenant_id == tenant_id]
        return 200, {"policies": [{"policy_id": p.policy_id, "role": p.role,
                                    "permissions": p.permissions} for p in policies]}

    def _ser_compliance(self, c: ComplianceConfig) -> Dict[str, Any]:
        return {"tenant_id": c.tenant_id, "compliance_level": c.compliance_level,
                "data_minimisation": c.data_minimisation, "encryption_at_rest": c.encryption_at_rest,
                "audit_retention_days": c.audit_retention_days, "export_enabled": c.export_enabled}

    def _ser_integration(self, i: EnterpriseIntegration) -> Dict[str, Any]:
        return {"integration_id": i.integration_id, "tenant_id": i.tenant_id,
                "integration_type": i.integration_type, "name": i.name, "status": i.status}
