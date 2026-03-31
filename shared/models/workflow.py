from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

WorkflowTriggerType = Literal["low_performance", "missed_payment", "inactivity"]
WorkflowActionType = Literal["send_notification", "raise_alert", "create_follow_up_task"]


@dataclass(frozen=True)
class WorkflowTrigger:
    trigger_type: WorkflowTriggerType
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowAction:
    action_type: WorkflowActionType
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    trigger: WorkflowTrigger
    actions: list[WorkflowAction]
    enabled: bool = True


@dataclass
class WorkflowActionResult:
    workflow_id: str
    action_type: WorkflowActionType
    status: str
    detail: dict[str, Any]
    executed_at: datetime = field(default_factory=datetime.utcnow)
