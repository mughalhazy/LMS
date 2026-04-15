from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from uuid import uuid4

from integrations.communication import (
    CommunicationRouter,
    CommunicationUser,
    DeliveryAttempt,
    EmailAdapter,
    SMSAdapter,
    Tenant,
    WhatsAppAdapter,
    WhatsAppOperationType,
)
from shared.models.template import Template
from shared.models.workflow import WorkflowAction, WorkflowDefinition

from action_routing import ChannelActionRouter, WhatsAppActionRouter


@dataclass(frozen=True)
class NotificationOrchestrationConfig:
    """Configuration for channel adapter ordering and adapter-level controls."""

    default_fallback_order: Sequence[str] = ("whatsapp", "sms", "email")
    capability_enabled: Mapping[str, bool] | None = None
    behavior_tuning: Mapping[str, Any] | None = None
    whatsapp_disabled_recipients: set[str] | None = None
    sms_disabled_recipients: set[str] | None = None
    email_disabled_recipients: set[str] | None = None


class NotificationOrchestrator:
    """Workflow-driven WhatsApp operations engine (attendance/reminders/updates)."""

    # BC-INT-02: persona → available command shortcuts
    _PERSONA_COMMANDS: dict[str, list[str]] = {
        "operator": ["status", "today", "pending", "approve [id]", "remind [batch]"],
        "manager":  ["status", "today", "pending", "approve [id]"],
        "instructor": ["status", "today", "remind [batch]"],
        "learner":  ["status", "today", "help"],
    }

    # BC-INT-02: persona → status response template
    _PERSONA_STATUS_MESSAGES: dict[str, str] = {
        "operator":   "Operator view: reply TODAY for today's action list, PENDING for open items, APPROVE [id] to approve.",
        "manager":    "Manager view: reply TODAY for team status, PENDING for open approvals.",
        "instructor": "Instructor view: reply TODAY for today's session roster, REMIND [batch] to send a reminder.",
        "learner":    "Learner view: reply TODAY for your schedule, STATUS for your progress.",
    }

    def __init__(self, config: NotificationOrchestrationConfig | None = None) -> None:
        cfg = config or NotificationOrchestrationConfig()

        self.whatsapp_adapter = WhatsAppAdapter(disabled_recipients=cfg.whatsapp_disabled_recipients)
        self.sms_adapter = SMSAdapter(disabled_recipients=cfg.sms_disabled_recipients)

        adapters = {
            "whatsapp": self.whatsapp_adapter,
            "sms": self.sms_adapter,
            "email": EmailAdapter(disabled_recipients=cfg.email_disabled_recipients),
        }

        fallback_order = self._resolve_fallback_order(config=cfg)
        self._router = CommunicationRouter(adapters=adapters, fallback_order=fallback_order)
        self._action_router = WhatsAppActionRouter()
        self._channel_action_router = ChannelActionRouter()
        self._phone_user_map: dict[str, str] = {}
        self._templates: dict[str, Template] = {}
        self.interactive_reply_log: list[dict[str, Any]] = []
        self._idempotent_send_log: set[str] = set()
        # BC-INT-02: user_id → persona type ("operator" | "manager" | "instructor" | "learner")
        self._persona_map: dict[str, str] = {}
        # CGAP-022: workflow engine back-reference for action execution.
        # Set by WorkflowEngine.__init__() via bind_workflow_engine().
        self._workflow_engine: Any | None = None

    def _resolve_fallback_order(self, *, config: NotificationOrchestrationConfig) -> tuple[str, ...]:
        behavior_tuning = dict(config.behavior_tuning or {})
        communication = behavior_tuning.get("communication", {})
        configured_priority = communication.get("routing_priority", config.default_fallback_order)

        if isinstance(configured_priority, str):
            candidate_order = [configured_priority]
        else:
            candidate_order = [str(item).strip().lower() for item in configured_priority if str(item).strip()]

        capability_enabled = dict(config.capability_enabled or {})
        if capability_enabled.get("whatsapp_primary_interface", False):
            candidate_order.insert(0, "whatsapp")

        # Router supports only these channels.
        supported_channels = {"whatsapp", "sms", "email"}
        deduped: list[str] = []
        for channel in candidate_order:
            if channel not in supported_channels or channel in deduped:
                continue
            deduped.append(channel)

        if not deduped:
            return ("sms",)
        return tuple(deduped)

    def send_notification(self, *, tenant_country_code: str, user_id: str, message: str) -> DeliveryAttempt:
        tenant = Tenant(country_code=tenant_country_code)
        user = CommunicationUser(user_id=user_id)
        return self._router.send_message(tenant=tenant, user=user, message=message)

    def send_whatsapp_operation(
        self,
        *,
        tenant_country_code: str,
        user_id: str,
        workflow_id: str,
        operation: WhatsAppOperationType,
        message: str | None = None,
        template_name: str | None = None,
        template_context: dict[str, Any] | None = None,
        choices: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> DeliveryAttempt:
        dedupe_key = idempotency_key or f"{tenant_country_code}:{workflow_id}:{user_id}:{operation}:{message or template_name or ''}"
        if dedupe_key in self._idempotent_send_log:
            return DeliveryAttempt(
                ok=True,
                provider="whatsapp",
                fallback_used=False,
                error=None,
            )

        resolved_message = message
        if template_name:
            resolved_message = self.whatsapp_adapter.render_template_message(
                template_name=template_name,
                context=template_context or {},
            )

        interactive_message = self.whatsapp_adapter.build_workflow_message(
            operation=operation,
            workflow_id=workflow_id,
            message=resolved_message or "Workflow notification",
            choices=choices,
        )
        attempt = self.send_notification(
            tenant_country_code=tenant_country_code,
            user_id=user_id,
            message=interactive_message,
        )
        if attempt.ok:
            self._idempotent_send_log.add(dedupe_key)
        return attempt

    def execute_workflow(
        self,
        *,
        workflow: WorkflowDefinition,
        tenant_country_code: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Run notification actions from a workflow, including WhatsApp operations."""

        results: list[dict[str, Any]] = []
        for action in workflow.actions:
            if action.action_type != "send_notification":
                continue
            results.append(
                self._execute_notification_action(
                    action=action,
                    workflow_id=workflow.workflow_id,
                    tenant_country_code=tenant_country_code,
                    context=context,
                )
            )

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "executed_actions": len(results),
            "results": results,
        }

    def register_user_persona(self, *, user_id: str, persona: str) -> None:
        """BC-INT-02: register a user's persona for persona-aware command routing."""
        self._persona_map[user_id.strip()] = persona.strip().lower()

    def _resolve_persona(self, user_id: str) -> str:
        return self._persona_map.get(user_id.strip(), "learner")

    def handle_command(self, *, user_id: str, command_text: str) -> dict[str, Any] | None:
        """BC-INT-02: handle persona-aware command shortcuts.

        Returns a dict response if the text matches a known shortcut, None otherwise
        (allowing the caller to fall through to WhatsApp reply parsing).
        """
        persona = self._resolve_persona(user_id)
        text = command_text.strip().lower()
        parts = text.split(None, 1)
        verb = parts[0] if parts else ""
        arg = parts[1].strip() if len(parts) > 1 else ""

        if verb == "status":
            msg = self._PERSONA_STATUS_MESSAGES.get(persona, self._PERSONA_STATUS_MESSAGES["learner"])
            return {"status": "handled", "command": "status", "persona": persona, "message": msg}

        if verb == "today":
            return {
                "status": "handled",
                "command": "today",
                "persona": persona,
                "message": f"Fetching today's {persona} agenda. Reply PENDING for open items.",
                "action_hint": "query_today",
            }

        if verb == "pending":
            return {
                "status": "handled",
                "command": "pending",
                "persona": persona,
                "message": f"Fetching pending items for {persona}.",
                "action_hint": "query_pending",
            }

        if verb == "approve" and arg and persona in {"operator", "manager"}:
            # Route to approve_request action via workflow engine
            if self._workflow_engine is not None:
                try:
                    envelope = {
                        "event_id": str(uuid4()),
                        "event_type": "request.approved",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "tenant_id": "",
                        "correlation_id": arg,
                        "payload": {"user_id": user_id, "action_id": arg, "action_type": "approve_request"},
                        "metadata": {"actor": {"user_id": user_id, "role": persona}, "source": "command_shortcut"},
                    }
                    self._workflow_engine.handle_event_envelope(envelope)
                except Exception:
                    pass
            return {"status": "handled", "command": "approve", "persona": persona, "action_id": arg}

        if verb == "remind" and arg and persona in {"operator", "instructor"}:
            return {
                "status": "handled",
                "command": "remind",
                "persona": persona,
                "batch_ref": arg,
                "message": f"Reminder queued for batch {arg}.",
                "action_hint": "batch_reminder_requested",
            }

        if verb == "help":
            commands = self._PERSONA_COMMANDS.get(persona, self._PERSONA_COMMANDS["learner"])
            return {
                "status": "handled",
                "command": "help",
                "persona": persona,
                "available_commands": commands,
                "message": f"Available commands: {', '.join(commands)}",
            }

        return None

    def bind_workflow_engine(self, engine: Any) -> None:
        """Bind the workflow engine for action execution on inbound replies (CGAP-022)."""
        self._workflow_engine = engine

    def handle_interactive_reply(self, *, user_id: str, reply: str) -> dict[str, Any]:
        # BC-INT-02: check for persona-aware command shortcuts before WhatsApp reply parsing
        command_result = self.handle_command(user_id=user_id, command_text=reply)
        if command_result is not None:
            self.interactive_reply_log.append({**command_result, "user_id": user_id, "raw_reply": reply})
            return command_result

        parsed = self.whatsapp_adapter.parse_interactive_reply(user_id=user_id, reply=reply)
        if parsed is None:
            parsed = self.whatsapp_adapter.classify_free_text_reply(user_id=user_id, reply=reply)
        if parsed is None:
            return {"status": "ignored", "reason": "invalid_reply_format"}

        routed = self._action_router.route(parsed)
        item = asdict(parsed) | {"status": routed.status, "routed_action": routed.action_type, "detail": routed.detail}
        self.interactive_reply_log.append(item)

        # CGAP-022: BC-INT-01 — execute the routed action via the workflow engine.
        # Previously actions were logged but never executed. Now accepted actions
        # are dispatched as workflow trigger events so downstream services act on them.
        if routed.status == "accepted" and self._workflow_engine is not None:
            dispatch_result = self._dispatch_routed_action(routed=routed, user_id=user_id)
            item = {**item, "dispatch_result": dispatch_result}

        return item

    # Action type → workflow trigger event type mapping (BC-INT-01)
    _ACTION_TO_TRIGGER: dict[str, str] = {
        "confirm_attendance": "attendance.marked",
        "decline_attendance": "attendance.marked",
        "initiate_payment": "payment.confirmed",
        "waive_payment": "payment.waived",
        "confirm_enrollment": "enrollment.confirmed",
        "enrollment_info_request": "enrollment.info_requested",
        "contact_learner": "learner.contact_requested",
        "approve_request": "request.approved",
        "reject_request": "request.rejected",
        "reserve_seat": "batch.seat_reserved",
        "acknowledge_reminder": "reminder.acknowledged",
        "snooze_reminder": "reminder.snoozed",
        "acknowledge_update": "update.acknowledged",
    }

    def _dispatch_routed_action(self, *, routed: Any, user_id: str) -> dict[str, Any]:
        """Convert a RoutedAction into a workflow trigger envelope and dispatch it.

        CGAP-022 fix: routed actions now execute via the workflow engine instead of
        being only logged.
        """
        trigger_type = self._ACTION_TO_TRIGGER.get(routed.action_type)
        if trigger_type is None:
            return {"dispatched": False, "reason": "no_trigger_mapping"}

        attendance_status: str | None = None
        if routed.action_type == "confirm_attendance":
            attendance_status = "present"
        elif routed.action_type == "decline_attendance":
            attendance_status = "absent"

        payload: dict[str, Any] = {
            "user_id": user_id,
            "workflow_id": routed.detail.get("workflow_id", ""),
            "action_type": routed.action_type,
        }
        if attendance_status:
            payload["attendance_status"] = attendance_status
            payload["student_id"] = user_id
        payload.update({k: v for k, v in routed.detail.items() if k not in {"workflow_id", "user_id"}})

        envelope = {
            "event_id": str(uuid4()),
            "event_type": trigger_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": routed.detail.get("tenant_id", ""),
            "correlation_id": routed.detail.get("workflow_id", ""),
            "payload": payload,
            "metadata": {
                "actor": {"user_id": user_id, "role": "user"},
                "source": "whatsapp_reply",
            },
        }
        try:
            result = self._workflow_engine.handle_event_envelope(envelope)
            return {"dispatched": True, "trigger_type": trigger_type, "scheduled": len(result.get("scheduled", []))}
        except Exception as exc:
            # Dispatch failure must not break reply processing
            return {"dispatched": False, "reason": str(exc)}

    def handle_inbound_whatsapp(
        self,
        *,
        source_phone: str,
        reply: str,
        provider_verified: bool,
        claimed_user_id: str | None = None,
    ) -> dict[str, Any]:
        if not provider_verified:
            return {"status": "rejected", "reason": "unverified_provider_event"}

        normalized_phone = self._normalize_phone(source_phone)
        mapped_user_id = self._phone_user_map.get(normalized_phone)
        if mapped_user_id is None:
            return {"status": "rejected", "reason": "unknown_phone"}

        if claimed_user_id and claimed_user_id != mapped_user_id:
            return {"status": "rejected", "reason": "spoofing_detected"}

        return self.handle_interactive_reply(user_id=mapped_user_id, reply=reply)

    def register_phone_user(self, *, phone: str, user_id: str) -> None:
        self._phone_user_map[self._normalize_phone(phone)] = user_id

    def register_template(self, template: Template) -> None:
        self._templates[template.template_id] = template

    def render_template(self, *, template_id: str, payload: dict[str, Any], locale: str) -> tuple[Template, str]:
        template = self._templates[template_id]
        message = template.render(payload=payload, locale=locale)
        return template, message

    def _normalize_phone(self, phone: str) -> str:
        return "".join(char for char in phone if char.isdigit() or char == "+").strip()

    def _execute_notification_action(
        self,
        *,
        action: WorkflowAction,
        workflow_id: str,
        tenant_country_code: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        recipients = list(action.config.get("recipients") or context.get("recipients") or [])
        operation = str(action.config.get("operation", "update")).lower()
        channel = str(action.config.get("channel", "whatsapp")).lower()
        locale = str(context.get("locale", "default"))
        template_id = action.config.get("template_id")
        if isinstance(template_id, str) and template_id in self._templates:
            template, message = self.render_template(
                template_id=template_id,
                payload=context,
                locale=locale,
            )
            channel = template.channel.lower()
        else:
            message = str(action.config.get("message", "Workflow notification"))
        choices = list(action.config.get("choices") or ["ACK"])

        delivery_results: list[dict[str, Any]] = []
        for recipient in recipients:
            if channel == "whatsapp":
                attempt = self.send_whatsapp_operation(
                    tenant_country_code=tenant_country_code,
                    user_id=recipient,
                    workflow_id=workflow_id,
                    operation=operation if operation in {"attendance", "reminder", "update"} else "update",
                    message=message,
                    choices=choices,
                )
            else:
                attempt = self.send_notification(
                    tenant_country_code=tenant_country_code,
                    user_id=recipient,
                    message=message,
                )
            delivery_results.append(asdict(attempt))

        return {
            "action_type": action.action_type,
            "channel": channel,
            "operation": operation,
            "recipients": recipients,
            "deliveries": delivery_results,
        }
