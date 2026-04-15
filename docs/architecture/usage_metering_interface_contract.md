# B1P04 — Usage Meter Interface Contract

## Purpose
Define a reusable, domain-agnostic interface for capability usage metering.

This contract handles **usage event intake and aggregation interfaces only**.
It does **not** include billing policy, rating, invoicing, or payment execution logic.

---

## Scope Boundaries (QC)
- **No billing logic included:** this interface records and aggregates usage only; billing systems consume its outputs later.
- **No duplication with capability schema:** capability identity stays in the capability registry; this interface references capability keys as opaque identifiers.
- **Reusable across domains:** event model is generic and does not encode LMS-specific business fields.
- **Supports all capability types:** metering is capability-key based, independent of capability domain/category.
- **Clear I/O structure:** ingest and query contracts define explicit required input and output payloads.

---

## Core Types (TypeScript-style, implementation-agnostic)

```ts
export type CapabilityKey = string;
export type TenantId = string;
export type MeterId = string;

/** Generic usage dimensions supported across any domain/service. */
export interface UsageDimensions {
  actorId?: string;
  resourceId?: string;
  sessionId?: string;
  region?: string;
  channel?: string;
  tags?: string[];
  attributes?: Record<string, string | number | boolean | null>;
}

/** Unitized quantity attached to an event (examples: requests, tokens, minutes, bytes). */
export interface UsageQuantity {
  value: number;
  unit: string;
}

/** Canonical event-based metering record. */
export interface UsageEvent {
  eventId: string;
  occurredAt: string; // ISO-8601 UTC timestamp
  tenantId: TenantId;
  capabilityKey: CapabilityKey;

  /** Generic action marker (invoke, export, generate, sync, etc.). */
  action: string;

  quantity: UsageQuantity;
  dimensions?: UsageDimensions;
  source: {
    service: string;
    environment?: string;
    version?: string;
  };
}

/** Ingestion result for deterministic producer handling. */
export interface UsageIngestResult {
  accepted: boolean;
  meterEventId: MeterId;
  deduplicated: boolean;
  normalizedAt: string; // ISO-8601 UTC timestamp
  validationErrors?: string[];
}
```

---

## Event-based Tracking Interface

```ts
/** Event ingestion only; no rating/pricing logic is defined here. */
export interface UsageEventTracker {
  ingest(event: UsageEvent): Promise<UsageIngestResult>;
  ingestBatch(events: UsageEvent[]): Promise<UsageIngestResult[]>;
}
```

Input:
- One or more `UsageEvent` objects.

Output:
- Per event `UsageIngestResult` indicating acceptance, dedupe state, normalization time, and validation errors.

---

## Aggregation Interface

```ts
export type AggregationWindow = "minute" | "hour" | "day" | "month";

export interface UsageAggregateQuery {
  tenantId: TenantId;
  capabilityKeys?: CapabilityKey[];
  from: string; // ISO-8601 inclusive
  to: string;   // ISO-8601 exclusive
  window: AggregationWindow;

  /** Optional grouped breakdowns for analytics/reconciliation. */
  groupBy?: Array<"capabilityKey" | "action" | "unit" | "region" | "channel">;
}

export interface UsageAggregatePoint {
  windowStart: string; // ISO-8601
  windowEnd: string;   // ISO-8601
  totals: {
    quantity: number;
    eventCount: number;
  };
  key: Record<string, string>; // group-by key/value map
}

export interface UsageAggregateResult {
  tenantId: TenantId;
  from: string;
  to: string;
  window: AggregationWindow;
  points: UsageAggregatePoint[];
  computedAt: string; // ISO-8601 UTC timestamp
}

export interface UsageAggregator {
  aggregate(query: UsageAggregateQuery): Promise<UsageAggregateResult>;
}
```

Input:
- `UsageAggregateQuery` with tenant, time range, window, optional capability filter, and optional groupings.

Output:
- `UsageAggregateResult` with deterministic aggregate points and totals.

---

## Billing System Bridge (Future Link, No Billing Logic)

```ts
/** Export contract for downstream billing/revenue systems. */
export interface UsageBillingExport {
  tenantId: TenantId;
  period: { from: string; to: string };
  aggregates: UsageAggregatePoint[];
  cursor?: string;
  exportedAt: string;
}

export interface UsageBillingBridge {
  /** Provides metered usage snapshots for billing systems to rate externally. */
  exportForBilling(input: {
    tenantId: TenantId;
    from: string;
    to: string;
    cursor?: string;
  }): Promise<UsageBillingExport>;
}
```

This bridge provides normalized usage output for a billing system integration later, while keeping pricing/rating rules outside this contract.

---

## Example Usage Event

```json
{
  "eventId": "evt_01HVW7FQPP2X7A3A9KJ2N8T4Z1",
  "occurredAt": "2026-03-30T10:15:22Z",
  "tenantId": "tenant_acme_42",
  "capabilityKey": "ai.tutor.session",
  "action": "invoke",
  "quantity": {
    "value": 1250,
    "unit": "tokens"
  },
  "dimensions": {
    "actorId": "user_9081",
    "sessionId": "sess_3f8d11",
    "channel": "web",
    "region": "us-east-1",
    "tags": ["interactive", "lesson-help"],
    "attributes": {
      "model_tier": "standard",
      "cached": false
    }
  },
  "source": {
    "service": "ai-tutor-service",
    "environment": "prod",
    "version": "2026.03.30"
  }
}
```

---

## Reuse Guarantees
- The interface is capability-key centric, not domain-object centric, so it can meter any capability class.
- Quantities are unitized (`value` + `unit`) to support heterogeneous usage types without schema changes.
- Dimensions are optional/extensible to avoid domain lock-in.
- Aggregation and export contracts are separate from billing policy to preserve clear responsibility boundaries.
