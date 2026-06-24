from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowStep:
    step_id: str
    action_type: str          # call_service | emit_event | send_notification | wait
    target_service: str
    action_payload: Dict[str, Any] = field(default_factory=dict)
    retry_limit: int = 3
    requires_approval: bool = False


@dataclass
class WorkflowTemplate:
    template_id: str
    name: str
    event_trigger: str        # e.g. enrollment.completed
    steps: List[WorkflowStep]
    enabled: bool = True
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowExecution:
    execution_id: str
    template_id: str
    event_trigger: str
    tenant_id: str
    trigger_payload: Dict[str, Any]
    status: str               # pending | running | completed | failed | awaiting_approval
    current_step: int = 0
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
