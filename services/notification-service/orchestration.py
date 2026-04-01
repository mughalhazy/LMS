from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

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
from shared.models.workflow import WorkflowAction, WorkflowDefinition

from action_routing import WhatsAppActionRouter


@dataclass(frozen=True)
class NotificationOrchestrationConfig:
    """Configuration for channel adapter ordering and adapter-level controls."""

    fallback_order: Sequence[str] = ("whatsapp", "sms")
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

        self._router = CommunicationRouter(adapters=adapters, fallback_order=cfg.fallback_order)
        self.interactive_reply_log: list[dict[str, Any]] = []
        self._phone_user_map: dict[str, str] = {}
        self._action_router = WhatsAppActionRouter()

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        digits = "".join(ch for ch in phone if ch.isdigit())
        return f"+{digits}" if digits else ""

    def register_user_phone(self, *, phone: str, user_id: str) -> None:
        normalized_phone = self._normalize_phone(phone)
        if normalized_phone and user_id.strip():
            self._phone_user_map[normalized_phone] = user_id.strip()

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
        message: str,
        choices: list[str] | None = None,
    ) -> DeliveryAttempt:
        interactive_message = self.whatsapp_adapter.build_workflow_message(
            operation=operation,
            workflow_id=workflow_id,
            message=message,
            choices=choices,
        )
        return self.send_notification(
            tenant_country_code=tenant_country_code,
            user_id=user_id,
            message=interactive_message,
        )

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
