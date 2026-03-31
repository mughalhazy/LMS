from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.config import ConfigResolutionContext

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ConfigModule = _load_module("workflow_engine_config_service", "services/config-service/service.py")
_NotificationModule = _load_module("workflow_engine_notification_service", "services/notification-service/orchestration.py")
_AcademyOpsModule = _load_module("workflow_engine_academy_ops_service", "services/academy-ops/service.py")
_PaymentsModule = _load_module("workflow_engine_payments_orchestration", "integrations/payments/orchestration.py")
_PaymentsBaseModule = _load_module("workflow_engine_payments_base", "integrations/payments/base_adapter.py")

ConfigService = _ConfigModule.ConfigService
NotificationOrchestrator = _NotificationModule.NotificationOrchestrator
AcademyOpsService = _AcademyOpsModule.AcademyOpsService
PaymentOrchestrationService = _PaymentsModule.PaymentOrchestrationService
build_pakistan_payment_orchestration = _PaymentsModule.build_pakistan_payment_orchestration
TenantPaymentContext = _PaymentsBaseModule.TenantPaymentContext

WorkflowStepType = Literal["notify", "wait", "escalate", "academy_ops", "payment"]


@dataclass(frozen=True)
class WorkflowTriggerEvent:
    event_id: str
    tenant_id: str
    country_code: str
    segment_id: str
    trigger_type: str
    actor_user_id: str
    context: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class WorkflowRule:
    rule_id: str
    trigger_type: str
    required_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    step_type: WorkflowStepType
    delay_seconds: int = 0
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    enabled: bool
    rules: tuple[WorkflowRule, ...]
    steps: tuple[WorkflowStep, ...]


@dataclass
class ScheduledStep:
    workflow_id: str
    event_id: str
    tenant_id: str
    country_code: str
    actor_user_id: str
    step: WorkflowStep
    due_at: datetime


class WorkflowEngine:
    """Orchestration-only workflow engine.

    Evaluates trigger/rule matching, resolves config-driven policy, schedules multi-step
    flows, and executes eligible orchestration actions through notification-service.
    """

    def __init__(
        self,
        *,
        config_service: ConfigService | None = None,
        notification_orchestrator: NotificationOrchestrator | None = None,
        academy_ops_service: AcademyOpsService | None = None,
        payment_orchestration_service: PaymentOrchestrationService | None = None,
    ) -> None:
        self._config_service = config_service or ConfigService()
        self._notification_orchestrator = notification_orchestrator or NotificationOrchestrator()
        self._academy_ops_service = academy_ops_service or AcademyOpsService()
        self._payment_orchestration_service = payment_orchestration_service or build_pakistan_payment_orchestration()
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._scheduled_steps: list[ScheduledStep] = []

    def register_workflow(self, definition: WorkflowDefinition) -> None:
        self._workflows[definition.workflow_id] = definition

    def list_scheduled_steps(self) -> tuple[ScheduledStep, ...]:
        return tuple(sorted(self._scheduled_steps, key=lambda item: item.due_at))

    def _resolve_rules(self, event: WorkflowTriggerEvent) -> dict[str, Any]:
        effective = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=event.tenant_id,
                country_code=event.country_code,
                segment_id=event.segment_id,
            )
        )
        return effective.behavior_tuning.get("workflow_engine", {})

    def _rule_matches(self, *, rule: WorkflowRule, event: WorkflowTriggerEvent) -> bool:
        if rule.trigger_type != event.trigger_type:
            return False
        for key, expected in rule.required_context.items():
            if event.context.get(key) != expected:
                return False
        return True

    def handle_trigger(self, event: WorkflowTriggerEvent) -> dict[str, Any]:
        policy = self._resolve_rules(event)
        disabled = set(policy.get("disabled_workflows", []))

        trace: list[dict[str, Any]] = [{"step": "trigger.received", "event_id": event.event_id}]
        scheduled: list[dict[str, Any]] = []

        for workflow in self._workflows.values():
            if not workflow.enabled or workflow.workflow_id in disabled:
                continue

            if not any(self._rule_matches(rule=rule, event=event) for rule in workflow.rules):
                continue

            trace.append({"step": "workflow.matched", "workflow_id": workflow.workflow_id})
            for wf_step in workflow.steps:
                due_at = event.occurred_at + timedelta(seconds=max(0, wf_step.delay_seconds))
                scheduled_step = ScheduledStep(
                    workflow_id=workflow.workflow_id,
                    event_id=event.event_id,
                    tenant_id=event.tenant_id,
                    country_code=event.country_code,
                    actor_user_id=event.actor_user_id,
                    step=wf_step,
                    due_at=due_at,
                )
                self._scheduled_steps.append(scheduled_step)
                scheduled.append(
                    {
                        "workflow_id": workflow.workflow_id,
                        "step_id": wf_step.step_id,
                        "step_type": wf_step.step_type,
                        "due_at": due_at.isoformat(),
                    }
                )
                trace.append({"step": "step.scheduled", "step_id": wf_step.step_id, "workflow_id": workflow.workflow_id})

        return {"scheduled": scheduled, "trace": trace}

    def handle_event_envelope(self, envelope: dict[str, Any]) -> dict[str, Any]:
        metadata = envelope.get("metadata") or {}
        actor = metadata.get("actor") or {}
        payload = envelope.get("payload") or {}
        timestamp = envelope.get("timestamp")
        occurred_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if isinstance(timestamp, str) else None

        trigger_event = WorkflowTriggerEvent(
            event_id=str(envelope.get("event_id", "")),
            tenant_id=str(envelope.get("tenant_id", "")),
            country_code=str(payload.get("country_code") or metadata.get("source_region", "PK")).upper(),
            segment_id=str(payload.get("segment_id") or "academy"),
            trigger_type=str(envelope.get("event_type", "")),
            actor_user_id=str(actor.get("user_id") or payload.get("actor_user_id") or "system"),
            context=dict(payload.get("context") or payload),
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
        return self.handle_trigger(trigger_event)

    def run_due(self, *, now: datetime | None = None) -> dict[str, Any]:
        current_time = now or datetime.now(timezone.utc)

        due = [item for item in self._scheduled_steps if item.due_at <= current_time]
        pending = [item for item in self._scheduled_steps if item.due_at > current_time]
        self._scheduled_steps = pending

        trace: list[dict[str, Any]] = []
        executions: list[dict[str, Any]] = []

        for item in sorted(due, key=lambda step: step.due_at):
            trace.append({"step": "step.started", "workflow_id": item.workflow_id, "step_id": item.step.step_id})

            if item.step.step_type == "notify":
                message = str(item.step.config.get("message", "workflow notification"))
                delivery = self._notification_orchestrator.send_notification(
                    tenant_country_code=item.country_code,
                    user_id=item.actor_user_id,
                    message=message,
                )
                result = {
                    "status": "sent" if delivery.ok else "failed",
                    "provider": delivery.provider,
                    "fallback_used": delivery.fallback_used,
                    "error": delivery.error,
                }
            elif item.step.step_type in {"wait", "escalate"}:
                result = {
                    "status": "orchestrated",
                    "action": item.step.step_type,
                    "detail": item.step.config,
                }
            elif item.step.step_type == "academy_ops":
                operation = str(item.step.config.get("operation", "run_qc_autofix"))
                if operation == "run_qc_autofix":
                    result = {
                        "status": "orchestrated",
                        "action": "academy_ops.run_qc_autofix",
                        "detail": self._academy_ops_service.run_qc_autofix(),
                    }
                else:
                    result = {"status": "skipped", "reason": "unsupported_academy_ops_operation"}
            elif item.step.step_type == "payment":
                amount = int(item.step.config.get("amount", 0))
                currency = str(item.step.config.get("currency", "PKR"))
                invoice_id = item.step.config.get("invoice_id")
                idempotency_key = str(item.step.config.get("idempotency_key") or f"{item.event_id}:{item.step.step_id}")
                payment_entry = self._payment_orchestration_service.process_checkout_payment(
                    idempotency_key=idempotency_key,
                    tenant=TenantPaymentContext(tenant_id=item.tenant_id, country_code=item.country_code),
                    amount=amount,
                    currency=currency,
                    invoice_id=str(invoice_id) if invoice_id is not None else None,
                )
                result = {
                    "status": payment_entry.status,
                    "provider": payment_entry.provider,
                    "payment_id": payment_entry.payment_id,
                    "verified": payment_entry.verified,
                    "error": payment_entry.error,
                }
            else:
                result = {"status": "skipped", "reason": "unsupported_step_type"}

            executions.append(
                {
                    "workflow_id": item.workflow_id,
                    "event_id": item.event_id,
                    "step_id": item.step.step_id,
                    "result": result,
                }
            )
            trace.append({"step": "step.completed", "workflow_id": item.workflow_id, "step_id": item.step.step_id})

        return {
            "executed": executions,
            "pending_count": len(self._scheduled_steps),
            "trace": trace,
        }

    def run_qc_autofix(self) -> dict[str, bool]:
        if self._notification_orchestrator is None:
            self._notification_orchestrator = NotificationOrchestrator()
        if self._academy_ops_service is None:
            self._academy_ops_service = AcademyOpsService()
        if self._payment_orchestration_service is None:
            self._payment_orchestration_service = build_pakistan_payment_orchestration()

        can_handle_event_envelopes = callable(getattr(self, "handle_event_envelope", None))
        rule_evaluation_enabled = callable(getattr(self, "_rule_matches", None))
        multi_step_execution_enabled = callable(getattr(self, "run_due", None))

        integration_ready = {
            "notification": hasattr(self._notification_orchestrator, "send_notification"),
            "academy_ops": hasattr(self._academy_ops_service, "run_qc_autofix"),
            "payments": hasattr(self._payment_orchestration_service, "process_checkout_payment"),
        }
        return {
            "event_driven_triggers": can_handle_event_envelopes,
            "rule_evaluation": rule_evaluation_enabled,
            "multi_step_execution": multi_step_execution_enabled,
            "notification_integration": integration_ready["notification"],
            "academy_ops_integration": integration_ready["academy_ops"],
            "payments_integration": integration_ready["payments"],
        }
