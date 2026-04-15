from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import hashlib
import hmac
from typing import Any, Callable, TypeVar

from integrations.communication.base_adapter import CommunicationRouter, CommunicationUser, Tenant
from integrations.communication.sms_adapter import SMSAdapter
from integrations.communication.whatsapp_adapter import WhatsAppAdapter

from .models import NotificationEvent, NotificationMessage, NotificationPreference
from .schemas import (
    DeliveryDrainRequest,
    EventNotificationRequest,
    EventRouteUpsertRequest,
    InboundWhatsAppReplyRequest,
    NotificationOrchestrationRequest,
    PhoneBindingUpsertRequest,
    PreferenceUpsertRequest,
)
from .store import (
    DatabaseUnavailableError,
    EventRoute,
    InMemoryNotificationStore,
    ServiceUnavailableError,
)
from workflows import WorkflowEngine
from shared.models.workflow import WorkflowAction, WorkflowDefinition, WorkflowTrigger

T = TypeVar("T")

WORKFLOW_EVENT_ROUTES: dict[str, dict[str, Any]] = {
    "learning.low_engagement": {
        "category": "alerts",
        "channels": ["in_app", "push"],
        "subject_template": "Low engagement detected for {course_id}",
        "body_template": "Learner {learner_id} has low engagement in {course_id}.",
        "workflow_action": "alert",
        # BC-INT-01: embedded executable action options
        "action_options": "Reply CONTACT to send learner a message, or INFO for engagement details.",
    },
    "billing.missed_payment": {
        "category": "billing",
        "channels": ["email", "in_app"],
        "subject_template": "Payment reminder for subscription {subscription_id}",
        "body_template": "Payment attempt failed for invoice {invoice_id}. Please retry.",
        "workflow_action": "reminder",
        # BC-INT-01: embedded executable action options
        "action_options": "Reply PAY to initiate payment, or WAIVE to dispute this charge.",
    },
    "learning.low_performance": {
        "category": "alerts",
        "channels": ["email", "in_app"],
        "subject_template": "Performance escalation for {course_id}",
        "body_template": "Learner {learner_id} requires performance escalation in {course_id}.",
        "workflow_action": "escalation",
        # BC-INT-01: embedded executable action options
        "action_options": "Reply CONTACT to send learner a message, or APPROVE to escalate to manager.",
    },
    "workforce.compliance.reminder_required": {
        "category": "compliance",
        "channels": ["email", "in_app"],
        "subject_template": "Mandatory training due soon: {course_id}",
        "body_template": "Learner {learner_id} must complete mandatory training {course_id} by {due_date}.",
        "workflow_action": "reminder",
        # BC-INT-01: embedded executable action options
        "action_options": "Reply ENROLL to confirm enrollment, or INFO for training details.",
    },
    "workforce.manager.digest": {
        "category": "compliance",
        "channels": ["email"],
        "subject_template": "Manager compliance digest",
        "body_template": "You have {non_compliant_count} direct reports with incomplete mandatory training.",
        "workflow_action": "manager_visibility",
        # BC-INT-01: embedded executable action options
        "action_options": "Reply PENDING to view the incomplete training list, or REMIND ALL to send reminders.",
    },
}


def _append_action_options(body: str, route: dict[str, Any]) -> str:
    """BC-INT-01: append embedded action options to outbound message body."""
    options = route.get("action_options", "")
    if not options:
        return body
    return f"{body}\n\n{options}"


class NotificationService:
    def __init__(self, store: InMemoryNotificationStore) -> None:
        self.store = store
        self.database_max_retries = 2
        self.circuit_breaker_threshold = 2
        self.circuit_breaker_open = False
        self._event_bus_failures = 0
        self.whatsapp_adapter = WhatsAppAdapter()
        self.sms_adapter = SMSAdapter()
        self.communication_router = CommunicationRouter(
            adapters={
                "whatsapp": self.whatsapp_adapter,
                "sms": self.sms_adapter,
            },
            fallback_order=["whatsapp", "sms"],
        )
        self.communication_router.whatsapp_adapter = self.whatsapp_adapter
        self.communication_router.sms_adapter = self.sms_adapter
        self.raised_alerts: list[dict[str, Any]] = []
        self.follow_up_tasks: list[dict[str, Any]] = []
        self.workflow_engine = WorkflowEngine(self)
        self._phone_binding_secret = b"notification-service-phone-binding-v1"

    _WHATSAPP_ACTION_ROUTE: dict[tuple[str, str], dict[str, Any]] = {
        ("attendance", "confirm"): {
            "workflow_name": "WhatsApp Attendance Confirmation",
            "trigger_type": "inactivity",
            "trigger_config": {"days": 0},
            "actions": [
                WorkflowAction(
                    action_type="create_follow_up_task",
                    config={"task_type": "attendance_confirmation", "title": "Attendance confirmed"},
                )
            ],
        },
        ("reminder", "ack"): {
            "workflow_name": "WhatsApp Reminder Acknowledged",
            "trigger_type": "inactivity",
            "trigger_config": {"days": 0},
            "actions": [
                WorkflowAction(
                    action_type="create_follow_up_task",
                    config={"task_type": "reminder_acknowledged", "title": "Reminder acknowledged"},
                )
            ],
        },
        ("update", "query"): {
            "workflow_name": "WhatsApp Simple Query",
            "trigger_type": "inactivity",
            "trigger_config": {"days": 0},
            "actions": [
                WorkflowAction(
                    action_type="send_notification",
                    config={
                        "subject": "Learner query received",
                        "body": "A WhatsApp query needs follow-up.",
                        "channels": ["in_app"],
                    },
                ),
                WorkflowAction(
                    action_type="create_follow_up_task",
                    config={"task_type": "learner_query", "title": "Respond to learner WhatsApp query"},
                ),
            ],
        },
    }


    def execute_workflows(
        self,
        tenant_id: str,
        workflows: list[WorkflowDefinition],
        context: dict[str, Any],
        tenant_country_code: str = "ZZ",
    ) -> tuple[int, dict[str, Any]]:
        if not workflows:
            return 200, {"tenant_id": tenant_id, "matched_workflows": 0, "executed_actions": 0, "results": []}

        result = self.workflow_engine.execute(
            tenant_id=tenant_id,
            workflows=workflows,
            context=context,
            tenant_country_code=tenant_country_code,
        )
        return 200, result

    def upsert_phone_binding(self, req: PhoneBindingUpsertRequest) -> tuple[int, dict[str, Any]]:
        self._ensure_service_available()
        normalized_phone = self._normalize_phone(req.phone_e164)
        if normalized_phone is None:
            return 400, {"error": "invalid_phone"}

        try:
            self._with_database_retry(
                lambda: self.store.upsert_phone_binding(
                    tenant_id=req.tenant_id,
                    phone_hash=self._phone_hash(req.tenant_id, normalized_phone),
                    user_id=req.user_id,
                )
            )
        except DatabaseUnavailableError as exc:
            return 503, {"error": "database_unavailable", "detail": str(exc)}

        return 200, {"tenant_id": req.tenant_id, "user_id": req.user_id, "phone_bound": True}

    def handle_whatsapp_inbound_reply(self, req: InboundWhatsAppReplyRequest) -> tuple[int, dict[str, Any]]:
        try:
            self._ensure_service_available()
        except ServiceUnavailableError as exc:
            return 503, {"error": "service_restarting", "detail": str(exc)}

        normalized_phone = self._normalize_phone(req.from_phone_e164)
        if normalized_phone is None:
            return 400, {"error": "invalid_phone"}

        phone_hash = self._phone_hash(req.tenant_id, normalized_phone)
        try:
            user_id = self._with_database_retry(
                lambda: self.store.get_user_by_phone_hash(tenant_id=req.tenant_id, phone_hash=phone_hash)
            )
        except DatabaseUnavailableError as exc:
            return 503, {"error": "database_unavailable", "detail": str(exc)}

        if user_id is None:
            return 403, {"error": "phone_not_mapped", "tenant_id": req.tenant_id}

        parsed = self.whatsapp_adapter.parse_interactive_reply(user_id=user_id, reply=req.reply)
        if parsed is None:
            parsed = self.whatsapp_adapter.classify_free_text_reply(user_id=user_id, reply=req.reply)
        if parsed is None:
            return 202, {"status": "ignored", "reason": "unrecognized_reply", "user_id": user_id}

        route = self._WHATSAPP_ACTION_ROUTE.get((parsed.operation, parsed.action))
        if route is None:
            return 202, {
                "status": "ignored",
                "reason": "unsupported_action",
                "operation": parsed.operation,
                "action": parsed.action,
                "user_id": user_id,
            }

        workflow = WorkflowDefinition(
            workflow_id=f"wa-{parsed.operation}-{parsed.action}",
            name=str(route["workflow_name"]),
            trigger=WorkflowTrigger(
                trigger_type=str(route["trigger_type"]),
                config=dict(route["trigger_config"]),
            ),
            actions=list(route["actions"]),
        )

        status, payload = self.execute_workflows(
            tenant_id=req.tenant_id,
            workflows=[workflow],
            context={
                "inactive_days": 0,
                "recipients": [user_id],
                "reply": req.reply,
                "reply_operation": parsed.operation,
                "reply_action": parsed.action,
                "reply_payload": parsed.payload,
            },
            tenant_country_code=req.tenant_country_code,
        )
        payload["routing"] = {
            "mode": "workflow_engine_only",
            "operation": parsed.operation,
            "action": parsed.action,
            "user_id": user_id,
            "workflow_id": workflow.workflow_id,
        }
        return status, payload

    def upsert_preference(self, req: PreferenceUpsertRequest) -> tuple[int, dict[str, Any]]:
        if not req.channels:
            return 400, {"error": "channels_required"}

        self._ensure_service_available()
        try:
            existing = self._with_database_retry(
                lambda: self.store.get_preference(req.tenant_id, req.user_id, req.category)
            )
            preference = NotificationPreference(
                preference_id=existing.preference_id if existing else self.store.new_id("pref"),
                tenant_id=req.tenant_id,
                user_id=req.user_id,
                category=req.category,
                channels=req.channels,
                created_at=existing.created_at if existing else datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self._with_database_retry(lambda: self.store.upsert_preference(preference))
        except DatabaseUnavailableError as exc:
            return 503, {"error": "database_unavailable", "detail": str(exc)}
        except ServiceUnavailableError as exc:
            return 503, {"error": "service_restarting", "detail": str(exc)}
        return 200, {"preference": asdict(preference)}

    def list_preferences(self, tenant_id: str, user_id: str) -> tuple[int, dict[str, Any]]:
        try:
            self._ensure_service_available()
            preferences = self._with_database_retry(
                lambda: self.store.list_preferences(tenant_id, user_id)
            )
        except DatabaseUnavailableError as exc:
            return 503, {"error": "database_unavailable", "detail": str(exc)}
        except ServiceUnavailableError as exc:
            return 503, {"error": "service_restarting", "detail": str(exc)}
        return 200, {"preferences": [asdict(p) for p in preferences]}

    def upsert_event_route(self, req: EventRouteUpsertRequest) -> tuple[int, dict[str, Any]]:
        if not req.channels:
            return 400, {"error": "channels_required"}

        self._ensure_service_available()
        try:
            existing = self._with_database_retry(
                lambda: self.store.get_route(req.tenant_id, req.event_type)
            )
            route = EventRoute(
                route_id=existing.route_id if existing else self.store.new_id("route"),
                tenant_id=req.tenant_id,
                event_type=req.event_type,
                category=req.category,
                channels=req.channels,
                subject_template=req.subject_template,
                body_template=req.body_template,
            )
            self._with_database_retry(lambda: self.store.upsert_route(route))
        except DatabaseUnavailableError as exc:
            return 503, {"error": "database_unavailable", "detail": str(exc)}
        except ServiceUnavailableError as exc:
            return 503, {"error": "service_restarting", "detail": str(exc)}
        return 200, {"route": asdict(route)}

    def orchestrate_notification(
        self,
        req: NotificationOrchestrationRequest,
        event_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        try:
            self._ensure_service_available()
        except ServiceUnavailableError as exc:
            return 503, {"error": "service_restarting", "detail": str(exc)}

        if self.circuit_breaker_open:
            return 202, {
                "status": "degraded",
                "reason": "event_bus_circuit_open",
                "tenant_id": req.tenant_id,
                "queued": 0,
                "messages": [],
            }

        queued_messages: list[dict[str, Any]] = []
        for user_id in req.recipients:
            try:
                preference = self._with_database_retry(
                    lambda: self.store.get_preference(req.tenant_id, user_id, req.category)
                )
            except DatabaseUnavailableError as exc:
                return 202, {
                    "status": "degraded",
                    "reason": "database_unavailable",
                    "detail": str(exc),
                    "tenant_id": req.tenant_id,
                    "queued": len(queued_messages),
                    "messages": queued_messages,
                }

            for channel in req.channels:
                if not self._channel_enabled(preference, channel):
                    continue
                metadata = dict(req.metadata)
                metadata["tenant_country_code"] = req.tenant_country_code
                message = NotificationMessage(
                    message_id=self.store.new_id("msg"),
                    tenant_id=req.tenant_id,
                    user_id=user_id,
                    category=req.category,
                    channel=channel,
                    subject=req.subject,
                    body=req.body,
                    event_id=event_id,
                    metadata=metadata,
                )
                if not self._persist_message_with_event_bus_retry(message):
                    return 202, {
                        "status": "degraded",
                        "reason": "event_bus_unavailable",
                        "tenant_id": req.tenant_id,
                        "queued": len(queued_messages),
                        "messages": queued_messages,
                    }
                queued_messages.append(asdict(message))

        return 202, {
            "status": "accepted",
            "tenant_id": req.tenant_id,
            "queued": len(queued_messages),
            "messages": queued_messages,
        }

    def process_event(self, req: EventNotificationRequest) -> tuple[int, dict[str, Any]]:
        if req.event_type.startswith("workforce.") and req.payload.get("audience", "workforce") != "workforce":
            return 202, {
                "status": "ignored",
                "reason": "non_workforce_audience",
                "tenant_id": req.tenant_id,
                "event_type": req.event_type,
            }
        try:
            self._ensure_service_available()
            route = self._with_database_retry(lambda: self.store.get_route(req.tenant_id, req.event_type))
        except DatabaseUnavailableError as exc:
            return 503, {"error": "database_unavailable", "detail": str(exc)}
        except ServiceUnavailableError as exc:
            return 503, {"error": "service_restarting", "detail": str(exc)}
        workflow_route = WORKFLOW_EVENT_ROUTES.get(req.event_type)
        if route is None and workflow_route is None:
            return 202, {
                "status": "ignored",
                "reason": "no_route_configured",
                "tenant_id": req.tenant_id,
                "event_type": req.event_type,
            }

        if not req.recipients:
            return 400, {"error": "recipients_required"}

        event = NotificationEvent(
            event_id=self.store.new_id("evt"),
            tenant_id=req.tenant_id,
            event_type=req.event_type,
            actor_id=req.actor_id,
            recipients=req.recipients,
            payload=req.payload,
        )
        try:
            self._with_database_retry(lambda: self.store.save_event(event))
        except DatabaseUnavailableError as exc:
            return 503, {"error": "database_unavailable", "detail": str(exc)}

        if route is not None:
            category = route.category
            channels = route.channels
            subject_template = route.subject_template
            body_template = route.body_template
            workflow_action = req.payload.get("workflow_action")
        else:
            assert workflow_route is not None
            category = str(workflow_route["category"])
            channels = list(workflow_route["channels"])
            subject_template = str(workflow_route["subject_template"])
            body_template = str(workflow_route["body_template"])
            workflow_action = workflow_route["workflow_action"]

        subject = subject_template.format(**req.payload)
        body = _append_action_options(body_template.format(**req.payload), workflow_route or {})
        status, payload = self.orchestrate_notification(
            NotificationOrchestrationRequest(
                tenant_id=req.tenant_id,
                tenant_country_code=req.tenant_country_code,
                category=category,
                recipients=req.recipients,
                channels=channels,
                subject=subject,
                body=body,
                metadata={
                    "event_type": req.event_type,
                    "actor_id": req.actor_id,
                    "workflow_action": workflow_action,
                },
            ),
            event_id=event.event_id,
        )
        payload["event"] = asdict(event)
        return status, payload

    def drain_delivery_queue(self, req: DeliveryDrainRequest) -> tuple[int, dict[str, Any]]:
        try:
            self._ensure_service_available()
        except ServiceUnavailableError as exc:
            return 503, {"error": "service_restarting", "detail": str(exc)}

        if not self.store.gateway_available:
            return 503, {"error": "gateway_unavailable", "detail": "gateway restarting"}

        processed = delivered = failed = 0
        delayed = 0
        delivered_messages: list[dict[str, Any]] = []
        failed_messages: list[dict[str, Any]] = []

        while processed < req.max_messages:
            if self.store.consume_delay_cycle():
                delayed += 1
                continue

            message = self.store.next_message()
            if message is None:
                break
            processed += 1

            if message.channel == "email" and "@" not in message.user_id:
                message.status = "failed"
                message.failure_reason = "unresolvable_email_recipient"
                failed += 1
                failed_messages.append(asdict(message))
                continue

            if message.channel in {"whatsapp", "sms"}:
                tenant = Tenant(country_code=message.metadata.get("tenant_country_code", "ZZ"))
                attempt = self.communication_router.send_message(
                    tenant=tenant,
                    user=CommunicationUser(user_id=message.user_id),
                    message=message.body,
                )
                if not attempt.ok:
                    message.status = "failed"
                    message.failure_reason = attempt.error or "adapter_delivery_failed"
                    failed += 1
                    failed_messages.append(asdict(message))
                    continue
                message.metadata["adapter_provider"] = attempt.provider
                message.metadata["adapter_fallback_used"] = attempt.fallback_used

            message.status = "delivered"
            message.delivered_at = datetime.utcnow()
            delivered += 1
            delivered_messages.append(asdict(message))

        return 200, {
            "processed": processed,
            "delivered": delivered,
            "failed": failed,
            "delayed_cycles": delayed,
            "delivered_messages": delivered_messages,
            "failed_messages": failed_messages,
        }

    def _with_database_retry(self, operation: Callable[[], T]) -> T:
        last_error: DatabaseUnavailableError | None = None
        for _ in range(self.database_max_retries + 1):
            self._ensure_service_available()
            try:
                return operation()
            except DatabaseUnavailableError as exc:
                last_error = exc
        if last_error is None:
            raise DatabaseUnavailableError("database operation failed")
        raise last_error

    def _persist_message_with_event_bus_retry(self, message: NotificationMessage) -> bool:
        for _ in range(self.database_max_retries + 1):
            try:
                self._ensure_event_bus_available()
                self._with_database_retry(lambda: self.store.save_message(message))
                self._event_bus_failures = 0
                self.circuit_breaker_open = False
                return True
            except (DatabaseUnavailableError, ServiceUnavailableError):
                return False
            except RuntimeError:
                self._event_bus_failures += 1
                if self._event_bus_failures >= self.circuit_breaker_threshold:
                    self.circuit_breaker_open = True
                    return False
        return False

    def _ensure_service_available(self) -> None:
        self.store.assert_service_running()

    def _ensure_event_bus_available(self) -> None:
        if not self.store.event_bus_available:
            raise RuntimeError("event bus unavailable")

    @staticmethod
    def _channel_enabled(preference: NotificationPreference | None, channel: str) -> bool:
        if preference is None:
            return True
        return preference.channels.get(channel, False)

    @staticmethod
    def _normalize_phone(phone_e164: str) -> str | None:
        digits = "".join(char for char in phone_e164 if char.isdigit() or char == "+")
        if not digits.startswith("+"):
            return None
        number = digits[1:]
        if not number.isdigit() or not 8 <= len(number) <= 15:
            return None
        return f"+{number}"

    def _phone_hash(self, tenant_id: str, normalized_phone: str) -> str:
        payload = f"{tenant_id}:{normalized_phone}".encode("utf-8")
        return hmac.new(self._phone_binding_secret, payload, hashlib.sha256).hexdigest()
