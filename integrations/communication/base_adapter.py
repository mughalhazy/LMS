from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Tenant:
    country_code: str


@dataclass(frozen=True)
class CommunicationUser:
    user_id: str


@dataclass(frozen=True)
class DeliveryAttempt:
    ok: bool
    provider: str
    fallback_used: bool = False
    error: str | None = None


class CommunicationAdapter(Protocol):
    provider_key: str

    def send_message(self, user: CommunicationUser, message: str) -> bool:
        """Send a communication message to a user."""


class CommunicationRouter:
    """Country-aware communication router with SMS fallback from WhatsApp."""

    def __init__(
        self,
        whatsapp_adapter: CommunicationAdapter,
        sms_adapter: CommunicationAdapter,
        whatsapp_country_codes: set[str] | None = None,
    ) -> None:
        self.whatsapp_adapter = whatsapp_adapter
        self.sms_adapter = sms_adapter
        self.whatsapp_country_codes = whatsapp_country_codes or {"IN", "BR", "MX", "ZA", "AE"}

    def _select_primary(self, tenant: Tenant) -> CommunicationAdapter:
        if tenant.country_code.upper() in self.whatsapp_country_codes:
            return self.whatsapp_adapter
        return self.sms_adapter

    def send_message(self, tenant: Tenant, user: CommunicationUser, message: str) -> DeliveryAttempt:
        primary = self._select_primary(tenant)
        primary_ok = primary.send_message(user, message)
        if primary_ok:
            return DeliveryAttempt(ok=True, provider=primary.provider_key)

        if primary.provider_key == self.sms_adapter.provider_key:
            return DeliveryAttempt(ok=False, provider=primary.provider_key, error="sms_delivery_failed")

        sms_ok = self.sms_adapter.send_message(user, message)
        if sms_ok:
            return DeliveryAttempt(
                ok=True,
                provider=self.sms_adapter.provider_key,
                fallback_used=True,
            )
        return DeliveryAttempt(
            ok=False,
            provider=self.sms_adapter.provider_key,
            fallback_used=True,
            error="fallback_sms_delivery_failed",
        )
