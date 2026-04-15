from __future__ import annotations

# CGAP-082 — Event bus transport layer.
# Previously build_event() in envelope.py created EventEnvelope objects with no transport.
# This module provides the in-process pub/sub bus used by all backend services.
#
# Architecture reference: ARCH_05 §5 (event bus responsibilities), event_envelope.md
# Spec: event_ingestion_spec.md §4.1 (event bus ingestion — primary path)
#
# Production deployments swap get_default_bus() for a Kafka/Pulsar/RabbitMQ adapter
# that implements the same subscribe/publish interface.

import threading
from collections import defaultdict
from typing import Callable

from .envelope import EventEnvelope

Handler = Callable[[EventEnvelope], None]


class EventBus:
    """In-process pub/sub event bus implementing ARCH_05 event bus responsibilities.

    Topic matching:
    - Exact topic string — handler receives events published to that exact topic.
    - Wildcard "*" — handler receives all published events regardless of topic.

    Delivery semantics:
    - At-least-once per ARCH_05 §5. Handler errors are swallowed so the bus
      never propagates failures back to producers.
    - No persistence or replay in this implementation; upgrade to a durable broker
      for production replay/DLQ requirements.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._topic_handlers: dict[str, list[Handler]] = defaultdict(list)
        self._wildcard_handlers: list[Handler] = []

    def subscribe(self, topic: str, handler: Handler) -> None:
        """Register a handler for a specific topic or "*" for all topics."""
        with self._lock:
            if topic == "*":
                self._wildcard_handlers.append(handler)
            else:
                self._topic_handlers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        """Remove a previously registered handler."""
        with self._lock:
            if topic == "*":
                self._wildcard_handlers = [h for h in self._wildcard_handlers if h is not handler]
            else:
                self._topic_handlers[topic] = [
                    h for h in self._topic_handlers.get(topic, []) if h is not handler
                ]

    def publish(self, event: EventEnvelope) -> int:
        """Deliver event to all matching subscribers. Returns handler delivery count.

        Handler errors are silently swallowed — bus delivery must not fail producers.
        Per ARCH_05 §5 at-least-once semantics.
        """
        with self._lock:
            handlers = (
                list(self._topic_handlers.get(event.topic, []))
                + list(self._wildcard_handlers)
            )
        count = 0
        for handler in handlers:
            try:
                handler(event)
                count += 1
            except Exception:
                # Intentional: bus delivery must never propagate handler failures.
                pass
        return count

    def subscriber_count(self, topic: str | None = None) -> int:
        """Return number of registered subscribers for a topic, or total if topic is None."""
        with self._lock:
            if topic is None:
                return (
                    sum(len(handlers) for handlers in self._topic_handlers.values())
                    + len(self._wildcard_handlers)
                )
            return len(self._topic_handlers.get(topic, [])) + len(self._wildcard_handlers)

    def reset(self) -> None:
        """Remove all subscriptions. Primarily for test isolation."""
        with self._lock:
            self._topic_handlers.clear()
            self._wildcard_handlers.clear()


_default_bus: EventBus | None = None
_bus_init_lock = threading.Lock()


def get_default_bus() -> EventBus:
    """Return the process-level singleton EventBus instance.

    Thread-safe double-checked locking. The returned instance is shared across
    all backend services in this process — equivalent to a single Kafka cluster
    in a real deployment.
    """
    global _default_bus
    if _default_bus is None:
        with _bus_init_lock:
            if _default_bus is None:
                _default_bus = EventBus()
    return _default_bus
