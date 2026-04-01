from __future__ import annotations

from dataclasses import dataclass

from shared.models.operations_dashboard import action_item, alert_card, dashboard_summary, priority_bucket


@dataclass(frozen=True)
class DailyOperationsDashboard:
    summary: dashboard_summary
    alert_cards: tuple[alert_card, ...]
    action_items: tuple[action_item, ...]


__all__ = [
    "DailyOperationsDashboard",
    "action_item",
    "alert_card",
    "dashboard_summary",
    "priority_bucket",
]
