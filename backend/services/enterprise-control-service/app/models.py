from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ComplianceConfig:
    tenant_id: str
    compliance_level: str   # baseline | enhanced | strict
    data_minimisation: bool = True
    encryption_at_rest: bool = True
    audit_retention_days: int = 365
    export_enabled: bool = True
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EnterpriseIntegration:
    integration_id: str
    tenant_id: str
    integration_type: str   # hris | sso | webhook | lti | directory
    name: str
    config: Dict[str, Any]
    status: str = "active"  # active | inactive | error
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RBACPolicy:
    policy_id: str
    tenant_id: str
    role: str
    permissions: List[str]
    delegatable: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
