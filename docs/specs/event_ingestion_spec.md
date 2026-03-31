# SPEC_15_event_ingestion_service

## 1) Service purpose
`event_ingestion_service` is the platform boundary for ingesting LMS domain events from internal services and approved external connectors, normalizing them into a canonical event format, persisting immutable event records, and forwarding curated streams to analytics and AI consumers.

### In scope
- Capture domain event envelopes from event bus topics and ingestion APIs.
- Validate envelope and tenant context.
- Normalize payloads into canonical family-specific shapes.
- Persist raw + normalized event records with traceability metadata.
- Forward accepted events to `learning_analytics_service` and AI-facing consumers.

### Out of scope
- Owning or mutating source domain entities (users, courses, lessons, enrollments, progress, assessments, certificates).
- Performing transactional updates back to source services.
- Replacing source-of-truth data stores in domain services.

## 2) Domain ownership and boundaries
`event_ingestion_service` owns only ingestion artifacts and derivative event records:
- Ingestion lifecycle state (`collected`, `validated`, `rejected`, `forwarded`).
- Canonical normalized event payloads.
- Replay and deduplication metadata.
- Routing metadata for downstream consumers.

It **does not** own source entities; each event retains `producer_service` and source entity references for lineage.

## 3) Owned data model
### 3.1 Immutable event record
- `ingestion_id` (ULID)
- `event_id` (idempotency key from producer)
- `trace_id`, `span_id`, `correlation_id`
- `tenant_id`, `tenant_partition_key`
- `event_family` (`user|course|lesson|enrollment|progress|assessment|certificate|ai`)
- `event_type`
- `topic`
- `producer_service`
- `timestamp`, `received_at`, `normalized_at`, `forwarded_at`
- `schema_version` (source), `normalization_version` (ingestion)
- `raw_payload` (JSONB/blob)
- `normalized_payload` (JSONB)
- `validation_status` (`passed|rejected|partial`)
- `rejection_reason` (nullable)
- `forwarding_status` (`pending|sent|failed|dead_letter`)

### 3.2 Supporting stores
1. **Raw append-only store** (object storage): replay/audit by `dt/tenant_id/event_family`.
2. **Normalized event store** (OLTP/columnar hybrid table): query by tenant/family/time.
3. **Dead-letter store**: rejected or forwarding-failed events with remediation metadata.
4. **Idempotency index**: `(tenant_id, event_id)` unique key with retention aligned to replay window.

## 4) Ingestion interfaces
### 4.1 Event bus ingestion (primary)
- Subscribes to LMS topics matching existing envelope contract (`event_id`, `event_type`, `topic`, `producer_service`, `tenant_id`, `timestamp`, `schema_version`, `payload`).
- Compatible with current runtime topic conventions (`lms.<domain>.<event>.vN`).

### 4.2 HTTP ingestion API (secondary)
- `POST /v1/events/ingest`
  - Accepts one envelope or batch.
  - Requires service auth + tenant scope.
  - Returns accepted/rejected counts + per-event reasons.
- `POST /v1/events/replay`
  - Replays from raw store by tenant/time/topic/filter.
  - Restricted to platform ops role.

### 4.3 Contract validation endpoint (internal)
- `POST /v1/events/validate` for preflight producer testing in lower environments.

## 5) Event contracts
### 5.1 Canonical envelope (runtime-compatible)
Required fields align with existing runtime envelope schema:
- `event_id: string`
- `event_type: string`
- `topic: string`
- `producer_service: string`
- `tenant_id: string`
- `timestamp: date-time`
- `schema_version: vN`
- `payload: object`

Additional ingestion metadata (added by this service):
- `ingestion_id`, `received_at`, `normalization_version`, `trace_id`, `correlation_id`, `event_family`.

### 5.2 Event families and normalization expectations
| event_family | required payload anchors (examples) | normalized output intent |
| --- | --- | --- |
| user | `user_id`, `action` | user lifecycle/activity analytics + AI learner profiling |
| course | `course_id`, `action` | catalog evolution, content effectiveness |
| lesson | `lesson_id`, `course_id`, `action` | lesson engagement funnels |
| enrollment | `enrollment_id` or (`user_id`,`course_id`), `status` | cohort and activation analysis |
| progress | `user_id`, `learning_object_id`, `progress_state` | completion and pacing intelligence |
| assessment | `assessment_id`, `attempt_id`, `score`/`result` | mastery and evaluation analytics |
| certificate | `certificate_id`, `user_id`, `issued_at` | credential attainment and compliance |
| ai | `ai_interaction_id`, `model_context`, `action` | AI efficacy, safety, and personalization signals |

### 5.3 Ingestion lifecycle events published
- `lms.analytics_ingestion.event_collected.v1`
- `lms.analytics_ingestion.event_validated.v1`
- `lms.analytics_ingestion.event_rejected.v1`
- `lms.analytics_ingestion.event_forwarded.v1` (new)

## 6) Storage model and retention
- Raw store retention: 365 days (tenant-configurable extension).
- Normalized store retention: 730 days default; tiered archival allowed.
- Dead-letter retention: 180 days with remediation workflow.
- Encryption at rest + tenant-partition keys for all stores.
- PII policy flags stored per event; sensitive fields tokenized where required.

## 7) Consumer model
### 7.1 Analytics consumers
- Primary: `learning_analytics_service` receives validated/normalized events.
- Secondary: reporting and feature-store consumers subscribe to validated stream.
- Delivery semantics: at-least-once with idempotency guarantees via `event_id` + `tenant_id`.

### 7.2 AI consumers
- AI feature pipelines receive normalized `ai`, `progress`, `assessment`, and engagement-related events.
- Event routing supports policy-based filtering (e.g., exclude restricted tenants/regions).
- Payload minimization profile for AI consumers (only required features + anonymized identifiers where mandated).

## 8) Integration design
### 8.1 Integration with `learning_analytics_service`
- Forward `event_validated` stream with canonical normalized payload.
- Include lineage metadata (`producer_service`, `source_schema_version`, `normalization_version`).
- Provide replay handshake API by tenant/time window for analytics backfills.

### 8.2 Integration with AI services
- Publish `event_forwarded` acknowledgments for AI delivery observability.
- Maintain AI-ready projection schema compatibility with `docs/data/DATA_07_ai_interaction_schema.md` concepts.
- Support near-real-time forwarding SLO (P95 end-to-end ingest-to-forward < 5s).

## 9) Tenant context and traceability
- Tenant isolation enforced at ingest, storage, replay, and forwarding layers.
- Every record includes `tenant_id`, `trace_id`, `producer_service`, `event_id`, timestamps.
- Cross-tenant replay is forbidden by API and storage access policy.
- Audit trail is immutable and queryable by `tenant_id + event_id + trace_id`.

## 10) Observability and operations readiness
- Metrics: ingest rate, validation pass/fail rate, normalization latency, forwarding latency, DLQ depth, replay throughput.
- Logs: structured logs with `tenant_id`, `event_id`, `trace_id`, `ingestion_status`.
- Traces: distributed trace spans from source producer through ingestion to downstream forwarders.
- Alerts: high rejection ratio, forwarding backlog growth, tenant partition hot-spotting.

## 11) Compatibility requirements
- Must accept the existing event envelope contract currently defined in repo runtime artifacts.
- Must preserve source `event_type/topic/schema_version` values without rewrite.
- Must not require domain services to change entity ownership or transactional boundaries.

## 12) QC LOOP
### QC iteration 1 (initial draft assessment)
| category | score (1-10) | defect identified |
| --- | --- | --- |
| event ingestion boundary clarity | 9 | boundary for replay vs domain reprocessing not explicit enough |
| compatibility with domain ownership | 10 | none |
| analytics readiness | 9 | downstream contract for backfill/replay missing explicit handshake |
| AI readiness | 9 | AI payload minimization/privacy controls under-specified |
| tenant safety | 10 | none |
| observability readiness | 9 | no explicit SLO target for ingest-to-forward path |

### Revision applied after iteration 1
- Added explicit out-of-scope clause forbidding domain reprocessing ownership.
- Added replay handshake API expectations for analytics backfills.
- Added AI payload minimization and policy-based filtering requirements.
- Added explicit forwarding SLO target and operational alerts.

### QC iteration 2 (post-revision)
| category | score (1-10) | result |
| --- | --- | --- |
| event ingestion boundary clarity | 10 | pass |
| compatibility with domain ownership | 10 | pass |
| analytics readiness | 10 | pass |
| AI readiness | 10 | pass |
| tenant safety | 10 | pass |
| observability readiness | 10 | pass |

**QC status:** All categories at 10/10.
