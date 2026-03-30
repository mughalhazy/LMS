# B1P06 — Communication Adapter Interface Contract

## Purpose
Define a channel-agnostic interface for outbound communication adapters that can:
- send a message now,
- schedule a message for later,
- broadcast to multiple recipients,
- and trigger workflow callbacks around message lifecycle events.

This contract is intentionally focused on **transport orchestration and adapter behavior only**.
It does **not** define notification policy, template governance, campaign strategy, or capability lifecycle metadata.

---

## Scope Boundaries (QC)
- **No overlap with notification logic:** this interface does not decide *who* should be notified, *when* business reminders happen, or template selection policy.
- **No duplication with capability definitions:** channel/provider metadata in capability registries remains external; this contract only defines runtime adapter behavior.
- **Channel-agnostic abstraction:** callers use one interface independent of WhatsApp/SMS implementation details.
- **Workflow trigger support required:** adapters emit/forward deterministic lifecycle events for orchestration systems.
- **Extensible by design:** new channels/providers can be added without changing caller contracts.
- **Clean separation of channel logic:** channel-specific payload normalization is isolated to concrete adapters.

---

## Core Types (TypeScript-style, implementation-agnostic)

```ts
export type ChannelType = "whatsapp" | "sms" | (string & {});
export type MessageId = string;
export type ScheduleId = string;
export type BroadcastId = string;
export type RecipientId = string;

/** Generic metadata that orchestration/observability systems can use. */
export interface MessageMetadata {
  tenantId: string;
  correlationId?: string;
  workflowRunId?: string;
  tags?: string[];
  attributes?: Record<string, string | number | boolean | null>;
}

/** Channel-agnostic message payload. Concrete adapters map this into provider-specific formats. */
export interface MessagePayload {
  body: string;
  subject?: string; // optional for channels that support it
  mediaUrls?: string[];
  templateRef?: string; // opaque; template ownership lives outside this interface
  variables?: Record<string, unknown>;
}

/** Single-recipient send request. */
export interface SendMessageRequest {
  channel: ChannelType;
  recipient: {
    id: RecipientId;
    address: string; // e.g., E.164 phone or WhatsApp identifier
    locale?: string;
  };
  payload: MessagePayload;
  metadata: MessageMetadata;
  idempotencyKey?: string;
}

/** Scheduled send request (single recipient). */
export interface ScheduleMessageRequest extends SendMessageRequest {
  sendAt: string; // ISO-8601 UTC
  timezone?: string; // optional display/intent timezone from caller
}

/** Broadcast request (fan-out to multiple recipients under one logical operation). */
export interface BroadcastRequest {
  channel: ChannelType;
  recipients: Array<{
    id: RecipientId;
    address: string;
    locale?: string;
  }>;
  payload: MessagePayload;
  metadata: MessageMetadata;
  idempotencyKey?: string;
  rateLimitPerSecond?: number;
}

export type DeliveryState =
  | "accepted"
  | "scheduled"
  | "queued"
  | "sent"
  | "delivered"
  | "failed"
  | "cancelled";

export interface AdapterResult {
  operationId: MessageId | ScheduleId | BroadcastId;
  channel: ChannelType;
  state: DeliveryState;
  acceptedAt: string; // ISO-8601 UTC
  providerRef?: string;
  errorCode?: string;
  errorMessage?: string;
}
```

---

## Workflow Trigger Contract

```ts
export type WorkflowTriggerType =
  | "communication.accepted"
  | "communication.scheduled"
  | "communication.sent"
  | "communication.delivered"
  | "communication.failed"
  | "communication.broadcast.completed";

export interface WorkflowTriggerEvent {
  triggerType: WorkflowTriggerType;
  occurredAt: string; // ISO-8601 UTC
  operationId: string;
  channel: ChannelType;
  tenantId: string;
  recipientId?: RecipientId;
  workflowRunId?: string;
  correlationId?: string;
  details?: Record<string, unknown>;
}

/** Adapter-injected workflow publisher (event bus, webhook, orchestrator callback, etc.). */
export interface WorkflowTriggerPublisher {
  publish(event: WorkflowTriggerEvent): Promise<void>;
}
```

---

## Communication Adapter Interface

```ts
/**
 * Channel-agnostic runtime contract for communication transports.
 * Concrete implementations include WhatsAppAdapter, SmsAdapter, and future channels.
 */
export interface CommunicationAdapter {
  /** Runtime-identifiable channel handled by this adapter implementation. */
  readonly channel: ChannelType;

  /** Immediate send (single recipient). */
  sendMessage(request: SendMessageRequest): Promise<AdapterResult>;

  /** Delayed send (single recipient). */
  scheduleMessage(request: ScheduleMessageRequest): Promise<AdapterResult>;

  /** Multi-recipient fan-out operation. */
  broadcast(request: BroadcastRequest): Promise<AdapterResult>;
}

/** Adapter registry/router so callers remain channel-agnostic. */
export interface CommunicationAdapterRegistry {
  register(adapter: CommunicationAdapter): void;
  resolve(channel: ChannelType): CommunicationAdapter | undefined;
  list(): CommunicationAdapter[];
}
```

---

## Required Channel Coverage

At minimum, implementations must provide:
- `WhatsAppAdapter` (`channel = "whatsapp"`)
- `SmsAdapter` (`channel = "sms"`)

Both adapters must implement the same `CommunicationAdapter` methods (`sendMessage`, `scheduleMessage`, `broadcast`) and publish workflow triggers through `WorkflowTriggerPublisher`.

---

## Example Adapter Usage

```ts
async function dispatchCommunication(
  registry: CommunicationAdapterRegistry,
  workflowPublisher: WorkflowTriggerPublisher,
) {
  // Channel-agnostic request from upstream workflow/service.
  const request: SendMessageRequest = {
    channel: "whatsapp",
    recipient: {
      id: "user_1001",
      address: "+15551234567",
      locale: "en-US",
    },
    payload: {
      body: "Your session starts in 30 minutes.",
      templateRef: "session_reminder_v1",
      variables: { minutes: 30 },
    },
    metadata: {
      tenantId: "tenant_acme_42",
      workflowRunId: "wf_run_9a31",
      correlationId: "corr_4f2a",
      tags: ["reminder", "session"],
    },
    idempotencyKey: "msg-tenant_acme_42-user_1001-2026-03-30T10:00Z",
  };

  const adapter = registry.resolve(request.channel);
  if (!adapter) throw new Error(`No communication adapter registered for channel: ${request.channel}`);

  const result = await adapter.sendMessage(request);

  // Workflow trigger emission remains generic and transport-independent.
  await workflowPublisher.publish({
    triggerType: result.state === "failed" ? "communication.failed" : "communication.sent",
    occurredAt: new Date().toISOString(),
    operationId: String(result.operationId),
    channel: result.channel,
    tenantId: request.metadata.tenantId,
    recipientId: request.recipient.id,
    workflowRunId: request.metadata.workflowRunId,
    correlationId: request.metadata.correlationId,
    details: {
      providerRef: result.providerRef,
      state: result.state,
    },
  });
}
```

---

## Extensibility Notes
- Add new channels (e.g., `push`, `email`, `voice`) by implementing `CommunicationAdapter` and registering them in `CommunicationAdapterRegistry`.
- Keep channel-specific mapping, retries, and provider constraints inside each adapter implementation.
- Preserve stable caller contract so workflow/orchestrator code remains unchanged as channels evolve.
- Extend `WorkflowTriggerType` only via additive events to keep backward compatibility.
