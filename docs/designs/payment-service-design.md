# Payment Service Design

## 1) Purpose and Scope

Payment Service is the Pakistan-market payment orchestration layer for the LMS commerce domain. It routes inbound payment callbacks from local mobile-money providers (JazzCash, Easypaisa) to the platform's transaction record system and emits verified payment events for downstream order and invoice processing.

In scope:
- Provider callback receipt and normalization.
- Payment verification and event emission.
- Provider routing policy (tenant country code + payment method preference).

Out of scope:
- Checkout session lifecycle and order creation (owned by checkout-service).
- Invoice generation and billing state (owned by invoice-billing-service).
- Subscription and renewal triggers (owned by subscription-service).
- Provider SDK credential management.

This service is a **callback handler and event emitter**. It does not initiate payments — initiation is a planned route (see §6, BA-017).

---

## 2) Design Goals

1. **Provider-agnostic callback normalization**
   Payment callbacks from JazzCash and Easypaisa arrive with provider-specific field schemas; the service normalizes them to a canonical `PaymentVerifiedEvent` before downstream dispatch.

2. **No checkout / invoice ownership**
   Payment Service handles only the inbound provider interaction layer. Order state transitions and invoice settlement are driven by consumers of emitted events.

3. **Idempotent callback handling**
   Duplicate callbacks from the same provider for the same `payment_id` must not produce duplicate verified events or double-credit transactions.

4. **Separation of routing policy from handler logic**
   `build_pakistan_payment_router()` encapsulates provider selection rules. Adding a new Pakistan provider requires only router extension, not handler changes.

---

## 3) Providers Supported

| Provider | Type | Role |
|---|---|---|
| JazzCash | Mobile money | Primary — widest coverage |
| Easypaisa | Mobile money | Secondary — coverage complement |

Provider selection is driven by `build_pakistan_payment_router()` in `service.py`, which resolves the eligible provider based on tenant country code and payment method preference supplied in the checkout context.

Both providers follow an asynchronous callback model: the LMS initiates a payment request externally, and the provider POSTs a callback to `/api/v1/payments/callback/{provider}` on result.

---

## 4) Domain Model

### 4.1 PaymentCallbackRequest

| Field | Type | Notes |
|---|---|---|
| `payment_id` | string | Provider-assigned transaction reference; non-empty |
| `status` | string | Provider status string (e.g., `SUCCESS`, `FAILED`); non-empty |
| `provider` | string \| null | Provider name — overridden by path param `{provider}` |
| `user_id` | string \| null | Learner/buyer reference |
| `order_id` | string \| null | Platform order reference |
| `metadata` | dict | Provider-specific supplementary fields |

### 4.2 PaymentCallbackResponse

| Field | Type | Notes |
|---|---|---|
| `transaction_id` | string | Echoed from `payment_id` |
| `status` | string | Normalized status from verified event |
| `user_id` | string | Buyer reference |
| `order_id` | string \| null | Platform order reference |
| `verified` | boolean | True if provider callback was successfully verified |

### 4.3 PaymentVerifiedEvent (internal)

Emitted by `PaymentOrchestrationService` after successful callback handling. Consumed to update order state and trigger invoice/subscription flows downstream.

Key fields: `transaction_id`, `status`, `user_id`, `order_id`.

---

## 5) Architecture

### 5.1 Components

1. **Payment API** (`api.py`) — FastAPI application; single callback handler route.
2. **PaymentOrchestrationService** (`service.py`) — top-level coordinator; delegates to provider router.
3. **Pakistan Payment Router** (`build_pakistan_payment_router()`) — resolves provider, applies routing rules.
4. **Provider Adapters** (JazzCash / Easypaisa) — implement provider-specific callback parsing and verification; follow `payment-provider-adapter-contract.md`.
5. **Event Publisher** — emits `PaymentVerifiedEvent` after verification; consumed by order/invoice services.

### 5.2 Callback Flow

```
Provider (JazzCash / Easypaisa)
    │  POST /api/v1/payments/callback/{provider}
    ▼
Payment API
    │  parse PaymentCallbackRequest; override provider from path param
    ▼
PaymentOrchestrationService.handle_provider_callback(provider, payload)
    │  route to correct adapter via Pakistan Payment Router
    ▼
Provider Adapter
    │  verify signature, normalize fields, mark payment verified/failed
    ▼
PaymentOrchestrationService
    │  emit PaymentVerifiedEvent (in-memory publisher; production: event bus)
    ▼
Payment API
    │  retrieve emitted event for response assembly
    ▼
PaymentCallbackResponse → 200
```

---

## 6) API Surface

### 6.1 Implemented

`POST /api/v1/payments/callback/{provider}`

Path param `{provider}`: `jazzcash` | `easypaisa`

Request body: `PaymentCallbackRequest`

Response `200`: `PaymentCallbackResponse`

Errors:
- `404 payment_not_found` — no transaction matched the `payment_id`
- `500 payment_verified_event_not_emitted` — orchestrator processed but event not retrievable (internal fault)

### 6.2 Planned (BA-017 — pending R4 build)

`POST /api/v1/payments/initiate`

Initiates a payment request to the selected provider. Body to include: `order_id`, `user_id`, `amount`, `currency`, `payment_method`, `tenant_id`. Returns a `payment_id` and provider redirect/deeplink for the buyer to complete payment.

This route is absent from the current implementation and is a tracked gap (BA-017).

---

## 7) Failure Handling

| Failure | Handling |
|---|---|
| `payment_id` not found | `404` returned; no event emitted |
| Provider adapter verification failure | Adapter returns `None`; `404` returned |
| Event not found after processing | `500` returned; indicates internal orchestrator fault |
| Duplicate callback (same `payment_id`) | Idempotency is adapter-level responsibility per `payment-provider-adapter-contract.md` |

---

## 8) Integration Points

### 8.1 checkout-service

Checkout-service initiates payment intent and supplies `order_id` and buyer context to the provider. On callback receipt, payment-service echoes `order_id` back in the response for downstream correlation. Checkout-service (or an event consumer) updates `Order.status` on `PaymentVerifiedEvent`.

### 8.2 invoice-billing-service

Invoice settlement is triggered by consuming `PaymentVerifiedEvent`. Invoice-service is not called synchronously by payment-service.

### 8.3 payment-provider-adapter-contract

Provider adapters must implement the normalized interface defined in `docs/contracts/payment-provider-adapter-contract.md`. This contract specifies the `create` / `verify` / `refund` surface; payment-service uses the `verify` path on callback.

---

## 9) Observability

Key metrics to instrument:

- `payment_callback_requests_total{provider}` — inbound callback volume per provider
- `payment_callback_verified_total{provider}` — successful verifications
- `payment_callback_failed_total{provider, reason}` — failures by reason code
- `payment_callback_latency_ms{provider}` — end-to-end handler latency

---

## See also

- `docs/contracts/payment-provider-adapter-contract.md` — provider adapter contract
- `docs/designs/checkout-service-design.md` — upstream order/checkout flow
- `docs/designs/invoice-billing-service-design.md` — downstream invoice flow
- `docs/qc/payment-adapter-validation-report.md` — JazzCash / Easypaisa adapter validation
- `Repo/backend/services/payment-service/README.md` — service run reference
- `doc-catalogue.md` B5 — this doc is registered here
