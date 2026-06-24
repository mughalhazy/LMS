from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import ActionItem, DailyActionList, OperationalMetric

# BC-OPS-02: Three-tier thresholds (config-driven in prod)
TIER_THRESHOLDS = {
    "attendance_rate": {"CRITICAL": 60, "IMPORTANT": 70},
    "fee_collection_rate": {"CRITICAL": 70, "IMPORTANT": 80},
    "batch_health": {"CRITICAL": 50, "IMPORTANT": 70},
}


class OperationsOSService:
    def __init__(self) -> None:
        self._metrics: List[OperationalMetric] = []
        self._action_items: List[ActionItem] = {}
        self._daily_lists: Dict[str, DailyActionList] = {}
        self._action_items: List[ActionItem] = []

    def record_metric(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        metric = OperationalMetric(
            metric_id=f"m-{secrets.token_urlsafe(6)}",
            tenant_id=body.get("tenant_id", ""),
            metric_type=body.get("metric_type", ""),
            value=float(body.get("value", 0)),
            threshold=float(body.get("threshold", 0)),
            period=body.get("period", ""),
        )
        self._metrics.append(metric)
        # Auto-detect patterns and generate action items (BC-OPS-01)
        self._detect_patterns(metric)
        return 201, {"metric_id": metric.metric_id, "metric_type": metric.metric_type,
                     "value": metric.value}

    def get_daily_action_list(self, operator_id: str, tenant_id: str, date: str) -> Tuple[int, Dict[str, Any]]:
        key = f"{tenant_id}:{operator_id}:{date}"
        if key not in self._daily_lists:
            self._generate_daily_list(operator_id, tenant_id, date)
        dal = self._daily_lists[key]
        return 200, self._serialize_dal(dal)

    def get_action_queue(self, operator_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        items = [i for i in self._action_items
                 if i.tenant_id == tenant_id and (i.operator_id == operator_id or i.operator_id == "*")]
        # BC-OPS-02: sort by tier — CRITICAL first
        tier_order = {"CRITICAL": 0, "IMPORTANT": 1, "OPTIONAL": 2}
        items.sort(key=lambda i: tier_order.get(i.tier, 99))
        return 200, {
            "operator_id": operator_id, "tenant_id": tenant_id,
            "actions": [self._serialize_item(i) for i in items],
            "critical_count": sum(1 for i in items if i.tier == "CRITICAL"),
            "important_count": sum(1 for i in items if i.tier == "IMPORTANT"),
            "optional_count": sum(1 for i in items if i.tier == "OPTIONAL"),
        }

    def _detect_patterns(self, metric: OperationalMetric) -> None:
        thresholds = TIER_THRESHOLDS.get(metric.metric_type, {})
        tier = None
        if thresholds.get("CRITICAL") and metric.value < thresholds["CRITICAL"]:
            tier = "CRITICAL"
        elif thresholds.get("IMPORTANT") and metric.value < thresholds["IMPORTANT"]:
            tier = "IMPORTANT"

        if tier:
            # BC-OPS-01: pattern with implication and suggested action
            item = ActionItem(
                item_id=f"ai-{secrets.token_urlsafe(6)}",
                tier=tier,
                title=f"{metric.metric_type.replace('_', ' ').title()} below threshold",
                description=f"Current value {metric.value:.1f}% is below {metric.threshold:.1f}% threshold",
                pattern=f"{metric.metric_type} dropped to {metric.value:.1f}%",
                implication=f"Operational risk — action required to restore normal levels",
                action_command=f"review_{metric.metric_type}",
                entity_ref=f"{metric.metric_type}:{metric.period}",
                operator_id="*",
                tenant_id=metric.tenant_id,
            )
            self._action_items.append(item)

    def _generate_daily_list(self, operator_id: str, tenant_id: str, date: str) -> None:
        key = f"{tenant_id}:{operator_id}:{date}"
        all_items = [i for i in self._action_items
                     if i.tenant_id == tenant_id and (i.operator_id == operator_id or i.operator_id == "*")]
        dal = DailyActionList(
            list_id=f"dal-{secrets.token_urlsafe(6)}",
            operator_id=operator_id, tenant_id=tenant_id, date=date,
            critical=[i for i in all_items if i.tier == "CRITICAL"],
            important=[i for i in all_items if i.tier == "IMPORTANT"],
            optional=[i for i in all_items if i.tier == "OPTIONAL"],
        )
        self._daily_lists[key] = dal

    def _serialize_dal(self, dal: DailyActionList) -> Dict[str, Any]:
        return {
            "list_id": dal.list_id, "operator_id": dal.operator_id,
            "tenant_id": dal.tenant_id, "date": dal.date,
            "critical": [self._serialize_item(i) for i in dal.critical],
            "important": [self._serialize_item(i) for i in dal.important],
            "optional": [self._serialize_item(i) for i in dal.optional],
            "generated_at": dal.generated_at.isoformat(),
        }

    def _serialize_item(self, i: ActionItem) -> Dict[str, Any]:
        return {
            "item_id": i.item_id, "tier": i.tier, "title": i.title,
            "description": i.description, "pattern": i.pattern,
            "implication": i.implication, "action_command": i.action_command,
        }
