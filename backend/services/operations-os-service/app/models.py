from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ActionItem:
    item_id: str
    tier: str               # CRITICAL | IMPORTANT | OPTIONAL
    title: str
    description: str
    pattern: Optional[str]
    implication: Optional[str]
    action_command: str
    entity_ref: str
    operator_id: str
    tenant_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DailyActionList:
    list_id: str
    operator_id: str
    tenant_id: str
    date: str
    critical: List[ActionItem] = field(default_factory=list)
    important: List[ActionItem] = field(default_factory=list)
    optional: List[ActionItem] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OperationalMetric:
    metric_id: str
    tenant_id: str
    metric_type: str        # attendance_rate | fee_collection_rate | enrollment_pipeline | batch_health
    value: float
    threshold: float
    period: str
    recorded_at: datetime = field(default_factory=datetime.utcnow)
