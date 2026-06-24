from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PolicyRule:
    rule_id: str
    action_pattern: str       # glob-style e.g. "config.change.*" or "*"
    resource_pattern: str
    decision: str             # ALLOW | DENY | CHALLENGE | REQUIRE_JIT_APPROVAL
    priority: int = 100       # lower = higher priority
    conditions: Dict[str, Any] = field(default_factory=dict)
    obligations: List[str] = field(default_factory=list)
    reason_code: str = ""


@dataclass
class PolicyBundle:
    bundle_id: str
    version: str
    rules: List[PolicyRule]
    published_at: datetime
    signature: str = ""


@dataclass
class PolicyDecision:
    decision_id: str
    tenant_id: str
    actor_id: str
    action: str
    resource_ref: str
    entitlement_input: str   # allow | deny | unknown
    policy_decision: str     # ALLOW | DENY | CHALLENGE | REQUIRE_JIT_APPROVAL
    policy_id: str
    policy_version: str
    reason_codes: List[str]
    obligations: List[str]
    request_id: str
    correlation_id: str
    evaluated_at: datetime


@dataclass
class AuditRecord:
    record_id: str
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    actor_id: Optional[str]
    target_ref: str
    action: str
    outcome: str
    source_service: str
    schema_version: str
    request_id: str
    correlation_id: str
    ingested_at: datetime
    payload_hash: str
    prev_hash: str = ""
    record_hash: str = ""
    decision_id: Optional[str] = None
    control_id: Optional[str] = None
    legal_hold: bool = False
