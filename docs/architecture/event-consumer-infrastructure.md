# Event Consumer Infrastructure — Implementation Design

**Location:** `Repo/docs/architecture/event-consumer-infrastructure.md`
**Status:** ACTIVE — governing doc for FA-024 implementation
**Last updated:** 2026-05-31
**Anchors:** `docs/architecture/event-driven-architecture.md` (ARCH_05), `docs/architecture/event-bus-design.md`

---

## 1) Problem Statement

All service specs define an "Events Consumed" section (§7 in B13 canonical specs). As of the full alignment audit (FA-001–032, 2026-05-30), **zero services have any event consumer infrastructure wired**. Every service publishes events via `InMemoryEventPublisher` but no service subscribes to or processes events from other services.

This document defines the Phase 1 implementation pattern that unblocks all 40 services' event consumption requirements.

---

## 2) Broker Decision

### Phase 1 — In-Process Event Bus (implemented now)

**Decision: extend the existing `InMemoryEventPublisher` pattern with a shared `InProcessEventBus`.**

Rationale:
- All services already use `InMemoryEventPublisher` — same process-local, in-memory pattern
- No external infrastructure required (no Kafka, no Redis, no broker setup)
- Adequate for development, integration testing, and single-node deployment
- Swap-out path to Phase 2 is clean (replace `InProcessEventBus` with a `RedisStreamsEventBus` implementing the same interface)
- Consistent with the platform's current stdlib/in-memory approach across all services

Limitations (accepted for Phase 1):
- No persistence — events lost on process restart
- No replay
- No cross-process delivery (each service process has its own bus)

### Phase 2 — Redis Streams (planned, not yet unblocked)

When operational requirements demand cross-process delivery or persistence:
- Replace `InProcessEventBus` with `RedisStreamsEventBus` implementing identical `EventBus` interface
- Consumer groups via `XREADGROUP` — each service consumer group reads its own cursor
- Dead-letter queue via a separate `lms.events.dlq.v1` stream
- At-least-once delivery with ACK after successful `handle()` call
- Replay via `XRANGE` from any offset

No code changes to service consumer logic required — only swap the bus implementation.

---

## 3) Consumer Interface

All event consumer implementations must conform to the `EventConsumer` protocol:

```python
class EventConsumer(Protocol):
    def handle(self, event: DomainEvent) -> None: ...
```

- `handle()` must be synchronous and idempotent
- If `handle()` raises, the bus logs the error and continues delivery to other consumers (fail-open)
- Consumer implementations must not mutate the event object

---

## 4) InProcessEventBus

Location: `Repo/backend/services/shared/events/bus.py`

```python
class InProcessEventBus:
    """Shared singleton event bus for in-process event delivery.

    Services register consumers via subscribe(); publishing via publish()
    delivers to all matching consumers synchronously in registration order.
    """

    def subscribe(self, event_type_prefix: str, consumer: EventConsumer) -> None:
        """Register consumer for all events whose event_type starts with prefix."""

    def publish(self, event: DomainEvent) -> None:
        """Deliver event to all consumers whose prefix matches event.event_type."""

    def clear(self) -> None:
        """Reset all subscriptions — for test isolation only."""
```

Each service that publishes events also calls `bus.publish()` after `InMemoryEventPublisher.publish()`. Consumer registration happens at service startup.

---

## 5) Consumer Registration Pattern

In each service's `main.py` (or equivalent startup):

```python
from backend.services.shared.events.bus import get_event_bus

bus = get_event_bus()

# Register this service's consumers
bus.subscribe("lms.course.", CourseLessonCountConsumer(service))
bus.subscribe("lms.user.", UserStatusConsumer(service))
```

In each service's publisher:

```python
class BusAwarePublisher:
    def publish(self, event: DomainEvent) -> None:
        self._inner.publish(event)           # store locally
        get_event_bus().publish(event)       # fan-out to subscribers
```

---

## 6) Error Handling

Phase 1 (in-process):
- Consumer `handle()` errors are caught, logged to stderr, and skipped
- Other consumers for the same event are not affected
- No retry — idempotent consumers handle re-delivery naturally

Phase 2 (Redis Streams):
- Failed events → DLQ stream after `max_retries` (default 3)
- DLQ consumers in `operations-os-service` and `audit-service`
- Retry with exponential backoff: 1s, 4s, 16s

---

## 7) Event Naming Convention (canonical)

All event types must use the canonical prefixes from the governing specs:

| Domain | Canonical prefix | Example |
|---|---|---|
| auth | `auth.` | `auth.login.succeeded.v1` |
| user | `lms.user.` | `lms.user.created.v1` |
| course | `lms.course.` | `lms.course.published.v1` |
| enrollment | `enrollment.` | `enrollment.created.v1` |
| assessment | `assessment.` | `assessment.attempt.started.v1` |
| certificate | `lms.certificate.` | `lms.certificate.issued.v1` |
| cohort | `cohort.` | `cohort.created.v1` |
| rbac | `rbac.` | `rbac.role.created.v1` |
| institution | `institution.` | `institution.created.v1` |

Non-canonical prefixes (`authentication.*`, `course.lifecycle.*`) are legacy and must be renamed — see FA-025 and FA-026.

---

## 8) Priority Consumer Pairs (Phase 1 scope)

The following producer→consumer pairs are highest-value for Phase 1 wiring:

| Producer event | Consumer service | Action |
|---|---|---|
| `lms.course.published.v1` | enrollment-service | Validate course is enrollable |
| `lms.user.created.v1` | auth-service | Associate session namespace |
| `enrollment.created.v1` | progress-service | Create progress record stub |
| `enrollment.status_transitioned.v1` | certificate-service | Trigger certificate on completed |
| `assessment.attempt.graded.v1` | progress-service | Update completion signals |

---

## 9) Implementation Files

| File | Purpose |
|---|---|
| `Repo/backend/services/shared/events/bus.py` | `InProcessEventBus` + `get_event_bus()` singleton |
| `Repo/backend/services/shared/events/consumer.py` | `EventConsumer` protocol |
| Each service's `consumers.py` | Service-specific consumer implementations |
