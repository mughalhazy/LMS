from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Protocol

from shared.models.workflow import WorkflowAction, WorkflowActionResult, WorkflowDefinition

from app.schemas import NotificationOrchestrationRequest


class WorkflowNotificationGateway(Protocol):
    raised_alerts: list[dict[str, Any]]
    follow_up_tasks: list[dict[str, Any]]

    def orchestrate_notification(
        self,
        req: NotificationOrchestrationRequest,
        event_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...


class WorkflowEngine:
    def __init__(self, notification_gateway: WorkflowNotificationGateway) -> None:
        self.notification_gateway = notification_gateway

    def execute(
        self,
        tenant_id: str,
        workflows: list[WorkflowDefinition],
        context: dict[str, Any],
        *,
        tenant_country_code: str = "ZZ",
    ) -> dict[str, Any]:
        matched = 0
        action_results: list[WorkflowActionResult] = []
        for workflow in workflows:
            if not workflow.enabled:
                continue
            if not self._trigger_matches(workflow, context):
                continue
            matched += 1
            for action in workflow.actions:
                action_results.append(
                    self._execute_action(
                        tenant_id=tenant_id,
                        workflow=workflow,
                        action=action,
                        context=context,
                        tenant_country_code=tenant_country_code,
                    )
                )

        return {
            "tenant_id": tenant_id,
            "matched_workflows": matched,
            "executed_actions": len(action_results),
            "results": [asdict(result) for result in action_results],
        }

    def _trigger_matches(self, workflow: WorkflowDefinition, context: dict[str, Any]) -> bool:
        trigger = workflow.trigger
        if trigger.trigger_type == "low_performance":
            threshold = float(trigger.config.get("threshold", 70.0))
            score = float(context.get("performance_score", 100.0))
            return score < threshold
        if trigger.trigger_type == "missed_payment":
            payment_status = str(context.get("payment_status", "")).lower()
            return bool(context.get("payment_missed")) or payment_status in {"missed", "failed", "overdue"}
        if trigger.trigger_type == "inactivity":
            threshold_days = int(trigger.config.get("days", 14))
            inactive_days = int(context.get("inactive_days", 0))
            return inactive_days >= threshold_days
        if trigger.trigger_type == "conversation_step":
            expected_step = str(trigger.config.get("step", "start"))
            current_step = str(context.get("current_step", "start"))
            return current_step == expected_step
        return False

    def _execute_action(
        self,
        *,
        tenant_id: str,
        workflow: WorkflowDefinition,
        action: WorkflowAction,
        context: dict[str, Any],
        tenant_country_code: str,
    ) -> WorkflowActionResult:
        action_config = action.config
        if action.action_type == "send_notification":
            recipients = action_config.get("recipients") or context.get("recipients") or []
            status, payload = self.notification_gateway.orchestrate_notification(
                NotificationOrchestrationRequest(
                    tenant_id=tenant_id,
                    tenant_country_code=tenant_country_code,
                    category=str(action_config.get("category", "workflow")),
                    recipients=list(recipients),
                    channels=list(action_config.get("channels", ["push"])),
                    subject=str(action_config.get("subject", f"Workflow triggered: {workflow.name}")),
                    body=str(action_config.get("body", "A workflow condition was met.")),
                    metadata={
                        "workflow_id": workflow.workflow_id,
                        "trigger": workflow.trigger.trigger_type,
                        "context": context,
                    },
                )
            )
            return WorkflowActionResult(
                workflow_id=workflow.workflow_id,
                action_type=action.action_type,
                status="executed" if status == 202 else "failed",
                detail=payload,
            )

        if action.action_type == "raise_alert":
            alert = {
                "tenant_id": tenant_id,
                "workflow_id": workflow.workflow_id,
                "severity": action_config.get("severity", "high"),
                "message": action_config.get("message", f"Workflow alert: {workflow.name}"),
                "context": context,
                "raised_at": datetime.utcnow().isoformat(),
            }
            self.notification_gateway.raised_alerts.append(alert)
            return WorkflowActionResult(
                workflow_id=workflow.workflow_id,
                action_type=action.action_type,
                status="executed",
                detail=alert,
            )

        task = {
            "tenant_id": tenant_id,
            "workflow_id": workflow.workflow_id,
            "task_type": action_config.get("task_type", "follow_up"),
            "title": action_config.get("title", f"Follow up: {workflow.name}"),
            "assignee": action_config.get("assignee", "ops-team"),
            "due_in_days": int(action_config.get("due_in_days", 2)),
            "context": context,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.notification_gateway.follow_up_tasks.append(task)
        return WorkflowActionResult(
            workflow_id=workflow.workflow_id,
            action_type=action.action_type,
            status="executed",
            detail=task,
        )
