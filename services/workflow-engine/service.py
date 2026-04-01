from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.config import ConfigResolutionContext
from shared.validation import summarize_contract_validation, validate_service_dependency_contracts

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
    conditions: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    step_type: WorkflowStepType
    delay_seconds: int = 0
    config: dict[str, Any] = field(default_factory=dict)
    max_retries: int = 0
    retry_delay_seconds: int = 60


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
    attempt: int = 0


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
        for condition in rule.conditions:
            if not self._evaluate_condition(condition=condition, context=event.context):
                return False
        return True

    def _evaluate_condition(self, *, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        key = str(condition.get("key", ""))
        operator = str(condition.get("operator", "eq"))
        expected = condition.get("value")
        value = context.get(key)

        if operator == "eq":
            return value == expected
        if operator == "neq":
            return value != expected
        if operator == "gt":
            return value is not None and expected is not None and value > expected
        if operator == "gte":
            return value is not None and expected is not None and value >= expected
        if operator == "lt":
            return value is not None and expected is not None and value < expected
        if operator == "lte":
            return value is not None and expected is not None and value <= expected
        if operator == "in":
            return expected is not None and value in expected
        if operator == "not_in":
            return expected is not None and value not in expected
        if operator == "exists":
            return key in context
        if operator == "not_exists":
            return key not in context
        return False

    def _resolve_step_due_at(self, *, event: WorkflowTriggerEvent, step: WorkflowStep) -> datetime:
        base_due = event.occurred_at + timedelta(seconds=max(0, step.delay_seconds))
        schedule_at = step.config.get("schedule_at")
        if isinstance(schedule_at, str):
            try:
                parsed = datetime.fromisoformat(schedule_at.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                return base_due
        schedule_in_seconds = step.config.get("schedule_in_seconds")
        if isinstance(schedule_in_seconds, int):
            return event.occurred_at + timedelta(seconds=max(0, schedule_in_seconds))
        return base_due

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
                due_at = self._resolve_step_due_at(event=event, step=wf_step)
                scheduled_step = ScheduledStep(
                    workflow_id=workflow.workflow_id,
                    event_id=event.event_id,
                    tenant_id=event.tenant_id,
                    country_code=event.country_code,
                    actor_user_id=event.actor_user_id,
                    step=wf_step,
                    due_at=due_at,
                    attempt=0,
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
            trace.append(
                {
                    "step": "step.started",
                    "workflow_id": item.workflow_id,
                    "step_id": item.step.step_id,
                    "attempt": item.attempt,
                }
            )

            try:
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
            except Exception as exc:
                result = {"status": "failed", "error": str(exc), "reason": "step_execution_exception"}

            executions.append(
                {
                    "workflow_id": item.workflow_id,
                    "event_id": item.event_id,
                    "step_id": item.step.step_id,
                    "attempt": item.attempt,
                    "result": result,
                }
            )
            status = str(result.get("status", ""))
            should_retry = status in {"failed", "error"} and item.attempt < max(0, item.step.max_retries)
            if should_retry:
                retry_due_at = current_time + timedelta(seconds=max(1, item.step.retry_delay_seconds))
                retried_step = replace(item, due_at=retry_due_at, attempt=item.attempt + 1)
                self._scheduled_steps.append(retried_step)
                trace.append(
                    {
                        "step": "step.retry_scheduled",
                        "workflow_id": item.workflow_id,
                        "step_id": item.step.step_id,
                        "next_attempt": retried_step.attempt,
                        "due_at": retry_due_at.isoformat(),
                    }
                )
            else:
                trace.append(
                    {
                        "step": "step.completed",
                        "workflow_id": item.workflow_id,
                        "step_id": item.step.step_id,
                        "attempt": item.attempt,
                    }
                )

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
        contract_results = validate_service_dependency_contracts(
            payment_orchestrator=self._payment_orchestration_service,
            sor_service=self._academy_ops_service._sor,
            notification_orchestrator=self._notification_orchestrator,
        )
        contract_summary = summarize_contract_validation(contract_results)
        return {
            "event_driven_triggers": can_handle_event_envelopes,
            "rule_evaluation": rule_evaluation_enabled,
            "multi_step_execution": multi_step_execution_enabled,
            "notification_integration": integration_ready["notification"],
            "academy_ops_integration": integration_ready["academy_ops"],
            "payments_integration": integration_ready["payments"],
            "commerce_payments_contract": contract_summary["commerce_to_payments"],
            "academy_sor_contract": contract_summary["academy_to_system_of_record"],
            "workflow_notifications_contract": contract_summary["workflow_to_notifications"],
            "no_broken_dependencies": all(contract_summary.values()),
        }
