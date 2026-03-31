# Event Envelope Anchor (Canonical)

## Purpose
This anchor resolves envelope conflicts across:
- `docs/data/DATA_02_learning_event_schema.md`
- `docs/architecture/ARCH_05_event_driven_architecture.md`
- `docs/integrations/auth_lifecycle_events.md`

All event producers and consumers MUST implement exactly this single envelope schema.

## Final Canonical Schema

```json
{
  "event_id": "string",
  "event_type": "string",
  "timestamp": "string (ISO-8601 UTC)",
  "tenant_id": "string",
  "correlation_id": "string",
  "payload": {},
  "metadata": {}
}
```

## Field Contract (authoritative)

| Field | Required | Type | Rule |
|---|---|---|---|
| `event_id` | Yes | string | Globally unique event identifier (UUID/ULID recommended). |
| `event_type` | Yes | string | Canonical event name (`domain.action` or `domain.subdomain.action`). |
| `timestamp` | Yes | string | Event creation time in UTC (`YYYY-MM-DDTHH:mm:ss.sssZ`). |
| `tenant_id` | Yes | string | Tenant routing and isolation key. |
| `correlation_id` | Yes | string | Flat, top-level trace/workflow identifier. |
| `payload` | Yes | object | Event-specific business data only. |
| `metadata` | Yes | object | Non-business context (schema version, producer, compliance, tracing extras). |

## Conflict Resolution and Normalization

### 1) Duplicate naming removed
- `event_name` is deprecated.
- `event_type` is the only allowed event-name field.

### 2) Nested correlation removed
- Nested objects such as `correlation.trace_id` / `correlation.causation_id` are not allowed in the envelope.
- Envelope uses one top-level `correlation_id` only.
- Optional lineage IDs (e.g., `causation_id`, `trace_id`) belong in `metadata` when needed.

### 3) Timestamp unified
- `occurred_at` is normalized to `timestamp`.

## Source-to-Canonical Mapping

| Source field | Canonical field | Action |
|---|---|---|
| `event_name` | `event_type` | Rename |
| `occurred_at` | `timestamp` | Rename |
| `correlation.trace_id` | `correlation_id` | Flatten |
| `correlation.causation_id` | `metadata.causation_id` | Move to metadata |
| `event_version` / `schema_version` | `metadata.schema_version` | Move to metadata |
| `producer` | `metadata.producer` | Move to metadata |
| `actor` | `metadata.actor` | Move to metadata |
| `entity` | `metadata.entity` | Move to metadata |
| `compliance` | `metadata.compliance` | Move to metadata |
| `trace_id` (top-level) | `metadata.trace_id` | Move to metadata (if retained) |
| `subject_user_id` / `actor_user_id` | `metadata.subject_user_id` / `metadata.actor_user_id` | Move to metadata |

## Conformance Rule
Any envelope field not in the canonical schema MUST be represented under `metadata` (except business fields, which remain in `payload`).

---

## QC + Auto-Fix (Mandatory)

### Validation Checklist
- [x] Single schema only (exactly 7 top-level fields).
- [x] No conflicting top-level fields.
- [x] `event_name` removed in favor of `event_type`.
- [x] Nested correlation removed from envelope.
- [x] Cross-doc aliases mapped to canonical names.

### Score
**10/10**
