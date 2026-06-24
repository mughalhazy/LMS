"""EventConsumer protocol for FA-024 consumer infrastructure."""

from __future__ import annotations

from typing import Protocol

from .envelope import EventEnvelope


class EventConsumer(Protocol):
    """All event consumer implementations must conform to this protocol.

    handle() must be synchronous and idempotent.
    Raising from handle() is caught by the bus — does not block other consumers.
    """

    def handle(self, event: EventEnvelope) -> None: ...
