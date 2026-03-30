# B1P07 — Media Security Interface Contract

## Purpose
Define a reusable, implementation-agnostic interface for **secure media access authorization** and **playback security policy issuance**.

This contract is intentionally separated from:
- **Content service responsibilities** (asset ingest, metadata, transcoding, storage lifecycle).
- **Delivery layer responsibilities** (CDN routing, segment serving, edge cache behavior, transport protocols).

The interface focuses only on security decisions and artifacts required before secure playback can proceed.

---

## Scope Boundaries (QC)
- **No overlap with content service:** no APIs for upload, encoding profiles, manifests, or asset metadata authoring.
- **No delivery implementation coupling:** no CDN/session transport orchestration or stream segment delivery logic.
- **No implementation logic:** this document defines contract shape, required inputs/outputs, and deterministic decision semantics only.
- **Anti-piracy readiness required:** contract must support tokenized playback, watermark controls, and policy-violation signaling hooks.
- **Reusable across players/channels:** web, mobile, desktop, and partner-integrated players consume the same interface.

---

## Core Types

```ts
export type TenantId = string;
export type UserId = string;
export type SessionId = string;
export type AssetId = string;
export type EntitlementRef = string;
export type DeviceId = string;
export type PlaybackToken = string;

export type DeliveryChannel = "web" | "ios" | "android" | "desktop" | "partner";

export type SecurityDecision = "allow" | "deny" | "step_up";

export interface PlaybackContext {
  tenantId: TenantId;
  userId: UserId;
  assetId: AssetId;
  sessionId: SessionId;
  deviceId?: DeviceId;
  channel: DeliveryChannel;
  ipAddress?: string;
  userAgent?: string;

  /** Optional correlation id for end-to-end audit/event tracing. */
  correlationId?: string;
}
```

---

## Entitlement Integration Contract

```ts
/** Read-only integration boundary; entitlement system remains source of truth. */
export interface EntitlementVerifier {
  verifyMediaAccess(input: {
    tenantId: TenantId;
    userId: UserId;
    assetId: AssetId;
    sessionId: SessionId;
  }): Promise<{
    entitled: boolean;
    entitlementRef: EntitlementRef;
    reasonCode?: string; // e.g., "NO_ACTIVE_ENROLLMENT", "LICENSE_EXPIRED"
    evaluatedAt: string; // ISO-8601
  }>;
}
```

**Constraint:** Media security MUST consume this interface and MUST NOT embed commercial/enrollment business policy logic internally.

---

## Tokenized Playback Contract

```ts
export interface TokenPolicy {
  ttlSeconds: number;
  singleUse?: boolean;
  bindToDevice?: boolean;
  bindToIp?: boolean;
  maxConcurrentSessions?: number;
}

export interface PlaybackTokenRequest {
  context: PlaybackContext;
  tokenPolicy: TokenPolicy;
}

export interface PlaybackTokenGrant {
  token: PlaybackToken;
  issuedAt: string; // ISO-8601
  expiresAt: string; // ISO-8601
  claims: {
    tenantId: TenantId;
    userId: UserId;
    assetId: AssetId;
    sessionId: SessionId;
    entitlementRef: EntitlementRef;
  };
}
```

---

## Watermark Hook Contract

```ts
export interface WatermarkContext {
  tenantId: TenantId;
  userId: UserId;
  assetId: AssetId;
  sessionId: SessionId;
  playbackTokenHash: string;
}

export interface WatermarkHooks {
  /** Called before playback grant finalization to attach watermark directives. */
  onBeforePlaybackGrant(input: WatermarkContext): Promise<{
    watermarkRequired: boolean;
    watermarkProfileId?: string;
    forensicPayloadRef?: string;
  }>;

  /** Called when a watermark anomaly/piracy signal is detected downstream. */
  onWatermarkSignal(input: WatermarkContext & {
    signalType: "tamper_detected" | "redistribution_suspected" | "capture_risk";
    observedAt: string;
  }): Promise<void>;
}
```

---

## Anti-Piracy Event Hook Contract

```ts
export interface AntiPiracyHooks {
  onPolicyViolation(input: {
    tenantId: TenantId;
    userId: UserId;
    assetId: AssetId;
    sessionId: SessionId;
    violationType:
      | "token_replay"
      | "concurrency_exceeded"
      | "geo_violation"
      | "entitlement_revoked"
      | "watermark_mismatch";
    detectedAt: string;
    correlationId?: string;
  }): Promise<void>;
}
```

---

## Primary Media Security Interface

```ts
export interface MediaSecurityInterface {
  /**
   * Evaluate secure playback eligibility and, if approved, issue security artifacts.
   * No media bytes or manifest URLs are returned by this interface.
   */
  authorizePlayback(input: PlaybackTokenRequest): Promise<{
    decision: SecurityDecision;
    reasonCode?: string;
    entitlement: {
      entitled: boolean;
      entitlementRef?: EntitlementRef;
      evaluatedAt: string;
    };
    playbackToken?: PlaybackTokenGrant;
    watermark?: {
      watermarkRequired: boolean;
      watermarkProfileId?: string;
      forensicPayloadRef?: string;
    };
    securityControls: {
      tokenizedPlayback: true;
      antiPiracyMonitoringEnabled: boolean;
      watermarkHookEvaluated: boolean;
    };
  }>;
}
```

---

## Deterministic Decision Order
Given identical input and identical dependency snapshots, `authorizePlayback` follows this order:

1. Validate request envelope completeness and required identity fields.
2. Call `EntitlementVerifier.verifyMediaAccess`.
3. If not entitled, return `decision = deny` with no token grant.
4. Evaluate anti-piracy token policy constraints (TTL/concurrency/binding rules).
5. Invoke `WatermarkHooks.onBeforePlaybackGrant`.
6. Return allow/step_up with playback token + watermark directives.

This preserves stable, auditable security outcomes while keeping implementation choices external.

---

## Example Flow (Contract-Level)

1. Player requests secure playback authorization with tenant/user/session/asset context.
2. Media Security Interface verifies access through `EntitlementVerifier`.
3. If entitlement is valid, interface computes token policy outcome and requests watermark directives via hooks.
4. Interface returns:
   - `decision: allow`
   - short-lived `playbackToken`
   - watermark directives
   - anti-piracy control flags
5. Delivery layer separately consumes the token to perform actual stream delivery checks.
6. If replay/tamper/redistribution indicators appear later, `AntiPiracyHooks.onPolicyViolation` and/or `WatermarkHooks.onWatermarkSignal` are triggered.

---

## Responsibility Separation Summary
- **This interface:** secure access decision contract + token/watermark/anti-piracy hooks.
- **Entitlement system:** authoritative access rights decision source.
- **Content service:** media asset lifecycle and metadata ownership.
- **Delivery layer/CDN/player transport:** serving and transport of media content.

This separation ensures reusable anti-piracy security controls without coupling policy contracts to storage or delivery implementation details.
