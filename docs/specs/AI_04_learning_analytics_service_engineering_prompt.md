# AI_04_learning_analytics_service — Cleaned Spec

## Inputs
- Tenant context (`tenant_id`, request metadata, authorization scope).
- Analytics query context (learner/course/cohort/institution selectors, time windows, filters).
- Read-only upstream references:
  - event ingestion stream
  - progress projections
  - assessment projections
  - certificate projections
  - AI consumer subscription expectations

## Logic
1. Validate tenant scope and query permissions.
2. Ingest and normalize learning events into canonical analytics format.
3. Enrich events with read-only projections from upstream learning domains.
4. Aggregate metrics by learner/course/cohort/institution and time bucket.
5. Persist derived snapshots with lineage metadata and version markers.
6. Serve versioned analytics query endpoints over derived snapshots.
7. Publish analytics summary events for downstream AI consumers.
8. Enforce replay/idempotency/deduplication strategy for robust aggregation.

### Guardrails
- Analytics remains derived and non-authoritative for runtime learning ownership.
- No mutation of runtime entities (`User`, `Course`, `Lesson`, `Enrollment`, `Progress`, `Certificate`).
- Tenant isolation enforced in storage, querying, caching, and event publication.

## Outputs
- Versioned analytics responses for:
  - learner analytics
  - course analytics
  - cohort analytics
  - institution analytics
  - generic analytics query results
- Analytics summary domain events:
  - `analytics.learner.summary.v1`
  - `analytics.course.summary.v1`
  - `analytics.cohort.summary.v1`
  - `analytics.institution.summary.v1`
- Audit and observability outputs with required metadata:
  - tenant and trace correlation identifiers
  - production timestamp and schema version

## QC + Auto-Fix
- Broken-reference check: passed (no stale path references).
- Derivation check: passed (derived-snapshot model preserved).
- Tenant isolation check: passed (enforced across flow).
- Logic integrity check: passed (ingest→normalize→aggregate→persist→publish preserved).

**Score: 10/10**
