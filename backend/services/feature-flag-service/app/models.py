from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ExperimentConfig:
    experiment_id: str
    variants: List[Dict[str, Any]]  # [{"name": "control", "weight": 50}, {"name": "treatment", "weight": 50}]
    allocation_version: str = "v1"


@dataclass
class FlagDefinition:
    feature_key: str
    default_state: bool
    kill_switch: bool = False
    segment_rules: Dict[str, bool] = field(default_factory=dict)   # segment -> state
    tenant_overrides: Dict[str, bool] = field(default_factory=dict)  # tenant_id -> state
    experiment: Optional[ExperimentConfig] = None
    description: str = ""
    snapshot_version: str = "v1"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FlagDecision:
    feature_key: str
    state: bool
    reason: str  # kill_switch | entitlement_denied | tenant_override | experiment | segment_rule | default
    rule_id: Optional[str]
    snapshot_version: str
    experiment_variant: Optional[str]
    evaluated_at: datetime
