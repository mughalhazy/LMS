from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

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

from action_routing import WhatsAppActionRouter


@dataclass(frozen=True)
class NotificationOrchestrationConfig:
    """Configuration for channel adapter ordering and adapter-level controls."""

    default_fallback_order: Sequence[str] = ("sms", "email")
    capability_enabled: Mapping[str, bool] | None = None
    behavior_tuning: Mapping[str, Any] | None = None
    whatsapp_disabled_recipients: set[str] | None = None
    sms_disabled_recipients: set[str] | None = None
    email_disabled_recipients: set[str] | None = None


class NotificationOrchestrator:
    """Workflow-driven WhatsApp operations engine (attendance/reminders/updates)."""

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
        self.interactive_reply_log: list[dict[str, Any]] = []
        self._idempotent_send_log: set[str] = set()

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

    def handle_interactive_reply(self, *, user_id: str, reply: str) -> dict[str, Any]:
        parsed = self.whatsapp_adapter.parse_interactive_reply(user_id=user_id, reply=reply)
        if parsed is None:
            parsed = self.whatsapp_adapter.classify_free_text_reply(user_id=user_id, reply=reply)
        if parsed is None:
            return {"status": "ignored", "reason": "invalid_reply_format"}

        routed = self._action_router.route(parsed)
        item = asdict(parsed) | {"status": routed.status, "routed_action": routed.action_type, "detail": routed.detail}
        self.interactive_reply_log.append(item)
        return item

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
