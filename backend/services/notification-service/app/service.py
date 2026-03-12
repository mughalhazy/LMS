from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from .models import NotificationEvent, NotificationMessage, NotificationPreference
from .schemas import (
    DeliveryDrainRequest,
    EventNotificationRequest,
    EventRouteUpsertRequest,
    NotificationOrchestrationRequest,
    PreferenceUpsertRequest,
)
from .store import EventRoute, InMemoryNotificationStore


class NotificationService:
    def __init__(self, store: InMemoryNotificationStore) -> None:
        self.store = store

    def upsert_preference(self, req: PreferenceUpsertRequest) -> tuple[int, dict[str, Any]]:
        if not req.channels:
            return 400, {"error": "channels_required"}

        existing = self.store.get_preference(req.tenant_id, req.user_id, req.category)
        preference = NotificationPreference(
            preference_id=existing.preference_id if existing else self.store.new_id("pref"),
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            category=req.category,
            channels=req.channels,
            created_at=existing.created_at if existing else datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.store.upsert_preference(preference)
        return 200, {"preference": asdict(preference)}

    def list_preferences(self, tenant_id: str, user_id: str) -> tuple[int, dict[str, Any]]:
        preferences = self.store.list_preferences(tenant_id, user_id)
        return 200, {"preferences": [asdict(p) for p in preferences]}

    def upsert_event_route(self, req: EventRouteUpsertRequest) -> tuple[int, dict[str, Any]]:
        if not req.channels:
            return 400, {"error": "channels_required"}

        existing = self.store.get_route(req.tenant_id, req.event_type)
        route = EventRoute(
            route_id=existing.route_id if existing else self.store.new_id("route"),
            tenant_id=req.tenant_id,
            event_type=req.event_type,
            category=req.category,
            channels=req.channels,
            subject_template=req.subject_template,
            body_template=req.body_template,
        )
        self.store.upsert_route(route)
        return 200, {"route": asdict(route)}

    def orchestrate_notification(
        self,
        req: NotificationOrchestrationRequest,
        event_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        queued_messages: list[dict[str, Any]] = []
        for user_id in req.recipients:
            preference = self.store.get_preference(req.tenant_id, user_id, req.category)
            for channel in req.channels:
                if not self._channel_enabled(preference, channel):
                    continue
                message = NotificationMessage(
                    message_id=self.store.new_id("msg"),
                    tenant_id=req.tenant_id,
                    user_id=user_id,
                    category=req.category,
                    channel=channel,
                    subject=req.subject,
                    body=req.body,
                    event_id=event_id,
                    metadata=req.metadata,
                )
                self.store.save_message(message)
                queued_messages.append(asdict(message))

        return 202, {
            "status": "accepted",
            "tenant_id": req.tenant_id,
            "queued": len(queued_messages),
            "messages": queued_messages,
        }

    def process_event(self, req: EventNotificationRequest) -> tuple[int, dict[str, Any]]:
        route = self.store.get_route(req.tenant_id, req.event_type)
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
        self.store.save_event(event)

        subject = route.subject_template.format(**req.payload)
        body = route.body_template.format(**req.payload)
        status, payload = self.orchestrate_notification(
            NotificationOrchestrationRequest(
                tenant_id=req.tenant_id,
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
        processed = delivered = failed = 0
        delivered_messages: list[dict[str, Any]] = []
        failed_messages: list[dict[str, Any]] = []

        while processed < req.max_messages:
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

            message.status = "delivered"
            message.delivered_at = datetime.utcnow()
            delivered += 1
            delivered_messages.append(asdict(message))

        return 200, {
            "processed": processed,
            "delivered": delivered,
            "failed": failed,
            "delivered_messages": delivered_messages,
            "failed_messages": failed_messages,
        }

    @staticmethod
    def _channel_enabled(preference: NotificationPreference | None, channel: str) -> bool:
        if preference is None:
            return True
        return preference.channels.get(channel, False)
