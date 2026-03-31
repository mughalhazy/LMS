from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable, TypeVar

from integrations.communication.base_adapter import CommunicationRouter, CommunicationUser, Tenant
from integrations.communication.sms_adapter import SMSAdapter
from integrations.communication.whatsapp_adapter import WhatsAppAdapter

from .models import NotificationEvent, NotificationMessage, NotificationPreference
from .schemas import (
    DeliveryDrainRequest,
    EventNotificationRequest,
    EventRouteUpsertRequest,
    NotificationOrchestrationRequest,
    PreferenceUpsertRequest,
)
from .store import (
    DatabaseUnavailableError,
    EventRoute,
    InMemoryNotificationStore,
    ServiceUnavailableError,
)

T = TypeVar("T")


class NotificationService:
    def __init__(self, store: InMemoryNotificationStore) -> None:
        self.store = store
        self.database_max_retries = 2
        self.circuit_breaker_threshold = 2
        self.circuit_breaker_open = False
        self._event_bus_failures = 0
        self.communication_router = CommunicationRouter(
            whatsapp_adapter=WhatsAppAdapter(),
            sms_adapter=SMSAdapter(),
        )

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
        try:
            self._ensure_service_available()
            route = self._with_database_retry(lambda: self.store.get_route(req.tenant_id, req.event_type))
        except DatabaseUnavailableError as exc:
            return 503, {"error": "database_unavailable", "detail": str(exc)}
        except ServiceUnavailableError as exc:
            return 503, {"error": "service_restarting", "detail": str(exc)}
        if route is None:
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

        subject = route.subject_template.format(**req.payload)
        body = route.body_template.format(**req.payload)
        status, payload = self.orchestrate_notification(
            NotificationOrchestrationRequest(
                tenant_id=req.tenant_id,
                tenant_country_code=req.tenant_country_code,
                category=route.category,
                recipients=req.recipients,
                channels=route.channels,
                subject=subject,
                body=body,
                metadata={"event_type": req.event_type, "actor_id": req.actor_id},
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
                tenant = Tenant(country_code=message.metadata.get("tenant_country_code", "US"))
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
