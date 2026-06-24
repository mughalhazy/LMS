# EVENT_DISCOVERY_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-23
Owner: AI
Phase: Phase 2 — Backend Authority Capture

Source: Direct code inspection + infrastructure/event-bus/event_topics.json

---

## Purpose

Detailed findings from Phase 2 inspection of the event architecture. Documents what was designed (event_topics.json), what is implemented (InMemoryEventPublisher), and the gap between them.

---

## What Was Found

### Infrastructure Configuration

**File**: `infrastructure/event-bus/event_topics.json`
- **Format version**: 1
- **Total topics**: 39
- **Topic naming convention**: `lms.<domain>.<event_type>.v1`
- **All topics** at version `v1` (no versioned migrations)
- **Each topic defines**: `event_type`, `topic`, `producer_service`, `consumer_services[]`, `contract_file`, `schema_ref`

### Implementation

Every service inspected uses:

```python
from backend.services.shared.events.bus import get_default_bus
bus = get_default_bus()  # shared singleton
bus.subscribe("auth.login.failed", handler_fn)
```

**Correction (2026-06-23)**: The event system is NOT per-service `InMemoryEventPublisher` instances. It is a **shared `EventBus` singleton** at `backend/services/shared/events/bus.py`. All 68 non-shared services import from this shared bus. `InMemoryEventPublisher` is an obsolete name that no longer reflects the implementation.

Event consumers are registered at startup:
```python
from .consumers import register_consumers as _register_consumers
_register_consumers()  # calls get_default_bus().subscribe(...)
```

Consumer registration is local to the process (in-process bus only — no cross-service delivery).

**Consumer handlers**: All `consumers.py` handlers are currently logging stubs. Business logic deferred to event-sprint.

---

## Producer → Consumer Topology (From event_topics.json)

This topology is documented but not enforced by any runtime mechanism:

| Domain | Topics | Producer | Consumers (Documented) |
|---|---|---|---|
| analytics_ingestion | 3 | event-ingestion-service | learning-analytics-service, reporting-service, audit-policy-service |
| assessment | 3 | assessment-service | (per JSON) |
| cohort | 4 | cohort-service | (per JSON) |
| content | 4 | content-service | (per JSON) |
| course | 4 | course-service | (per JSON) |
| enrollment | 2 | enrollment-service | (per JSON) |
| learning_path | 4 | learning-path-service | (per JSON) |
| lesson | 4 | lesson-service | (per JSON) |
| media | 4 | media-service | (per JSON) |
| prerequisite_engine | 3 | prerequisite-engine-service | (per JSON) |
| progress | 4 | progress-service | (per JSON) |

Total: 11 domains × avg 3.5 topics = 39 topics confirmed.

---

## Gap: Design vs. Reality

| Designed Element | Implementation Reality |
|---|---|
| 39 event topics with producer→consumer routing | event_topics.json defines routing; `InMemoryEventPublisher` does not use this file |
| Cross-service event delivery | Not implemented — all events are local to process |
| Event persistence | None — events are transient |
| Consumer service subscription | In-memory registration only; does not survive restart |
| Dead-letter handling | Not implemented |
| Event replay | Not implemented |
| Schema validation on event | Not implemented at infrastructure level |

---

## Event Consumer Pattern (Per Service)

Each service's `consumers.py` registers handlers for events it cares about. Because the publisher is in-memory, these handlers only fire when called within the same process.

For example, if `enrollment-service` publishes `lms.enrollment.created.v1`, and `progress-service` has a consumer registered for that topic, the consumer **does not fire** because the publisher and consumer are in separate processes.

---

## Canonical Event Envelope

7-field structure (from `docs/anchors/event-envelope.md` — PROTECTED):

```python
# Inferred from code context (anchor doc is authoritative)
{
    "event_id": str,       # UUID
    "event_type": str,     # e.g., "lms.enrollment.created.v1"
    "tenant_id": str,      # always required
    "producer_service": str,
    "occurred_at": str,    # ISO 8601
    "version": str,        # "v1"
    "payload": dict        # event-specific data
}
```

---

## Observations From Service Inspection

### enrollment-service

- Declares `InMemoryEventPublisher` in service.py (imported into main.py)
- FA-024 / G-24 compliance: `register_consumers()` called at startup
- Published events: likely `lms.enrollment.created.v1`, `lms.enrollment.status_changed.v1`

### progress-service

- `InMemoryEventPublisher` declared in service.py
- Published events: likely `lms.progress.lesson_completed.v1`, `lms.progress.course_completed.v1`
- certificate-service likely intended to consume progress events (not wired)

### rbac-service

- Has dedicated `events.py` with `InMemoryEventPublisher` and `InMemoryObservabilityHook`
- Events likely include authorization decision events (not in event_topics.json — internal)

### tenant-service

- Has `InMemoryEventPublisher` + `InMemoryTenantStore`
- Events include tenant lifecycle transitions

---

## Event Governance Rules (From REVISED_DECISION_ESCALATION_MATRIX.md)

| Action | Tier |
|---|---|
| Changing event topic names | REQUIRES_APPROVAL |
| Changing `event_type` values in envelope | REQUIRES_APPROVAL |
| Adding new topics to event_topics.json | REQUIRES_APPROVAL (manifest update needed) |
| Reducing 7-field envelope below 7 fields | PROHIBITED |
| Documenting event topology | AUTONOMOUS |
| Generating event reports | SAFE_REPOSITORY_HYGIENE |

---

## Impact of Missing Message Queue

The following platform workflows currently do not function end-to-end because cross-service events are not delivered:

| Workflow | Requires Event | Missing Cross-Service Link |
|---|---|---|
| Enrollment → Certificate issuance | `lms.enrollment.status_changed.v1` | enrollment-service → certificate-service |
| Lesson completion → Progress update | `lms.lesson.completed.v1` | lesson-service → progress-service |
| Course completion → Badge award | `lms.progress.course_completed.v1` | progress-service → badge-service |
| Assessment attempt → Score record | `lms.assessment.attempt_scored.v1` | assessment-service → analytics-service |
| Enrollment → Prerequisite check | event | enrollment-service → prerequisite-engine |

These workflows would only function if:
1. The services are in the same process (not the case in microservice deployment)
2. A real message broker is introduced

---

## Recommended Path (Observation Only — Not a Decision)

A real message queue implementation would require:
1. Owner decision on broker technology (Kafka, RabbitMQ, Redis Streams, or SQS/Pub-Sub)
2. Replacement of `InMemoryEventPublisher` with a real publisher adapter
3. External consumer process per consuming service
4. The event_topics.json topology can guide the implementation

This is D-003 scope if it includes infrastructure platform decisions.

---

## Related Documents

- `infrastructure/event-bus/event_topics.json` — authoritative topic registry
- `docs/anchors/event-envelope.md` — canonical 7-field envelope (PROTECTED)
- `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` — architecture document
- `docs/08_reports/BACKEND_GAP_REGISTER.md` — GAP-003, GAP-006
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — RISK-006
