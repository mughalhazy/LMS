from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from integrations.communication import (
    CommunicationRouter,
    CommunicationUser,
    DeliveryAttempt,
    EmailAdapter,
    SMSAdapter,
    Tenant,
    WhatsAppAdapter,
)


@dataclass(frozen=True)
class NotificationOrchestrationConfig:
    """Configuration for channel adapter ordering and adapter-level controls."""

    fallback_order: Sequence[str] = ("whatsapp", "sms")
    whatsapp_disabled_recipients: set[str] | None = None
    sms_disabled_recipients: set[str] | None = None
    email_disabled_recipients: set[str] | None = None


class NotificationOrchestrator:
    """Adapter-driven orchestration for outbound notification delivery."""

    def __init__(self, config: NotificationOrchestrationConfig | None = None) -> None:
        cfg = config or NotificationOrchestrationConfig()

        adapters = {
            "whatsapp": WhatsAppAdapter(disabled_recipients=cfg.whatsapp_disabled_recipients),
            "sms": SMSAdapter(disabled_recipients=cfg.sms_disabled_recipients),
            "email": EmailAdapter(disabled_recipients=cfg.email_disabled_recipients),
        }

        self._router = CommunicationRouter(adapters=adapters, fallback_order=cfg.fallback_order)

    def send_notification(self, *, tenant_country_code: str, user_id: str, message: str) -> DeliveryAttempt:
        tenant = Tenant(country_code=tenant_country_code)
        user = CommunicationUser(user_id=user_id)
        return self._router.send_message(tenant=tenant, user=user, message=message)
