# B1P08 — Offline Sync Interface Contract

## Purpose
Define a modular, implementation-agnostic interface for offline learning synchronization.

This contract covers **offline sync orchestration interfaces only**:
- content download orchestration
- sync queue lifecycle
- resume/retry synchronization

It explicitly excludes learning-core domain logic, storage implementation details, and delivery-player/runtime behavior.

---

## Scope Boundaries (QC)
- **No overlap with learning core:** course sequencing, grading, mastery, attempt scoring, and completion rules remain in learning-core services.
- **No storage logic:** this contract does not define database schemas, file systems, cache engines, object stores, or encryption-at-rest implementation.
- **Modular by design:** each responsibility is isolated behind dedicated ports/interfaces (download, queue, transport, learning integration).
- **Failure recovery required:** queue entries and transfer sessions are resumable with idempotent replay semantics.
- **Separated from delivery system:** playback/rendering/offline media runtime is outside this contract; only sync metadata and progress exchange are handled.

---

## Core Types (TypeScript-style, implementation-agnostic)

```ts
export type TenantId = string;
export type LearnerId = string;
export type EnrollmentId = string;
export type ContentRef = string;
export type SyncItemId = string;
export type CorrelationId = string;

export type ConnectivityState = "online" | "degraded" | "offline";

export interface NetworkSnapshot {
  observedAt: string; // ISO-8601 UTC
  state: ConnectivityState;
  estimatedBandwidthKbps?: number;
  packetLossPct?: number;
  jitterMs?: number;
}

export interface DownloadRequest {
  tenantId: TenantId;
  learnerId: LearnerId;
  enrollmentId: EnrollmentId;
  content: Array<{
    contentRef: ContentRef;
    priority?: number;
    expectedBytes?: number;
    checksum?: string;
  }>;
  requestedAt: string; // ISO-8601 UTC
  correlationId: CorrelationId;
}

export type SyncOperation =
  | "progress_upsert"
  | "attempt_event_append"
  | "content_manifest_refresh";

export interface SyncQueueItem {
  syncItemId: SyncItemId;
  tenantId: TenantId;
  learnerId: LearnerId;
  enrollmentId: EnrollmentId;
  operation: SyncOperation;
  payload: Record<string, unknown>; // opaque to offline-sync contract
  attemptCount: number;
  nextAttemptAt: string; // ISO-8601 UTC
  createdAt: string; // ISO-8601 UTC
  lastErrorCode?: string;
  correlationId: CorrelationId;
}

export interface TransferCursor {
  contentRef: ContentRef;
  receivedBytes: number;
  totalBytes?: number;
  etag?: string;
  checksum?: string;
  updatedAt: string; // ISO-8601 UTC
}
```

---

## Download Orchestration Interface

```ts
export interface OfflineContentDownloadPort {
  /** Begin or continue acquisition of entitled learning content for offline availability. */
  requestDownload(input: DownloadRequest): Promise<{
    accepted: boolean;
    queuedContentRefs: ContentRef[];
    rejectedContentRefs: Array<{ contentRef: ContentRef; reason: string }>;
    acceptedAt: string;
  }>;

  /** Read resumable transfer cursor for a specific content reference. */
  getTransferCursor(input: {
    tenantId: TenantId;
    learnerId: LearnerId;
    contentRef: ContentRef;
  }): Promise<TransferCursor | undefined>;
}
```

Input:
- `DownloadRequest` with learner/content scope and correlation metadata.

Output:
- Acceptance status, queued/rejected content references, and transfer cursor access for resume semantics.

---

## Sync Queue Interface

```ts
export interface OfflineSyncQueuePort {
  enqueue(items: SyncQueueItem[]): Promise<{
    acceptedIds: SyncItemId[];
    deduplicatedIds: SyncItemId[];
    rejected: Array<{ syncItemId: SyncItemId; reason: string }>;
  }>;

  leaseBatch(input: {
    maxItems: number;
    now: string; // ISO-8601 UTC
  }): Promise<SyncQueueItem[]>;

  acknowledge(input: {
    syncItemId: SyncItemId;
    processedAt: string;
  }): Promise<void>;

  reschedule(input: {
    syncItemId: SyncItemId;
    errorCode: string;
    nextAttemptAt: string;
  }): Promise<void>;
}
```

Behavioral requirements:
- Idempotent enqueue using `syncItemId` and `correlationId`.
- Deterministic leasing order (`nextAttemptAt`, then `createdAt`).
- Retry/backoff represented via `reschedule`; no transport-specific assumptions.

---

## Resume Sync & Connectivity Adaptation Interface

```ts
export interface OfflineSyncResumePort {
  /** Trigger resume workflow when connectivity improves or app foregrounds. */
  resume(input: {
    tenantId: TenantId;
    learnerId: LearnerId;
    network: NetworkSnapshot;
    resumedAt: string;
  }): Promise<{
    resumed: boolean;
    scheduledSyncItems: number;
    resumedTransfers: number;
    deferredReason?: string;
  }>;

  /** Read sync health for diagnostics/recovery UIs. */
  getRecoveryState(input: {
    tenantId: TenantId;
    learnerId: LearnerId;
  }): Promise<{
    pendingItems: number;
    blockedItems: number;
    inFlightTransfers: number;
    lastSuccessfulSyncAt?: string;
    lastFailureCode?: string;
  }>;
}
```

Unstable connectivity support:
- `resume` must be safe to call repeatedly and concurrently.
- degraded network may schedule only lightweight operations while deferring large transfers.
- partial transfers continue from `TransferCursor.receivedBytes` when server supports ranges.

---

## Learning System Integration Port (Boundary Adapter)

```ts
export interface LearningSystemSyncAdapter {
  /** Pull authoritative enrollment/content entitlements from learning system. */
  fetchSyncContext(input: {
    tenantId: TenantId;
    learnerId: LearnerId;
    enrollmentId: EnrollmentId;
  }): Promise<{
    enrollmentState: "active" | "paused" | "completed" | "revoked";
    entitledContentRefs: ContentRef[];
    learningRevision?: string;
  }>;

  /** Push reconciled learner activity to learning system without embedding core rules here. */
  pushReconciledActivity(input: {
    tenantId: TenantId;
    learnerId: LearnerId;
    enrollmentId: EnrollmentId;
    items: Array<{
      syncItemId: SyncItemId;
      operation: SyncOperation;
      payload: Record<string, unknown>;
      occurredAt: string;
      correlationId: CorrelationId;
    }>;
  }): Promise<{
    accepted: SyncItemId[];
    rejected: Array<{ syncItemId: SyncItemId; reason: string }>;
    processedAt: string;
  }>;
}
```

Boundary rule:
- This adapter is the only integration point with the learning system.
- The offline sync contract does not interpret pedagogical correctness; it transports and reconciles events.

---

## Example Sync Flow (Failure-Recovery + Resume)

1. Learner selects modules for offline access.
2. Client calls `OfflineContentDownloadPort.requestDownload(...)`.
3. Offline sync service validates entitlement via `LearningSystemSyncAdapter.fetchSyncContext(...)` and accepts allowed `contentRef`s.
4. Download worker starts transfer; periodically persists transfer cursor via the download port.
5. While offline, learner progress events are converted into `SyncQueueItem`s and `enqueue(...)` is called.
6. Network drops repeatedly (`degraded`/`offline`); worker calls `reschedule(...)` with backoff for failed queue items.
7. App reconnects with unstable network; orchestrator calls `resume(...)`.
8. `resume(...)` leases retry-eligible items, resumes range-supported downloads from transfer cursor, and defers heavy items if bandwidth is too low.
9. Successful sync items are sent through `LearningSystemSyncAdapter.pushReconciledActivity(...)`.
10. Accepted items are `acknowledge(...)`d; rejected items remain recoverable with explicit error codes and next retry times.

Outcome guarantees:
- No learning-core logic embedded.
- No storage engine assumptions.
- Modular ports allow independent replacement/testing.
- Recovery is deterministic across app restarts and connectivity oscillations.

---

## Reuse Guarantees
- Works across mobile, desktop, kiosk, and edge clients by keeping network/storage concerns abstract.
- Supports intermittent connectivity through resumable transfer cursor + explicit queue retry controls.
- Integrates with any learning platform exposing equivalent entitlement/activity adapter methods.
- Remains delivery-system agnostic by excluding playback concerns.
