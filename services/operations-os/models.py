from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DailyAlert:
    alert_id: str
    tenant_id: str
    student_id: str
    alert_type: str
    severity: str
    message: str
    source: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionItem:
    action_id: str
    tenant_id: str
    action_type: str
    priority: str
    subject_type: str
    subject_id: str
    reason: str
    due_at: datetime
    status: str
    suggested_next_step: str
    metadata: dict[str, Any] = field(default_factory=dict)
