from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class alert_card:
    alert_id: str
    tenant_id: str
    subject_id: str
    category: str
    severity: str
    title: str
    source: str
    status: str = "open"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class action_item:
    action_id: str
    tenant_id: str
    subject_id: str
    action_type: str
    priority: str
    status: str
    owner: str
    source_alert_id: str = ""
    notes: str = ""


@dataclass(frozen=True)
class priority_bucket:
    priority: str
    total_items: int
    items: tuple[action_item, ...] = ()


@dataclass(frozen=True)
class dashboard_summary:
    tenant_id: str
    total_unpaid_fees: int
    total_absent_students: int
    total_inactive_users: int
    total_overdue_follow_ups: int
    total_unresolved_alerts: int
    priority_buckets: tuple[priority_bucket, ...] = ()
