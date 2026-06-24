from __future__ import annotations

import secrets
from typing import Dict, List, Optional

from .models import WorkflowExecution, WorkflowTemplate


class InMemoryWorkflowStore:
    def __init__(self) -> None:
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._executions: Dict[str, WorkflowExecution] = {}

    def save_template(self, template: WorkflowTemplate) -> None:
        self._templates[template.template_id] = template

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        return self._templates.get(template_id)

    def get_templates_for_event(self, event_trigger: str) -> List[WorkflowTemplate]:
        return [t for t in self._templates.values()
                if t.event_trigger == event_trigger and t.enabled]

    def list_templates(self) -> List[WorkflowTemplate]:
        return list(self._templates.values())

    def save_execution(self, execution: WorkflowExecution) -> None:
        self._executions[execution.execution_id] = execution

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        return self._executions.get(execution_id)

    def list_executions(self, tenant_id: str) -> List[WorkflowExecution]:
        return [e for e in self._executions.values() if e.tenant_id == tenant_id]

    def new_id(self, prefix: str = "") -> str:
        return f"{prefix}-{secrets.token_urlsafe(8)}" if prefix else secrets.token_urlsafe(10)
