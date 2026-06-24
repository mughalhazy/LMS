# EVENT_AND_QUEUE_ARCHITECTURE

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

This document captures the event system exactly as implemented. Source of truth for event topics: `infrastructure/event-bus/event_topics.json`. Implementation reality (in-memory, no queue) is documented as-found.

---

## Event Architecture (Updated 2026-06-23)

**No external message broker. All event delivery is in-process via a shared EventBus singleton.**

The implementation is a **shared `EventBus`** at `backend/services/shared/events/bus.py` — NOT per-service `InMemoryEventPublisher` instances. One bus instance (`get_default_bus()` singleton) is shared across all services within the same process.

```python
# Actual pattern — all 68 non-shared services
from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import publish_event

bus = get_default_bus()
# Subscribers:
bus.subscribe("auth.login.failed", handler_fn)
bus.subscribe("*", catch_all_handler)
# Publishers:
publish_event(bus, "lms.enrollment.created.v1", tenant_id="...", payload={...})
```

The `EventBus` supports: thread-safe `subscribe()`, `publish()`, wildcard `"*"` subscriptions, `get_default_bus()` singleton pattern.

It does NOT:
- Persist events to disk
- Deliver events across process/service boundaries
- Guarantee delivery on failure
- Support replay or dead-letter queues

`infrastructure/event-bus/event_topics.json` documents the **intended** event topology for a future external broker. The canonical topic names there (`lms.<domain>.<event>.v1`) are NOT consistently used in current code — see OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md OA-013.

**Consumer handlers**: All `consumers.py` handlers are currently **logging stubs**. Business logic is deferred to a future "event-sprint". auth-service consumers.py line 1: `"business logic is stub (logging only). Full implementation deferred to event-sprint."`

---

## Event Consumer Registration Pattern

Every service registers consumers at module load:

```python
# In every service's main.py
from .consumers import register_consumers as _register_consumers
_register_consumers()
```

The `consumers.py` module calls `get_default_bus().subscribe(topic, handler)`. Registration is local to the process (in-process bus only).

---

## Canonical Event Envelope

10-field implementation in `backend/services/shared/events/envelope.py` `EventEnvelope` dataclass. Anchor (`docs/anchors/event-envelope.md`) defines 7 external fields; 3 additional implementation fields:

| Field | Type | Source | Description |
|---|---|---|---|
| `event_id` | string (UUID) | anchor | Unique event identifier |
| `event_type` | string | anchor | Topic identifier |
| `tenant_id` | string | anchor | Tenant isolation key — never null |
| `timestamp` | ISO 8601 datetime | anchor | When the event occurred *(was `occurred_at` — corrected)* |
| `payload` | object | anchor | Event-specific data |
| `correlation_id` | string | anchor | Correlation chain identifier |
| `metadata` | object | anchor | Additional context metadata |
| `topic` | string | implementation | Routing topic (maps to event_type in most cases) |
| `producer_service` | string | implementation | Originating service name |
| `schema_version` | string | implementation | Schema version (`"v1"`) *(was `version` — corrected)* |

`build_event()` helper constructs the full 10-field envelope. `publish_event()` publishes to the bus.

**Note**: `occurred_at` and `version` field names from prior docs are incorrect. Use `timestamp` and `schema_version` respectively.

---

## Event Topic Registry

Source: `infrastructure/event-bus/event_topics.json`

**Total topics: 39**

Topic naming pattern: `lms.<domain>.<event_type>.v1`

Each topic entry contains: `event_type`, `topic`, `producer_service`, `consumer_services[]`, `contract_file`, `schema_ref`

### Domain: analytics_ingestion (3 topics)

| Topic | Producer | Consumers |
|---|---|---|
| `lms.analytics_ingestion.event_collected.v1` | event-ingestion-service | learning-analytics-service, reporting-service, audit-policy-service |
| `lms.analytics_ingestion.event_rejected.v1` | event-ingestion-service | operations-os-service, audit-policy-service, learning-analytics-service |
| `lms.analytics_ingestion.event_validated.v1` | event-ingestion-service | learning-analytics-service, reporting-service |

*Service name corrected: manifest and event_topics.json both use `event-ingestion-service` (not `analytics-ingestion-service`). Topic event_types corrected from event_topics.json 2026-06-23.*

### Domain: assessment (3 topics)

| Topic | Producer |
|---|---|
| `lms.assessment.attempt_started.v1` | assessment-service |
| `lms.assessment.attempt_submitted.v1` | assessment-service |
| `lms.assessment.attempt_scored.v1` | assessment-service |

### Domain: cohort (4 topics)

| Topic | Producer |
|---|---|
| `lms.cohort.created.v1` | cohort-service |
| `lms.cohort.updated.v1` | cohort-service |
| `lms.cohort.member_added.v1` | cohort-service |
| `lms.cohort.member_removed.v1` | cohort-service |

### Domain: content (4 topics)

| Topic | Producer |
|---|---|
| `lms.content.published.v1` | content-service |
| `lms.content.unpublished.v1` | content-service |
| `lms.content.version_created.v1` | content-service |
| `lms.content.deleted.v1` | content-service |

### Domain: course (4 topics)

| Topic | Producer |
|---|---|
| `lms.course.created.v1` | course-service |
| `lms.course.published.v1` | course-service |
| `lms.course.archived.v1` | course-service |
| `lms.course.updated.v1` | course-service |

### Domain: enrollment (2 topics)

| Topic | Producer |
|---|---|
| `lms.enrollment.created.v1` | enrollment-service |
| `lms.enrollment.status_changed.v1` | enrollment-service |

### Domain: learning_path (4 topics)

| Topic | Producer |
|---|---|
| `lms.learning_path.created.v1` | learning-path-service |
| `lms.learning_path.updated.v1` | learning-path-service |
| `lms.learning_path.assigned.v1` | learning-path-service |
| `lms.learning_path.completed.v1` | learning-path-service |

### Domain: lesson (4 topics)

| Topic | Producer |
|---|---|
| `lms.lesson.created.v1` | lesson-service |
| `lms.lesson.published.v1` | lesson-service |
| `lms.lesson.updated.v1` | lesson-service |
| `lms.lesson.deleted.v1` | lesson-service |

### Domain: media (4 topics)

| Topic | Producer |
|---|---|
| `lms.media.uploaded.v1` | media-service |
| `lms.media.processed.v1` | media-service |
| `lms.media.published.v1` | media-service |
| `lms.media.deleted.v1` | media-service |

### Domain: prerequisite_engine (3 topics)

| Topic | Producer |
|---|---|
| `lms.prerequisite_engine.check_passed.v1` | prerequisite-engine-service |
| `lms.prerequisite_engine.check_failed.v1` | prerequisite-engine-service |
| `lms.prerequisite_engine.rules_updated.v1` | prerequisite-engine-service |

### Domain: progress (4 topics)

| Topic | Producer |
|---|---|
| `lms.progress.lesson_completed.v1` | progress-service |
| `lms.progress.course_completed.v1` | progress-service |
| `lms.progress.learning_path_completed.v1` | progress-service |
| `lms.progress.milestone_reached.v1` | progress-service |

---

## Topic Naming: Canonical vs. Short-Form Aliases

`event_topics.json` defines canonical topic names using the `lms.<domain>.<event>.v1` pattern. Actual service code uses mixed naming:

| Service | Code string used | Canonical equivalent |
|---|---|---|
| auth-service | `"auth.login.failed"` | `lms.auth.login_failed.v1` |
| attempt-service | `"assessment.submission"` | `lms.assessment.attempt_submitted.v1` |
| payment-service | `"payment.success"` | (internal — not in event_topics.json) |
| enrollment-service | `"lms.enrollment.status_changed.v1"` AND `"enrollment.completed"` | dual-subscribe resilience pattern |

The enrollment-service dual-subscribe (`lms.enrollment.status_changed.v1` AND `enrollment.completed`) is an evidence-based resilience pattern — it subscribes to both the canonical name and the short alias so that producers using either convention deliver to consumers. This pattern is intentional and should be documented in event_bus_config.json when canonical topic standardization is implemented.

**Policy:** New event publishing code should use canonical `lms.*` names. Existing short-form aliases remain as-is; introducing alias subscriptions for resilience is permitted with documentation. Standardization of all code to canonical names is OA-013 scope.

---

## Event Governance

Per `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` and governance:

- **Changing event topic names**: REQUIRES_APPROVAL (breaks all consumers)
- **Changing event_type values**: REQUIRES_APPROVAL (breaking contract change)
- **Adding new topics**: requires service-manifest.json update (REQUIRES_APPROVAL)
- **7-field envelope reduction**: PROHIBITED

---

## Gap Analysis

| Gap ID | Description | Severity |
|---|---|---|
| GAP-003 | No real message queue — InMemoryEventPublisher only | CRITICAL |
| GAP-008 | Cross-service event delivery not implemented | CRITICAL |
| GAP-009 | No event persistence — events not replayable | HIGH |
| GAP-010 | No dead-letter queue — failed event handling undefined | HIGH |
| GAP-011 | event_topics.json topology not enforced by runtime | MEDIUM |

---

## Related Documents

- `infrastructure/event-bus/event_topics.json` — canonical topic registry (65 services, 39 topics)
- `docs/anchors/event-envelope.md` — canonical 7-field envelope (PROTECTED)
- `docs/01_backend/BACKEND_ARCHITECTURE.md` — service architecture
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — risk register
- `docs/08_reports/EVENT_DISCOVERY_REPORT.md` — discovery findings
