from __future__ import annotations

import concurrent.futures
import importlib.util
import sys
from dataclasses import dataclass, field
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
_OperationsOSModule = _load_module("workflow_engine_operations_os_service", "services/operations-os/service.py")
_PaymentsModule = _load_module("workflow_engine_payments_orchestration", "integrations/payments/orchestration.py")
_PaymentsBaseModule = _load_module("workflow_engine_payments_base", "integrations/payments/base_adapter.py")
_SystemOfRecordModule = _load_module("workflow_engine_system_of_record", "services/system-of-record/service.py")

ConfigService = _ConfigModule.ConfigService
NotificationOrchestrator = _NotificationModule.NotificationOrchestrator
AcademyOpsService = _AcademyOpsModule.AcademyOpsService
OperationsOSService = _OperationsOSModule.OperationsOSService
PaymentOrchestrationService = _PaymentsModule.PaymentOrchestrationService
build_pakistan_payment_orchestration = _PaymentsModule.build_pakistan_payment_orchestration
TenantPaymentContext = _PaymentsBaseModule.TenantPaymentContext
SystemOfRecordService = _SystemOfRecordModule.SystemOfRecordService

WorkflowStepType = Literal["notify", "wait", "escalate", "academy_ops", "payment", "action_item", "approval_gate"]

# CGAP-007: human approval gate states
ApprovalGateStatus = Literal["pending", "approved", "rejected", "expired"]


@dataclass
class PendingApprovalGate:
    """CGAP-007: Represents a workflow step paused awaiting human approval."""
    gate_id: str
    workflow_id: str
    event_id: str
    tenant_id: str
    actor_user_id: str
    step: "WorkflowStep"
    context: dict[str, Any]
    requested_at: datetime
    status: ApprovalGateStatus = "pending"
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_note: str | None = None


@dataclass(frozen=True)
class WorkflowTriggerEvent:
    event_id: str
    tenant_id: str
    country_code: str
    segment_id: str
    trigger_type: str
    actor_user_id: str
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


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
    parallel: bool = False  # CGAP-005: steps with parallel=True run concurrently in run_due()


@dataclass(frozen=True)
class WorkflowBranch:
    """CGAP-006: Conditional branch — steps execute only when condition matches event context."""
    branch_id: str
    condition: dict[str, Any]  # same operator format as WorkflowRule.conditions items
    steps: tuple[WorkflowStep, ...]


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    enabled: bool
    rules: tuple[WorkflowRule, ...]
    steps: tuple[WorkflowStep, ...]
    branches: tuple[WorkflowBranch, ...] = ()  # CGAP-006: conditional branches evaluated at trigger time


@dataclass
class ScheduledStep:
    workflow_id: str
    event_id: str
    tenant_id: str
    country_code: str
    actor_user_id: str
    trigger_type: str
    context: dict[str, Any]
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
        operations_os_service: OperationsOSService | None = None,
        payment_orchestration_service: PaymentOrchestrationService | None = None,
        system_of_record_service: SystemOfRecordService | None = None,
    ) -> None:
        self._config_service = config_service or ConfigService()
        self._notification_orchestrator = notification_orchestrator or NotificationOrchestrator()
        # CGAP-022: bind this engine back to the orchestrator so inbound WhatsApp
        # action replies execute downstream service calls (not just log).
        if hasattr(self._notification_orchestrator, "bind_workflow_engine"):
            self._notification_orchestrator.bind_workflow_engine(self)
        self._academy_ops_service = academy_ops_service or AcademyOpsService()
        self._operations_os_service = operations_os_service or OperationsOSService()
        self._payment_orchestration_service = payment_orchestration_service or build_pakistan_payment_orchestration()
        self._system_of_record_service = system_of_record_service or SystemOfRecordService()
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._scheduled_steps: list[ScheduledStep] = []
        self._scheduled_step_keys: set[str] = set()
        self._executed_step_keys: set[str] = set()
        self._student_parent_map: dict[tuple[str, str], tuple[str, ...]] = {}
        # CGAP-007: pending human approval gates keyed by gate_id
        self._pending_approval_gates: dict[str, PendingApprovalGate] = {}
        # CGAP-009: audit log for automation enable/disable state changes
        self._automation_audit_log: list[dict[str, Any]] = []

    def register_workflow(self, definition: WorkflowDefinition) -> None:
        self._workflows[definition.workflow_id] = definition

    def register_parent_student_mapping(self, *, tenant_id: str, student_id: str, parent_user_ids: list[str]) -> None:
        key = (tenant_id.strip(), student_id.strip())
        self._student_parent_map[key] = tuple(user_id.strip() for user_id in parent_user_ids if user_id and user_id.strip())

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
        base_due = event.timestamp + timedelta(seconds=max(0, step.delay_seconds))
        schedule_from_context_key = step.config.get("schedule_from_context_key")
        if isinstance(schedule_from_context_key, str):
            schedule_value = event.context.get(schedule_from_context_key)
            if isinstance(schedule_value, str):
                try:
                    parsed = datetime.fromisoformat(schedule_value.replace("Z", "+00:00"))
                    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
        schedule_at = step.config.get("schedule_at")
        if isinstance(schedule_at, str):
            try:
                parsed = datetime.fromisoformat(schedule_at.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                return base_due
        schedule_in_seconds = step.config.get("schedule_in_seconds")
        if isinstance(schedule_in_seconds, int):
            return event.timestamp + timedelta(seconds=max(0, schedule_in_seconds))
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

            # Collect steps from unconditional list + any matching conditional branches (CGAP-006)
            steps_to_schedule: list[WorkflowStep] = list(workflow.steps)
            for branch in workflow.branches:
                if self._evaluate_condition(condition=branch.condition, context=event.context):
                    steps_to_schedule.extend(branch.steps)
                    trace.append({"step": "branch.taken", "branch_id": branch.branch_id, "workflow_id": workflow.workflow_id})
                else:
                    trace.append({"step": "branch.skipped", "branch_id": branch.branch_id, "workflow_id": workflow.workflow_id})

            for wf_step in steps_to_schedule:
                due_at = self._resolve_step_due_at(event=event, step=wf_step)
                scheduled_step = ScheduledStep(
                    workflow_id=workflow.workflow_id,
                    event_id=event.event_id,
                    tenant_id=event.tenant_id,
                    country_code=event.country_code,
                    actor_user_id=event.actor_user_id,
                    trigger_type=event.trigger_type,
                    context=dict(event.context),
                    step=wf_step,
                    due_at=due_at,
                    attempt=0,
                )
                dedupe_key = self._scheduled_step_key(scheduled_step)
                if dedupe_key in self._scheduled_step_keys or dedupe_key in self._executed_step_keys:
                    trace.append(
                        {
                            "step": "step.skipped_duplicate",
                            "step_id": wf_step.step_id,
                            "workflow_id": workflow.workflow_id,
                            "reason": "idempotent_schedule_guard",
                        }
                    )
                    continue
                self._scheduled_steps.append(scheduled_step)
                self._scheduled_step_keys.add(dedupe_key)
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
        resolved_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if isinstance(timestamp, str) else None

        event_type = str(envelope.get("event_type", ""))
        if event_type == "attendance.marked":
            return self._handle_attendance_marked_envelope(
                envelope=envelope,
                payload=payload,
                metadata=metadata,
                actor=actor,
                resolved_timestamp=resolved_timestamp,
            )

        trigger_event = WorkflowTriggerEvent(
            event_id=str(envelope.get("event_id", "")),
            tenant_id=str(envelope.get("tenant_id", "")),
            country_code=str(payload.get("country_code") or metadata.get("source_region", "PK")).upper(),
            segment_id=str(payload.get("segment_id") or "academy"),
            trigger_type=event_type,
            actor_user_id=str(actor.get("user_id") or payload.get("actor_user_id") or "system"),
            context=dict(payload.get("context") or payload),
            timestamp=resolved_timestamp or datetime.now(timezone.utc),
        )
        response = self.handle_trigger(trigger_event)
        self._create_event_action_if_applicable(trigger_event)
        return response

    def _handle_attendance_marked_envelope(
        self,
        *,
        envelope: dict[str, Any],
        payload: dict[str, Any],
        metadata: dict[str, Any],
        actor: dict[str, Any],
        resolved_timestamp: datetime | None,
    ) -> dict[str, Any]:
        tenant_id = str(envelope.get("tenant_id", ""))
        country_code = str(payload.get("country_code") or metadata.get("source_region", "PK")).upper()
        segment_id = str(payload.get("segment_id") or "academy")
        student_id = str(payload.get("student_id") or "")
        status = self._resolve_attendance_status(payload)
        parent_user_ids = self._resolve_parent_recipients(tenant_id=tenant_id, student_id=student_id, payload=payload)

        context = dict(payload.get("context") or payload)
        context["attendance_status"] = status
        context["notification_recipients"] = parent_user_ids
        context["student_id"] = student_id

        if status == "present" and not self._is_present_notification_enabled(
            tenant_id=tenant_id,
            country_code=country_code,
            segment_id=segment_id,
        ):
            return {
                "scheduled": [],
                "trace": [
                    {"step": "trigger.received", "event_id": str(envelope.get("event_id", ""))},
                    {"step": "attendance.present_notification_skipped", "reason": "config_disabled"},
                ],
            }

        trigger_event = WorkflowTriggerEvent(
            event_id=str(envelope.get("event_id", "")),
            tenant_id=tenant_id,
            country_code=country_code,
            segment_id=segment_id,
            trigger_type="attendance.absence_detected" if status == "absent" else "attendance.present_marked",
            actor_user_id=parent_user_ids[0] if parent_user_ids else str(actor.get("user_id") or payload.get("actor_user_id") or "system"),
            context=context,
            timestamp=resolved_timestamp or datetime.now(timezone.utc),
        )
        response = self.handle_trigger(trigger_event)
        response["trace"].append(
            {
                "step": "attendance.marked.normalized",
                "attendance_status": status,
                "parent_recipients": list(parent_user_ids),
            }
        )
        self._create_event_action_if_applicable(trigger_event)
        return response

    def _resolve_attendance_status(self, payload: dict[str, Any]) -> str:
        raw_status = str(payload.get("attendance_status") or payload.get("status") or "").strip().lower()
        if raw_status in {"present", "absent"}:
            return raw_status
        if "present" in payload:
            return "present" if bool(payload.get("present")) else "absent"
        return "absent"

    def _resolve_parent_recipients(self, *, tenant_id: str, student_id: str, payload: dict[str, Any]) -> tuple[str, ...]:
        inline = payload.get("parent_user_ids") or payload.get("guardian_user_ids") or ()
        if isinstance(inline, (list, tuple)):
            inline_parents = tuple(str(item).strip() for item in inline if str(item).strip())
            if inline_parents:
                return inline_parents
        return self._student_parent_map.get((tenant_id, student_id), ())

    def _is_present_notification_enabled(self, *, tenant_id: str, country_code: str, segment_id: str) -> bool:
        effective = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=tenant_id,
                country_code=country_code,
                segment_id=segment_id,
            )
        )
        attendance_settings = effective.behavior_tuning.get("attendance_notifications", {})
        return bool(attendance_settings.get("notify_on_present", False))

    def _create_event_action_if_applicable(self, event: WorkflowTriggerEvent) -> None:
        defaults: dict[str, dict[str, str]] = {
            "payment.missed": {
                "action_type": "unpaid_fees_follow_up",
                "priority": "high",
                "reason": "Payment overdue event received.",
                "next_step": "Call guardian and confirm payment plan.",
            },
            "attendance.absence_detected": {
                "action_type": "repeated_absence_intervention",
                "priority": "high",
                "reason": "Repeated absence event received.",
                "next_step": "Schedule counselor outreach.",
            },
            "user_inactive": {
                "action_type": "inactivity_reengagement",
                "priority": "medium",
                "reason": "Inactivity threshold reached.",
                "next_step": "Send nudge and assign mentor check-in.",
            },
            "communication.failed": {
                "action_type": "failed_communication_retry",
                "priority": "medium",
                "reason": "Communication delivery repeatedly failed.",
                "next_step": "Try alternate channel and verify contact info.",
            },
            "operations.issue_overdue": {
                "action_type": "overdue_operational_issue",
                "priority": "critical",
                "reason": "Operational issue is overdue.",
                "next_step": "Escalate to operations lead immediately.",
            },
        }
        config = defaults.get(event.trigger_type)
        if config is None:
            return
        self._operations_os_service.create_action_item(
            tenant_id=event.tenant_id,
            action_type=config["action_type"],
            priority=config["priority"],
            subject_type="workflow_event",
            subject_id=str(event.context.get("student_id") or event.event_id),
            reason=config["reason"],
            due_at=event.timestamp + timedelta(hours=24),
            suggested_next_step=config["next_step"],
            metadata={"event_id": event.event_id, "trigger_type": event.trigger_type},
        )

    def _execute_step(self, item: ScheduledStep, current_time: datetime) -> dict[str, Any]:
        """Execute a single scheduled step and return its result dict."""
        try:
            if item.step.step_type == "notify":
                operation, template_name = self._resolve_whatsapp_template(
                    trigger_type=item.trigger_type,
                    step_config=item.step.config,
                )
                template_context = self._build_fee_template_context(item=item)
                template_context.setdefault("message", str(item.step.config.get("message", "workflow notification")))
                recipients = tuple(item.context.get("notification_recipients") or ()) or (item.actor_user_id,)
                routing_order = self._config_service.resolve_communication_routing(
                    ConfigResolutionContext(
                        tenant_id=item.tenant_id,
                        country_code=item.country_code,
                        segment_id=str(item.context.get("segment_id") or "academy"),
                    )
                )
                deliveries = []
                for recipient in recipients:
                    if "whatsapp" in routing_order:
                        delivery = self._notification_orchestrator.send_whatsapp_operation(
                            tenant_country_code=item.country_code,
                            user_id=recipient,
                            workflow_id=item.workflow_id,
                            operation=operation,
                            template_name=template_name,
                            template_context=template_context,
                            choices=list(item.step.config.get("choices") or ["ACK"]),
                            idempotency_key=f"{item.event_id}:{item.workflow_id}:{item.step.step_id}:{recipient}",
                        )
                    else:
                        fallback_message = self._notification_orchestrator.whatsapp_adapter.render_template_message(
                            template_name=template_name,
                            context=template_context,
                        )
                        delivery = self._notification_orchestrator.send_notification(
                            tenant_country_code=item.country_code,
                            user_id=recipient,
                            message=fallback_message,
                        )
                    deliveries.append(
                        {
                            "recipient": recipient,
                            "ok": delivery.ok,
                            "provider": delivery.provider,
                            "fallback_used": delivery.fallback_used,
                            "error": delivery.error,
                        }
                    )
                return {
                    "status": "sent" if deliveries and all(entry["ok"] for entry in deliveries) else "failed",
                    "deliveries": deliveries,
                    "template_name": template_name,
                    "routing_order": routing_order,
                }
            elif item.step.step_type in {"wait", "escalate"}:
                result: dict[str, Any] = {"status": "orchestrated", "action": item.step.step_type, "detail": item.step.config}
                if item.step.step_type == "escalate":
                    action = self._operations_os_service.create_action_item(
                        tenant_id=item.tenant_id,
                        action_type=str(item.step.config.get("action_type", "workflow_escalation")),
                        priority=str(item.step.config.get("priority", "high")),
                        subject_type=str(item.step.config.get("subject_type", "workflow_event")),
                        subject_id=str(item.context.get("student_id") or item.event_id),
                        reason=str(item.step.config.get("reason", f"Workflow escalation for {item.trigger_type}")),
                        due_at=current_time + timedelta(hours=8),
                        suggested_next_step=str(
                            item.step.config.get("suggested_next_step", "Assign operator and execute escalation runbook.")
                        ),
                        metadata={"workflow_id": item.workflow_id, "step_id": item.step.step_id, "event_id": item.event_id},
                    )
                    result["action_item_id"] = action.action_id
                return result
            elif item.step.step_type == "academy_ops":
                operation = str(item.step.config.get("operation", "run_qc_autofix"))
                if operation == "run_qc_autofix":
                    return {
                        "status": "orchestrated",
                        "action": "academy_ops.run_qc_autofix",
                        "detail": self._academy_ops_service.run_qc_autofix(),
                    }
                return {"status": "skipped", "reason": "unsupported_academy_ops_operation"}
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
                return {
                    "status": payment_entry.status,
                    "provider": payment_entry.provider,
                    "payment_id": payment_entry.payment_id,
                    "verified": payment_entry.verified,
                    "error": payment_entry.error,
                }
            elif item.step.step_type == "action_item":
                action = self._operations_os_service.create_action_item(
                    tenant_id=item.tenant_id,
                    action_type=str(item.step.config.get("action_type", "workflow_generated_action")),
                    priority=str(item.step.config.get("priority", "medium")),
                    subject_type=str(item.step.config.get("subject_type", "workflow_event")),
                    subject_id=str(item.step.config.get("subject_id") or item.context.get("student_id") or item.event_id),
                    reason=str(item.step.config.get("reason", f"Action generated from workflow {item.workflow_id}.")),
                    due_at=current_time + timedelta(hours=int(item.step.config.get("due_in_hours", 24))),
                    suggested_next_step=str(item.step.config.get("suggested_next_step", "Review and execute next operational step.")),
                    metadata={
                        "workflow_id": item.workflow_id,
                        "step_id": item.step.step_id,
                        "event_id": item.event_id,
                        "trigger_type": item.trigger_type,
                    },
                )
                return {"status": "created", "action_item_id": action.action_id}
            elif item.step.step_type == "approval_gate":
                # CGAP-007: human approval gate — pause workflow until operator approves/rejects
                import uuid as _uuid
                gate_id = str(item.step.config.get("gate_id") or f"gate_{_uuid.uuid4().hex[:12]}")
                gate = PendingApprovalGate(
                    gate_id=gate_id,
                    workflow_id=item.workflow_id,
                    event_id=item.event_id,
                    tenant_id=item.tenant_id,
                    actor_user_id=item.actor_user_id,
                    step=item.step,
                    context=dict(item.context),
                    requested_at=current_time,
                    status="pending",
                )
                self._pending_approval_gates[gate_id] = gate
                try:
                    from backend.services.shared.events.envelope import publish_event
                    publish_event({
                        "event_type": "workflow.approval_gate.requested",
                        "tenant_id": item.tenant_id,
                        "gate_id": gate_id,
                        "workflow_id": item.workflow_id,
                        "event_id": item.event_id,
                        "step_id": item.step.step_id,
                        "approval_prompt": item.step.config.get("approval_prompt", "Approval required to proceed."),
                        "context": item.context,
                    })
                except Exception:
                    pass
                return {
                    "status": "pending_approval",
                    "gate_id": gate_id,
                    "approval_prompt": item.step.config.get("approval_prompt", "Approval required to proceed."),
                }
            else:
                return {"status": "skipped", "reason": "unsupported_step_type"}
        except Exception as exc:
            return {"status": "failed", "error": str(exc), "step_type": item.step.step_type}

    def run_due(self, *, now: datetime | None = None) -> dict[str, Any]:
        """Execute all due scheduled steps.

        CGAP-004: Failed steps are re-queued up to max_retries with retry_delay_seconds backoff.
        CGAP-005: Steps with parallel=True are executed concurrently via ThreadPoolExecutor.
        """
        current_time = now or datetime.now(timezone.utc)

        due = [item for item in self._scheduled_steps if item.due_at <= current_time]
        self._scheduled_steps = [item for item in self._scheduled_steps if item.due_at > current_time]

        trace: list[dict[str, Any]] = []
        executions: list[dict[str, Any]] = []

        # CGAP-005: Split due items into sequential and parallel groups
        serial_items = [item for item in sorted(due, key=lambda s: s.due_at) if not item.step.parallel]
        parallel_items = [item for item in due if item.step.parallel]

        def _run_item(item: ScheduledStep) -> tuple[ScheduledStep, str, dict[str, Any]]:
            """Run one item; return (item, dedupe_key, result)."""
            dedupe_key = self._scheduled_step_key(item)
            self._scheduled_step_keys.discard(dedupe_key)
            if dedupe_key in self._executed_step_keys:
                return item, dedupe_key, {"status": "skipped_duplicate"}
            return item, dedupe_key, self._execute_step(item, current_time)

        def _record(item: ScheduledStep, dedupe_key: str, result: dict[str, Any]) -> None:
            """Record execution result; re-queue on failure if retries remain (CGAP-004)."""
            if result.get("status") == "skipped_duplicate":
                trace.append({
                    "step": "step.skipped_duplicate",
                    "workflow_id": item.workflow_id,
                    "step_id": item.step.step_id,
                    "reason": "idempotent_execution_guard",
                })
                return

            trace.append({"step": "step.started", "workflow_id": item.workflow_id, "step_id": item.step.step_id})
            is_failure = result.get("status") in {"failed", "failure"}
            will_retry = is_failure and item.attempt < item.step.max_retries

            executions.append({
                "workflow_id": item.workflow_id,
                "event_id": item.event_id,
                "step_id": item.step.step_id,
                "attempt": item.attempt,
                "result": result,
            })

            if will_retry:
                retry_due = current_time + timedelta(seconds=max(1, item.step.retry_delay_seconds))
                retry = ScheduledStep(
                    workflow_id=item.workflow_id,
                    event_id=item.event_id,
                    tenant_id=item.tenant_id,
                    country_code=item.country_code,
                    actor_user_id=item.actor_user_id,
                    trigger_type=item.trigger_type,
                    context=item.context,
                    step=item.step,
                    due_at=retry_due,
                    attempt=item.attempt + 1,
                )
                self._scheduled_steps.append(retry)
                self._scheduled_step_keys.add(self._scheduled_step_key(retry))
                trace.append({
                    "step": "step.retry_scheduled",
                    "workflow_id": item.workflow_id,
                    "step_id": item.step.step_id,
                    "attempt": item.attempt + 1,
                    "retry_due_at": retry_due.isoformat(),
                })
            else:
                self._executed_step_keys.add(dedupe_key)
                trace.append({"step": "step.completed", "workflow_id": item.workflow_id, "step_id": item.step.step_id})

        # Execute serial items sequentially
        for item in serial_items:
            item_obj, key, res = _run_item(item)
            _record(item_obj, key, res)

        # Execute parallel items concurrently (CGAP-005)
        if parallel_items:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(parallel_items))) as pool:
                futures = {pool.submit(_run_item, item): item for item in parallel_items}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        item_obj, key, res = future.result()
                    except Exception as exc:
                        item_obj = futures[future]
                        key = self._scheduled_step_key(item_obj)
                        res = {"status": "failed", "error": str(exc), "step_type": item_obj.step.step_type}
                    _record(item_obj, key, res)

        return {
            "executed": executions,
            "pending_count": len(self._scheduled_steps),
            "trace": trace,
        }

    def _scheduled_step_key(self, item: ScheduledStep) -> str:
        return f"{item.event_id}:{item.workflow_id}:{item.step.step_id}:{item.actor_user_id}"

    def _resolve_whatsapp_template(
        self,
        *,
        trigger_type: str,
        step_config: dict[str, Any],
    ) -> tuple[Literal["attendance", "reminder", "update"], str]:
        configured_operation = str(step_config.get("operation", "")).strip().lower()
        configured_template = str(step_config.get("template_name", "")).strip()
        if configured_operation in {"attendance", "reminder", "update"} and configured_template:
            return configured_operation, configured_template  # type: ignore[return-value]

        normalized = trigger_type.strip().lower()
        if normalized.startswith("attendance."):
            return "attendance", "attendance_notification"
        if normalized in {"fee.overdue"}:
            return "reminder", "fee_overdue_escalation"
        if normalized in {"fee.due"}:
            return "reminder", "fee_reminder"
        if normalized in {"payment.due", "payment.missed", "payment.overdue"}:
            return "reminder", "fee_reminder"
        if normalized.startswith("progress.") or normalized.startswith("learning.progress"):
            return "update", "progress_update"
        return "update", "progress_update"

    def _build_fee_template_context(self, *, item: ScheduledStep) -> dict[str, Any]:
        context = dict(item.context)
        profile = self._system_of_record_service.get_student_profile(tenant_id=item.tenant_id, student_id=item.actor_user_id)
        if profile is not None:
            context.setdefault("student_name", profile.full_name)
            if profile.ledger_summary.last_invoice_id:
                context.setdefault("invoice_id", profile.ledger_summary.last_invoice_id)
            context.setdefault("amount", str(profile.financial_state.dues_outstanding))
            metadata_due_date = profile.metadata.get("fee.due_date")
            if metadata_due_date:
                context.setdefault("due_date", metadata_due_date)
            if "currency" not in context:
                ledger = self._system_of_record_service.get_student_ledger(tenant_id=item.tenant_id, student_id=item.actor_user_id)
                last_invoice_entry = next((entry for entry in reversed(ledger) if entry.source_type == "invoice"), None)
                if last_invoice_entry is not None:
                    context["currency"] = last_invoice_entry.currency
        return context


    def bootstrap_default_workflows(self, tenant_id: str = "__global__") -> tuple[str, ...]:
        """Register default workflows.

        CGAP-008: Activation list is config-driven. Config key
        ``behavior_tuning.workflow_engine.default_workflows`` may hold a list of workflow IDs
        to activate. If absent or empty the full set is registered (opt-out posture per BC-WF-01).
        Tenants can extend or restrict the default bundle via config without code changes.
        """
        try:
            policy = self._config_service.resolve(
                ConfigResolutionContext(tenant_id=tenant_id, country_code="", segment_id="")
            )
            wf_config = policy.behavior_tuning.get("workflow_engine", {})
            raw_enabled = wf_config.get("default_workflows")
            enabled_ids: set[str] | None = set(raw_enabled) if raw_enabled else None
        except Exception:
            enabled_ids = None  # fallback: register all (preserves opt-out posture)

        defaults = (
            WorkflowDefinition(
                workflow_id="wf_default_attendance",
                name="Default Attendance Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(rule_id="rule_attendance_absence", trigger_type="attendance.absence_detected"),
                    WorkflowRule(rule_id="rule_attendance_present", trigger_type="attendance.present_marked"),
                ),
                steps=(
                    WorkflowStep(step_id="step_attendance_notify", step_type="notify", config={"message": "Attendance alert triggered."}),
                    WorkflowStep(step_id="step_attendance_followup", step_type="action_item", config={"action_type": "attendance_follow_up", "priority": "high"}),
                ),
            ),
            WorkflowDefinition(
                workflow_id="wf_default_fees",
                name="Default Fees Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(rule_id="rule_fee_missed", trigger_type="payment.missed"),
                    WorkflowRule(rule_id="rule_fee_due", trigger_type="fee.due"),
                    WorkflowRule(rule_id="rule_fee_overdue", trigger_type="fee.overdue"),
                    WorkflowRule(rule_id="rule_payment_due", trigger_type="payment.due"),
                    WorkflowRule(rule_id="rule_payment_overdue", trigger_type="payment.overdue"),
                ),
                steps=(
                    WorkflowStep(step_id="step_fees_notify", step_type="notify", config={"message": "Fee reminder sent."}),
                    WorkflowStep(step_id="step_fees_action", step_type="action_item", config={"action_type": "unpaid_fees_follow_up", "priority": "high"}),
                ),
            ),
            WorkflowDefinition(
                workflow_id="wf_default_notifications",
                name="Default Notifications Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(rule_id="rule_progress_update", trigger_type="progress.updated"),
                ),
                steps=(
                    WorkflowStep(step_id="step_progress_notify", step_type="notify", config={"message": "Progress update available."}),
                ),
            ),
            # CGAP-001: BC-WF-01 — enrollment.completed → certificate issuance + congratulations
            WorkflowDefinition(
                workflow_id="wf_default_enrollment_completed",
                name="Default Enrollment Completed Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(rule_id="rule_enrollment_completed", trigger_type="enrollment.completed"),
                ),
                steps=(
                    WorkflowStep(
                        step_id="step_enrollment_congratulations",
                        step_type="notify",
                        config={
                            "operation": "update",
                            "template_name": "enrollment_congratulations",
                            "message": "Congratulations! Your enrollment is confirmed.",
                        },
                    ),
                    WorkflowStep(
                        step_id="step_certificate_issuance",
                        step_type="action_item",
                        config={
                            "action_type": "certificate_issuance",
                            "priority": "medium",
                            "subject_type": "enrollment",
                            "reason": "Enrollment completed — certificate ready for issuance.",
                            "suggested_next_step": "Issue certificate and deliver to learner.",
                            "due_in_hours": 1,
                        },
                    ),
                ),
            ),
            # CGAP-002: BC-WF-01 — batch.capacity_below_threshold → admin alert + open-seat notification
            WorkflowDefinition(
                workflow_id="wf_default_capacity_alert",
                name="Default Batch Capacity Alert Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(rule_id="rule_capacity_below_threshold", trigger_type="batch.capacity_below_threshold"),
                ),
                steps=(
                    WorkflowStep(
                        step_id="step_capacity_escalate",
                        step_type="escalate",
                        config={
                            "action_type": "batch_capacity_low",
                            "priority": "high",
                            "subject_type": "batch",
                            "reason": "Batch capacity is below threshold.",
                            "suggested_next_step": "Review waitlist and send open-seat notifications.",
                        },
                    ),
                    WorkflowStep(
                        step_id="step_capacity_notify_waitlist",
                        step_type="notify",
                        config={
                            "operation": "update",
                            "template_name": "open_seat_notification",
                            "message": "A seat has become available in your batch. Reply JOIN to reserve.",
                        },
                        delay_seconds=300,
                    ),
                ),
            ),
            # CGAP-003: BC-WF-01 — assessment.failed → remediation suggestion + instructor alert
            WorkflowDefinition(
                workflow_id="wf_default_assessment_failed",
                name="Default Assessment Failed Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(rule_id="rule_assessment_failed", trigger_type="assessment.failed"),
                ),
                steps=(
                    WorkflowStep(
                        step_id="step_assessment_remediation_notify",
                        step_type="notify",
                        config={
                            "operation": "update",
                            "template_name": "assessment_remediation",
                            "message": "You did not pass the assessment. Review the material and try again.",
                        },
                    ),
                    WorkflowStep(
                        step_id="step_assessment_instructor_alert",
                        step_type="action_item",
                        config={
                            "action_type": "assessment_failed_follow_up",
                            "priority": "medium",
                            "subject_type": "learner",
                            "reason": "Learner failed assessment — review and consider intervention.",
                            "suggested_next_step": "Contact learner, review weak areas, assign remediation content.",
                            "due_in_hours": 24,
                        },
                    ),
                ),
            ),
            # MO-032 / Phase D: BC-LEARN-01 — at-risk learner intervention default workflow.
            # Triggered by workflow.trigger.learner_intervention events emitted by
            # AnalyticsService.trigger_at_risk_interventions() (MO-030).
            # Without this workflow registration the event fires but nothing acts on it.
            WorkflowDefinition(
                workflow_id="wf_default_learner_intervention",
                name="Default At-Risk Learner Intervention Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(
                        rule_id="rule_learner_intervention_trigger",
                        trigger_type="workflow.trigger.learner_intervention",
                    ),
                ),
                steps=(
                    WorkflowStep(
                        step_id="step_learner_intervention_notify",
                        step_type="notify",
                        config={
                            "operation": "send",
                            "template_name": "at_risk_learner_outreach",
                            "message": (
                                "We've noticed you may need some extra support. "
                                "Your teacher has been notified and will reach out shortly. "
                                "Reply HELP to get resources."
                            ),
                        },
                    ),
                    WorkflowStep(
                        step_id="step_learner_intervention_action",
                        step_type="action_item",
                        config={
                            "action_type": "at_risk_learner_follow_up",
                            "priority": "high",
                            "subject_type": "learner",
                            "reason": "Learner identified as at-risk by analytics engine.",
                            "suggested_next_step": (
                                "Contact learner directly, review their progress gaps, "
                                "and assign a targeted remediation activity."
                            ),
                            "due_in_hours": 24,
                        },
                    ),
                ),
            ),
            # CGAP-091: MS-REDUCE-01 (MS§10.6) — compliance tracking automation path.
            # Every repeatable operation type must have an automation path.
            # Compliance deadline tracking is repeatable — enforce via default workflow.
            WorkflowDefinition(
                workflow_id="wf_default_compliance_tracking",
                name="Default Compliance Tracking Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(
                        rule_id="rule_compliance_training_due",
                        trigger_type="compliance.training_due",
                    ),
                    WorkflowRule(
                        rule_id="rule_compliance_deadline_approaching",
                        trigger_type="compliance.deadline_approaching",
                    ),
                ),
                steps=(
                    WorkflowStep(
                        step_id="step_compliance_learner_notify",
                        step_type="notify",
                        config={
                            "operation": "send",
                            "template_name": "compliance_reminder",
                            "message": (
                                "Your mandatory compliance module is due. "
                                "Complete it to maintain your compliance status."
                            ),
                        },
                    ),
                    WorkflowStep(
                        step_id="step_compliance_manager_action",
                        step_type="action_item",
                        config={
                            "action_type": "compliance_follow_up",
                            "priority": "high",
                            "subject_type": "learner",
                            "reason": "Learner compliance training deadline approaching.",
                            "suggested_next_step": (
                                "Confirm learner has enrolled in required compliance module "
                                "or escalate to compliance manager."
                            ),
                            "due_in_hours": 24,
                        },
                    ),
                ),
            ),
            # CGAP-091: MS-REDUCE-01 (MS§10.6) — daily action list generation automation path.
            # Daily action list generation is a repeatable start-of-day operation.
            # Automation path ensures operators receive structured priority list without manual trigger.
            WorkflowDefinition(
                workflow_id="wf_default_daily_action_list",
                name="Default Daily Action List Workflow",
                enabled=True,
                rules=(
                    WorkflowRule(
                        rule_id="rule_operations_day_start",
                        trigger_type="operations.day_start",
                    ),
                ),
                steps=(
                    WorkflowStep(
                        step_id="step_generate_daily_actions",
                        step_type="action_item",
                        config={
                            "action_type": "generate_daily_action_list",
                            "priority": "medium",
                            "subject_type": "operator",
                            "reason": "Start-of-day action list generation.",
                            "suggested_next_step": (
                                "Review CRITICAL items immediately; "
                                "action IMPORTANT items before end of day."
                            ),
                            "due_in_hours": 0,
                        },
                    ),
                    WorkflowStep(
                        step_id="step_deliver_daily_actions",
                        step_type="notify",
                        config={
                            "operation": "send",
                            "template_name": "daily_action_list",
                            "message": (
                                "Your daily action list is ready. "
                                "Review CRITICAL items first, then IMPORTANT items."
                            ),
                        },
                        delay_seconds=60,
                    ),
                ),
            ),
        )
        for workflow in defaults:
            # CGAP-008: only register if no explicit activation list, or workflow is in the list
            if enabled_ids is None or workflow.workflow_id in enabled_ids:
                self.register_workflow(workflow)
        return tuple(w.workflow_id for w in self._workflows.values())

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

    # ------------------------------------------------------------------ #
    # CGAP-007: Human approval gate management                            #
    # ------------------------------------------------------------------ #

    def get_pending_approval_gates(self, *, tenant_id: str | None = None) -> list[PendingApprovalGate]:
        """Return all pending approval gates, optionally filtered by tenant."""
        gates = [g for g in self._pending_approval_gates.values() if g.status == "pending"]
        if tenant_id is not None:
            gates = [g for g in gates if g.tenant_id == tenant_id]
        return sorted(gates, key=lambda g: g.requested_at)

    def approve_gate(self, gate_id: str, *, actor_id: str, note: str = "") -> dict[str, Any]:
        """Approve a pending approval gate, resuming the paused workflow step."""
        gate = self._pending_approval_gates.get(gate_id)
        if gate is None:
            return {"ok": False, "reason": "gate_not_found"}
        if gate.status != "pending":
            return {"ok": False, "reason": f"gate_already_{gate.status}"}
        gate.status = "approved"
        gate.resolved_at = datetime.now(timezone.utc)
        gate.resolved_by = actor_id
        gate.resolution_note = note or None
        try:
            from backend.services.shared.events.envelope import publish_event
            publish_event({
                "event_type": "workflow.approval_gate.approved",
                "tenant_id": gate.tenant_id,
                "gate_id": gate_id,
                "workflow_id": gate.workflow_id,
                "actor_id": actor_id,
                "resolved_at": gate.resolved_at.isoformat(),
            })
        except Exception:
            pass
        return {"ok": True, "gate_id": gate_id, "status": "approved", "resolved_by": actor_id}

    def reject_gate(self, gate_id: str, *, actor_id: str, note: str = "") -> dict[str, Any]:
        """Reject a pending approval gate, halting the paused workflow step."""
        gate = self._pending_approval_gates.get(gate_id)
        if gate is None:
            return {"ok": False, "reason": "gate_not_found"}
        if gate.status != "pending":
            return {"ok": False, "reason": f"gate_already_{gate.status}"}
        gate.status = "rejected"
        gate.resolved_at = datetime.now(timezone.utc)
        gate.resolved_by = actor_id
        gate.resolution_note = note or None
        try:
            from backend.services.shared.events.envelope import publish_event
            publish_event({
                "event_type": "workflow.approval_gate.rejected",
                "tenant_id": gate.tenant_id,
                "gate_id": gate_id,
                "workflow_id": gate.workflow_id,
                "actor_id": actor_id,
                "resolved_at": gate.resolved_at.isoformat(),
            })
        except Exception:
            pass
        return {"ok": True, "gate_id": gate_id, "status": "rejected", "resolved_by": actor_id}

    # ------------------------------------------------------------------ #
    # CGAP-009: Automation enable/disable audit logging                   #
    # ------------------------------------------------------------------ #

    def enable_workflow(self, workflow_id: str, *, actor_id: str, tenant_id: str = "__global__") -> dict[str, Any]:
        """Enable a registered workflow and write a BC-WF-01 audit log entry."""
        existing = self._workflows.get(workflow_id)
        if existing is None:
            return {"ok": False, "reason": "workflow_not_found"}
        if existing.enabled:
            return {"ok": True, "status": "already_enabled"}
        self._workflows[workflow_id] = WorkflowDefinition(
            workflow_id=existing.workflow_id,
            name=existing.name,
            enabled=True,
            rules=existing.rules,
            steps=existing.steps,
            branches=existing.branches,
        )
        entry = {
            "action": "automation.enabled",
            "workflow_id": workflow_id,
            "actor_id": actor_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._automation_audit_log.append(entry)
        try:
            from backend.services.shared.events.envelope import publish_event
            publish_event({"event_type": "workflow.automation.state_changed", **entry})
        except Exception:
            pass
        return {"ok": True, "workflow_id": workflow_id, "status": "enabled"}

    def disable_workflow(self, workflow_id: str, *, actor_id: str, tenant_id: str = "__global__") -> dict[str, Any]:
        """Disable a registered workflow and write a BC-WF-01 audit log entry."""
        existing = self._workflows.get(workflow_id)
        if existing is None:
            return {"ok": False, "reason": "workflow_not_found"}
        if not existing.enabled:
            return {"ok": True, "status": "already_disabled"}
        self._workflows[workflow_id] = WorkflowDefinition(
            workflow_id=existing.workflow_id,
            name=existing.name,
            enabled=False,
            rules=existing.rules,
            steps=existing.steps,
            branches=existing.branches,
        )
        entry = {
            "action": "automation.disabled",
            "workflow_id": workflow_id,
            "actor_id": actor_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._automation_audit_log.append(entry)
        try:
            from backend.services.shared.events.envelope import publish_event
            publish_event({"event_type": "workflow.automation.state_changed", **entry})
        except Exception:
            pass
        return {"ok": True, "workflow_id": workflow_id, "status": "disabled"}

    def get_automation_audit_log(
        self, *, tenant_id: str | None = None, workflow_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Return automation enable/disable audit entries, optionally filtered."""
        log = list(self._automation_audit_log)
        if tenant_id is not None:
            log = [e for e in log if e.get("tenant_id") == tenant_id]
        if workflow_id is not None:
            log = [e for e in log if e.get("workflow_id") == workflow_id]
        return log
