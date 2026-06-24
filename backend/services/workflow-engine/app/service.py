from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import WorkflowExecution, WorkflowStep, WorkflowTemplate
from .store import InMemoryWorkflowStore

# BC-WF-01: Default-on workflow automations
DEFAULT_TEMPLATES = [
    {
        "template_id": "wf-enrollment-completed",
        "name": "Enrollment Completed",
        "event_trigger": "enrollment.completed",
        "enabled": True,
        "description": "Certificate issuance + congratulations notification on enrollment completion",
        "steps": [
            {"step_id": "s1", "action_type": "call_service", "target_service": "certificate-service",
             "action_payload": {"action": "issue_certificate"}},
            {"step_id": "s2", "action_type": "send_notification", "target_service": "notification-service",
             "action_payload": {"template": "congratulations"}},
        ],
    },
    {
        "template_id": "wf-assessment-failed",
        "name": "Assessment Failed",
        "event_trigger": "assessment.failed",
        "enabled": True,
        "description": "Remediation suggestion to learner + instructor alert on assessment failure",
        "steps": [
            {"step_id": "s1", "action_type": "send_notification", "target_service": "notification-service",
             "action_payload": {"template": "remediation_suggestion", "recipient": "learner"}},
            {"step_id": "s2", "action_type": "send_notification", "target_service": "notification-service",
             "action_payload": {"template": "assessment_failed_alert", "recipient": "instructor"}},
        ],
    },
    {
        "template_id": "wf-learner-inactivity",
        "name": "Learner Inactivity",
        "event_trigger": "learner.inactivity_threshold_crossed",
        "enabled": True,
        "description": "Re-engagement notification after configurable inactivity period (default 7 days)",
        "steps": [
            {"step_id": "s1", "action_type": "send_notification", "target_service": "notification-service",
             "action_payload": {"template": "re_engagement"}},
        ],
    },
    {
        "template_id": "wf-fee-overdue",
        "name": "Fee Overdue",
        "event_trigger": "fee.overdue_threshold_crossed",
        "enabled": True,
        "description": "Fee reminder to student/guardian after 7 days overdue",
        "steps": [
            {"step_id": "s1", "action_type": "send_notification", "target_service": "notification-service",
             "action_payload": {"template": "fee_reminder"}},
        ],
    },
    {
        "template_id": "wf-student-absence",
        "name": "Student Absence Threshold",
        "event_trigger": "student.absence_threshold_crossed",
        "enabled": True,
        "description": "Admin alert + optional student nudge after 3 consecutive absences",
        "steps": [
            {"step_id": "s1", "action_type": "send_notification", "target_service": "notification-service",
             "action_payload": {"template": "absence_alert", "recipient": "admin"}},
        ],
    },
    {
        "template_id": "wf-batch-capacity",
        "name": "Batch Capacity Alert",
        "event_trigger": "batch.capacity_below_threshold",
        "enabled": True,
        "description": "Admin alert + optional open-seat notification when batch below capacity",
        "steps": [
            {"step_id": "s1", "action_type": "send_notification", "target_service": "notification-service",
             "action_payload": {"template": "capacity_alert", "recipient": "admin"}},
        ],
    },
]


class WorkflowEngineService:
    def __init__(self, store: InMemoryWorkflowStore) -> None:
        self.store = store
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        for td in DEFAULT_TEMPLATES:
            steps = [WorkflowStep(**s) for s in td["steps"]]
            t = WorkflowTemplate(
                template_id=td["template_id"], name=td["name"],
                event_trigger=td["event_trigger"], steps=steps,
                enabled=td["enabled"], description=td["description"],
            )
            self.store.save_template(t)

    def register_template(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        steps = [WorkflowStep(**s) for s in body.get("steps", [])]
        template = WorkflowTemplate(
            template_id=body.get("template_id") or self.store.new_id("wf"),
            name=body.get("name", ""),
            event_trigger=body.get("event_trigger", ""),
            steps=steps,
            enabled=body.get("enabled", True),
            description=body.get("description", ""),
        )
        self.store.save_template(template)
        return 200, self._serialize_template(template)

    def trigger(self, event_trigger: str, tenant_id: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        templates = self.store.get_templates_for_event(event_trigger)
        if not templates:
            return 200, {"triggered": 0, "message": "no_templates_for_event", "event": event_trigger}

        executions = []
        for template in templates:
            execution = WorkflowExecution(
                execution_id=self.store.new_id("exec"),
                template_id=template.template_id,
                event_trigger=event_trigger,
                tenant_id=tenant_id,
                trigger_payload=payload,
                status="running",
            )
            # Execute each step (simulated — in prod these would call downstream services)
            for i, step in enumerate(template.steps):
                execution.current_step = i
                execution.step_results.append({
                    "step_id": step.step_id,
                    "action_type": step.action_type,
                    "target_service": step.target_service,
                    "status": "completed",
                })
            execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc)
            self.store.save_execution(execution)
            executions.append(execution.execution_id)

        return 202, {"triggered": len(executions), "event": event_trigger,
                     "execution_ids": executions, "tenant_id": tenant_id}

    def enable_template(self, template_id: str, enabled: bool) -> Tuple[int, Dict[str, Any]]:
        template = self.store.get_template(template_id)
        if not template:
            return 404, {"error": "template_not_found"}
        template.enabled = enabled
        self.store.save_template(template)
        return 200, {"template_id": template_id, "enabled": enabled}

    def get_execution(self, execution_id: str) -> Tuple[int, Dict[str, Any]]:
        execution = self.store.get_execution(execution_id)
        if not execution:
            return 404, {"error": "execution_not_found"}
        return 200, self._serialize_execution(execution)

    def list_templates(self) -> Tuple[int, Dict[str, Any]]:
        templates = self.store.list_templates()
        return 200, {"templates": [self._serialize_template(t) for t in templates], "count": len(templates)}

    def list_executions(self, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        executions = self.store.list_executions(tenant_id)
        return 200, {"executions": [self._serialize_execution(e) for e in executions]}

    def _serialize_template(self, t: WorkflowTemplate) -> Dict[str, Any]:
        return {
            "template_id": t.template_id, "name": t.name,
            "event_trigger": t.event_trigger, "enabled": t.enabled,
            "description": t.description,
            "steps": [{"step_id": s.step_id, "action_type": s.action_type,
                        "target_service": s.target_service} for s in t.steps],
        }

    def _serialize_execution(self, e: WorkflowExecution) -> Dict[str, Any]:
        return {
            "execution_id": e.execution_id, "template_id": e.template_id,
            "event_trigger": e.event_trigger, "tenant_id": e.tenant_id,
            "status": e.status, "current_step": e.current_step,
            "step_results": e.step_results,
            "started_at": e.started_at.isoformat(),
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        }
