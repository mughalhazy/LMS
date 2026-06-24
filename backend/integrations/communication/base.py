"""Channel-agnostic communication adapter base types.

B05-005: communication-adapter-contract.md — CommunicationAdapter interface +
CommunicationAdapterRegistry per BC-COMMS-01 / MS-ADAPTER-01.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


DeliveryState = str  # accepted | scheduled | queued | sent | delivered | failed | cancelled


@dataclass
class AdapterResult:
    operation_id: str
    channel: str
    state: DeliveryState
    accepted_at: str
    provider_ref: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class CommunicationAdapter(ABC):
    """Runtime contract for communication transports (communication-adapter-contract.md)."""

    @property
    @abstractmethod
    def channel(self) -> str:
        """Runtime-identifiable channel handled by this adapter."""

    @abstractmethod
    def send_message(
        self,
        *,
        channel: str,
        recipient_id: str,
        recipient_address: str,
        body: str,
        subject: str | None = None,
        template_ref: str | None = None,
        variables: dict[str, Any] | None = None,
        tenant_id: str,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> AdapterResult:
        """Immediate send (single recipient)."""

    @abstractmethod
    def schedule_message(
        self,
        *,
        channel: str,
        recipient_id: str,
        recipient_address: str,
        body: str,
        send_at: str,
        tenant_id: str,
        **kwargs: Any,
    ) -> AdapterResult:
        """Delayed send (single recipient)."""

    @abstractmethod
    def broadcast(
        self,
        *,
        channel: str,
        recipients: list[dict[str, Any]],
        body: str,
        tenant_id: str,
        **kwargs: Any,
    ) -> AdapterResult:
        """Multi-recipient fan-out operation."""

    @staticmethod
    def _make_result(channel: str, state: DeliveryState = "accepted") -> AdapterResult:
        return AdapterResult(
            operation_id=str(uuid4()),
            channel=channel,
            state=state,
            accepted_at=datetime.now(timezone.utc).isoformat(),
        )


class CommunicationAdapterRegistry:
    """Adapter registry/router — callers remain channel-agnostic."""

    def __init__(self) -> None:
        self._adapters: dict[str, CommunicationAdapter] = {}

    def register(self, adapter: CommunicationAdapter) -> None:
        self._adapters[adapter.channel] = adapter

    def resolve(self, channel: str) -> CommunicationAdapter | None:
        return self._adapters.get(channel)

    def list(self) -> list[CommunicationAdapter]:
        return list(self._adapters.values())
