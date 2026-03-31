from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .schemas import CohortKind, CohortSchedule, CohortStatus


@dataclass
class CohortRecord:
    cohort_id: str
    tenant_id: str
    name: str
    code: str
    kind: CohortKind
    status: CohortStatus
    schedule: CohortSchedule
    program_id: str | None
    metadata: dict[str, str]
    created_at: datetime
    updated_at: datetime
    created_by: str


@dataclass
class MembershipRecord:
    membership_id: str
    cohort_id: str
    tenant_id: str
    user_id: str
    role: str
    joined_at: datetime
    added_by: str


@dataclass
class EventRecord:
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    correlation_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any]


@dataclass
class ObservabilityState:
    counters: dict[str, int] = field(default_factory=dict)

    def inc(self, metric_name: str) -> None:
        self.counters[metric_name] = self.counters.get(metric_name, 0) + 1
