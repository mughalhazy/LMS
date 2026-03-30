# B2P04 — Usage Metering Service Design

## 1) Purpose and Scope

The Usage Metering Service provides **event-driven tracking and aggregation of capability usage per tenant**.

It is intentionally separated from billing and entitlement decisioning:

- **Tracking only:** captures and aggregates usage facts.
- **No billing logic inside:** does not calculate prices, invoices, discounts, taxes, or payment status.
- **No capability schema duplication:** stores only stable identifiers (`capability_key`, `tenant_id`, `domain_key`) and event metadata, while authoritative capability definitions remain in the capability registry/service.
- **Domain-agnostic:** supports all capability domains (learning, analytics, communication, AI, integration, etc.) by using common envelope fields rather than domain-specific tables.

## 2) Design Goals

1. **Event-based tracking first**
   - Every usage signal enters through immutable usage events.
2. **Tenant-level aggregation**
   - Support hourly/daily/monthly rollups per `tenant_id + capability_key`.
3. **Scalable architecture**
   - Horizontally scalable ingest and stream processing.
4. **Clear integration boundaries**
   - Integrates with Entitlement Service for enrichment/validation context.
   - Integrates with Billing Service via exported usage aggregates/events only.
5. **Auditability and replay**
   - Durable raw event log enables recomputation of aggregates.

## 3) High-Level Architecture

### 3.1 Components

1. **Usage Metering Ingest API**
   - Accepts signed/internal usage events from domain services.
   - Performs lightweight validation (schema, required IDs, timestamp bounds).
   - Publishes to usage event bus topic.

2. **Usage Event Topic (Event Bus / Kafka/Pulsar equivalent)**
   - Partition key: `tenant_id` (or `tenant_id + capability_key` for hot-tenant balancing).
   - Retention long enough for replay/backfill.

3. **Usage Normalizer & Deduplicator**
   - Validates canonical envelope.
   - Applies idempotency using `event_id` + `producer_id`.
   - Rejects or quarantines malformed/unknown events.

4. **Usage Aggregator (Stream Processor)**
   - Stateful stream jobs compute rolling aggregates:
     - `tenant_capability_hourly_usage`
     - `tenant_capability_daily_usage`
     - `tenant_capability_monthly_usage`
   - Supports late-arriving events with watermark/window strategy.

5. **Usage Query API**
   - Read-only API for operations, analytics, entitlement checks, and billing export jobs.
   - Serves summarized usage, not pricing.

6. **Usage Export Publisher**
   - Emits curated aggregate events (e.g., daily tenant-capability usage) for billing pipeline.
   - Export contracts are versioned and backward-compatible.

7. **Raw Event Store + Aggregate Store**
   - Raw append-only event store for audit/replay.
   - Aggregate store optimized for tenant+capability+time queries.

### 3.2 Data Ownership Boundaries

- **Usage Metering owns:**
  - Usage event acceptance, normalization, dedupe, aggregation, and usage summaries.
- **Entitlement owns:**
  - Whether a tenant/user is allowed to use a capability.
- **Billing owns:**
  - Price plans, rated usage, invoicing, credits, payment lifecycle.
- **Capability Registry owns:**
  - Capability metadata/schema; Metering only references capability keys.

## 4) Canonical Usage Event Model

```json
{
  "event_id": "uuid",
  "event_type": "capability.usage.recorded.v1",
  "occurred_at": "2026-03-30T10:15:00Z",
  "producer": {
    "service": "ai-copilot-service",
    "version": "1.2.0"
  },
  "tenant_id": "tenant_123",
  "actor": {
    "actor_type": "user|system",
    "actor_id": "user_456"
  },
  "domain_key": "learning|analytics|communication|integration|ai|...",
  "capability_key": "ai.learning_copilot.chat_session",
  "usage": {
    "metric_key": "request_count",
    "quantity": 1,
    "unit": "count"
  },
  "context": {
    "resource_id": "course_789",
    "session_id": "sess_abc",
    "region": "us-east-1"
  },
  "idempotency_key": "optional-producer-key"
}
```

### Event Modeling Notes

- `capability_key` is the stable join field to entitlement and billing maps.
- `domain_key` is a filter/grouping helper, not a domain-specific schema fork.
- `usage.metric_key` + `unit` allow multiple metering semantics without schema duplication.
- Producers may emit different metrics, but all must fit canonical envelope.

## 5) Storage Model

### 5.1 Raw Usage Event Table (append-only)

Primary fields:

- `event_id` (PK component)
- `producer_service`
- `tenant_id`
- `capability_key`
- `domain_key`
- `metric_key`
- `quantity`
- `unit`
- `occurred_at`
- `ingested_at`
- `payload_json`

Indexes/partitioning:

- Time partition (`occurred_at` day/month)
- Secondary index: (`tenant_id`, `capability_key`, `occurred_at`)

### 5.2 Aggregate Tables

1. `tenant_capability_usage_hourly`
2. `tenant_capability_usage_daily`
3. `tenant_capability_usage_monthly`

Common dimensions:

- `tenant_id`
- `capability_key`
- `domain_key`
- `metric_key`
- `unit`
- `window_start`
- `window_end`

Measures:

- `total_quantity`
- `event_count`
- `distinct_actor_count` (optional)
- `last_updated_at`

## 6) Usage Flow (Event-Driven)

1. **Capability action occurs** in any domain service (e.g., analytics export, AI prompt request, content publish).
2. Service emits `capability.usage.recorded.v1` to metering ingest/topic.
3. Metering normalizer validates envelope and deduplicates by idempotency key strategy.
4. Valid events are persisted in raw event store (immutable).
5. Stream aggregator updates tenant-capability time windows.
6. Query API serves near-real-time aggregated usage.
7. Export publisher emits usage summaries for Billing (`usage.tenant_capability.daily_aggregated.v1`).
8. Billing consumes summaries and applies pricing externally (outside Metering Service).

## 7) Integration Contracts

### 7.1 Entitlement Integration

- **Optional pre-check pattern:** producer services consult Entitlement before allowing capability execution.
- **Metering enrichment:** Metering may attach entitlement snapshot references (plan/version IDs) for audit context.
- **No authorization ownership transfer:** Metering does not decide entitlement allow/deny.

### 7.2 Billing Integration

- Metering publishes **usage facts/aggregates only**.
- Billing pulls/pushes by contract:
  - `tenant_id`
  - `capability_key`
  - `metric_key`
  - `unit`
  - `window`
  - `total_quantity`
- Billing computes rated charges in its own bounded context.

## 8) Scalability Strategy

1. **Horizontal ingest scale**
   - Stateless ingest replicas behind load balancer.
2. **Partitioned event stream**
   - Key by tenant to parallelize while preserving per-tenant order.
3. **Stateful stream scaling**
   - Scale stream processors by partition count.
4. **Hot-tenant mitigation**
   - Composite partition keys and adaptive sharding for large tenants.
5. **Backpressure controls**
   - Queue buffering, retry topics, DLQ for poison events.
6. **Tiered storage**
   - Hot aggregates in OLTP/serving DB; cold raw events in object storage.
7. **Replay/rebuild capability**
   - Recompute aggregates from raw events after schema/job changes.

## 9) Reliability, Security, and Governance

- **At-least-once ingestion + idempotent processing** for correctness.
- **Schema registry + versioned events** to avoid producer/consumer breaks.
- **PII minimization:** usage events should not require sensitive content payloads.
- **Tenant isolation:** strict row-level tenant scoping in query/export APIs.
- **Observability:** lag, dedupe rate, late-event rate, aggregation freshness, export success.
- **Retention policies:** configurable by compliance class (raw vs aggregate).

## 10) Non-Goals (QC Guardrails)

1. **No billing logic inside Metering Service**.
2. **No duplication of capability schema or capability registry metadata**.
3. **No domain-specific forked meter implementations**; one canonical, domain-agnostic pipeline.
4. **No synchronous coupling to billing for write path**; ingestion remains event-driven.

## 11) API Surface (Minimal)

### Ingest

- `POST /v1/usage/events`
  - Accepts canonical usage events (single or batch).
  - Returns accepted/rejected counts and rejection reasons.

### Query

- `GET /v1/usage/tenants/{tenant_id}/capabilities/{capability_key}`
  - Filters: `from`, `to`, `granularity=hour|day|month`, `metric_key`.

### Export Control (internal)

- `POST /v1/usage/exports/daily`
  - Triggers or checkpoints daily aggregate publication for downstream billing.

---

## Summary

This design delivers a **scalable, event-driven, tenant-aggregated Usage Metering Service** with strict separation from entitlement decisions and billing logic. It supports all capability domains through a canonical usage envelope, avoids capability schema duplication, and provides reliable aggregate outputs for billing and operational consumers.
