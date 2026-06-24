"""WhatsApp communication adapter stub.

B05-005: communication-adapter-contract.md — required channel "whatsapp".
Provider SDK wiring is external; this stub satisfies the interface contract.
"""
from __future__ import annotations

import logging
from typing import Any

from .base import AdapterResult, CommunicationAdapter

logger = logging.getLogger("integrations.communication.whatsapp")


class WhatsAppAdapter(CommunicationAdapter):
    """WhatsApp channel adapter — satisfies CommunicationAdapter contract."""

    @property
    def channel(self) -> str:
        return "whatsapp"

    def send_message(self, *, channel: str, recipient_id: str, recipient_address: str,
                     body: str, tenant_id: str, template_ref: str | None = None,
                     variables: dict[str, Any] | None = None, subject: str | None = None,
                     idempotency_key: str | None = None, **kwargs: Any) -> AdapterResult:
        logger.info("WhatsApp send to %s (tenant=%s) idempotency=%s", recipient_address, tenant_id, idempotency_key)
        return self._make_result("whatsapp", state="queued")

    def schedule_message(self, *, channel: str, recipient_id: str, recipient_address: str,
                         body: str, send_at: str, tenant_id: str, **kwargs: Any) -> AdapterResult:
        logger.info("WhatsApp scheduled to %s at %s (tenant=%s)", recipient_address, send_at, tenant_id)
        return self._make_result("whatsapp", state="scheduled")

    def broadcast(self, *, channel: str, recipients: list[dict[str, Any]], body: str,
                  tenant_id: str, **kwargs: Any) -> AdapterResult:
        logger.info("WhatsApp broadcast to %d recipients (tenant=%s)", len(recipients), tenant_id)
        return self._make_result("whatsapp", state="accepted")
