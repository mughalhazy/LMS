from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence


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
    """Adapter-driven communication router with configurable fallback order."""

    def __init__(self, adapters: Mapping[str, CommunicationAdapter], fallback_order: Sequence[str]) -> None:
        self._adapters = dict(adapters)
        self._fallback_order = tuple(fallback_order)

        if not self._fallback_order:
            raise ValueError("fallback_order must include at least one channel")

        unknown_channels = [channel for channel in self._fallback_order if channel not in self._adapters]
        if unknown_channels:
            raise ValueError(f"Unknown channels in fallback_order: {unknown_channels}")

    def send_message(self, tenant: Tenant, user: CommunicationUser, message: str) -> DeliveryAttempt:
        del tenant  # Routing is adapter-driven; no tenant/provider hardcoding in router.

        last_channel = self._fallback_order[-1]
        for idx, channel in enumerate(self._fallback_order):
            adapter = self._adapters[channel]
            if adapter.send_message(user, message):
                return DeliveryAttempt(
                    ok=True,
                    provider=adapter.provider_key,
                    fallback_used=idx > 0,
                )

        return DeliveryAttempt(
            ok=False,
            provider=self._adapters[last_channel].provider_key,
            fallback_used=len(self._fallback_order) > 1,
            error=f"{last_channel}_delivery_failed",
        )
