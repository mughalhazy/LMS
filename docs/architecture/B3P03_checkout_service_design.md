# B3P03 — Checkout Service Design

## 1) Purpose and Scope

Checkout Service converts a buyer's purchase intent into a committed order and triggers payment initiation through a provider-agnostic payment interface.

In scope:
- Checkout session lifecycle.
- Order creation from validated checkout intents.
- Payment initiation request dispatch via payment adapter contract.

Out of scope:
- Provider-specific payment behavior (SDK workflows, API quirks, field mapping internals).
- Invoice lifecycle/state transitions and invoice calculations.
- Tax/discount/rating rules owned by billing/invoice services.

This design enforces **stateless service nodes** with all durable state externalized to databases/event streams.

---

## 2) Design Goals

1. **Clear checkout vs payment separation**
   - Checkout owns intent/session/order orchestration.
   - Payment Adapter layer owns provider execution details.

2. **No overlap with Invoice Service**
   - Checkout does not create, mutate, or settle invoices.
   - Checkout emits order/payment-intent events consumed by downstream billing/invoice services.

3. **Stateless runtime architecture**
   - API workers keep no in-memory workflow state.
   - Every step is reconstructible from persisted records and events.

4. **Clean retry model**
   - Idempotent commands for session submission, order creation, payment initiation.
   - Deterministic outcomes for duplicate requests and at-least-once event delivery.

5. **Resilient failure handling**
   - Distinguish retryable vs terminal failures.
   - Dead-letter and operator recovery paths without double-charging or duplicate orders.

---

## 3) Integrations

### 3.1 Catalog Integration (required)

Checkout calls Catalog for:
- SKU/product existence and sellability.
- Price reference snapshot lookup (pricebook/version references only).
- Quantity constraints, availability flags, purchase policy validation.

Checkout persists a **catalog snapshot reference** (not full catalog ownership) with each session/order to ensure consistent replay/audit.

### 3.2 Payment Adapter Interface Integration (required)

Checkout invokes a commerce payment gateway/adapter contract to initiate payment intent using normalized commands:
- `request_id` (idempotency key)
- `order_id`
- `customer_id`
- `amount_minor`, `currency`
- `payment_method_type`
- contextual metadata

Checkout does **not** embed any provider logic. Provider selection/routing is delegated to the payment adapter router layer.

### 3.3 Multi-provider Support

Checkout is provider-agnostic by design:
- It passes payment context and desired method.
- Router resolves eligible provider(s) externally.
- Checkout stores normalized `payment_intent_id` and abstract payment status only.

---

## 4) Domain Model and Ownership

### 4.1 Checkout-owned aggregates

1. `CheckoutSession`
   - `session_id`
   - `tenant_id`
   - `customer_id`
   - `status` (`open`, `submitted`, `expired`, `failed_validation`)
   - `line_items[]` (SKU refs, qty, captured display price refs)
   - `currency`, totals snapshot
   - `catalog_snapshot_ref`
   - `expires_at`
   - `idempotency_key_last_submit`

2. `Order`
   - `order_id`
   - `tenant_id`, `customer_id`
   - `source_session_id`
   - `status` (`created`, `pending_payment`, `payment_initiated`, `payment_failed`, `completed`, `cancelled`)
   - commercial amounts/currency snapshot
   - immutable order lines

3. `CheckoutPaymentAttempt` (or payment-initiation record)
   - `attempt_id`
   - `order_id`
   - `request_id` (idempotency)
   - `attempt_no`
   - `status` (`requested`, `accepted`, `retryable_failure`, `terminal_failure`)
   - normalized adapter error fields (`code`, `retryable`)

### 4.2 Explicit non-ownership

Checkout does not own:
- `Invoice`, `InvoiceLine`, invoice numbering, invoice state machine.
- Payment provider transaction internals or credentials.
- Accounting ledger behavior.

---

## 5) Stateless Service Architecture

## 5.1 Components

1. **Checkout API (stateless)**
   - CRUD/submit endpoints for checkout session.

2. **Checkout Application Service (stateless)**
   - Validates commands, applies idempotency policy, orchestrates persistence/events.

3. **Order Repository (state store)**
   - Durable storage for sessions/orders/payment attempts.

4. **Outbox Publisher**
   - Transactionally emits events/commands after DB commit.

5. **Payment Initiation Worker (stateless)**
   - Consumes `checkout.payment_initiation.requested` and calls payment adapter interface.

6. **Saga/Process Manager state (persisted)**
   - Stored in DB/event log; no in-memory orchestration dependency.

### 5.2 Statelessness enforcement rules

- No sticky sessions.
- No in-memory locks as source of truth.
- Concurrency controlled via DB constraints/version columns.
- Every command requires idempotency key; dedupe persisted.

---

## 6) API/Command Surface (conceptual)

### 6.1 Checkout APIs

- `POST /checkout/sessions`
- `PATCH /checkout/sessions/{session_id}/items`
- `POST /checkout/sessions/{session_id}/submit`

Submit request includes:
- `idempotency_key`
- selected payment method type + customer payment context reference
- optional return/callback context

### 6.2 Internal commands/events

Commands:
- `CreateOrderFromSession`
- `InitiatePaymentForOrder`

Events:
- `checkout.session.submitted.v1`
- `checkout.order.created.v1`
- `checkout.payment_initiation.requested.v1`
- `checkout.payment_initiation.accepted.v1`
- `checkout.payment_initiation.failed.v1`

Invoice service consumes order events and handles invoice generation independently.

---

## 7) Checkout Flow

1. Client creates/updates checkout session.
2. On submit, Checkout validates session completeness and freshness.
3. Checkout calls Catalog for final validation/snapshot references.
4. Checkout atomically:
   - marks session submitted,
   - creates `Order`,
   - writes outbox event `checkout.payment_initiation.requested.v1`.
5. Payment initiation worker consumes event and calls payment adapter interface with idempotent `request_id`.
6. On adapter success:
   - persist `CheckoutPaymentAttempt=accepted`,
   - set `Order.status=payment_initiated`,
   - emit `checkout.payment_initiation.accepted.v1`.
7. On adapter failure:
   - classify retryable vs terminal,
   - persist attempt status,
   - emit failure event for retry pipeline or terminal handling.

---

## 8) Failure Handling and Retry Model

### 8.1 Failure categories

1. **Validation failure (pre-order)**
   - Missing/invalid items, catalog mismatch, expired session.
   - No order created.

2. **Order creation failure**
   - DB conflict/transient storage issue.
   - Retry command with same idempotency key; return existing order if already created.

3. **Payment initiation retryable failure**
   - timeout, provider unavailable, network transient.
   - Send to retry schedule with bounded exponential backoff.

4. **Payment initiation terminal failure**
   - unsupported method, hard decline, invalid request.
   - Mark order as `payment_failed`; no auto retry.

### 8.2 Clean retries (QC)

- **Client submit retries:** deduped by `idempotency_key + tenant_id + session_id`.
- **Order creation retries:** unique constraint on `source_session_id` prevents duplicates.
- **Payment initiation retries:** unique `request_id` per logical attempt prevents duplicate intent creation.
- **Consumer retries:** at-least-once safe because handlers are idempotent and state-transition guarded.
- **Poison messages:** DLQ after max attempts with replay tooling.

### 8.3 State transition guards

- `open -> submitted` only once.
- `Order.created -> pending_payment/payment_initiated/payment_failed` allowed per state machine.
- Prevent `payment_initiated` from regressing to `created`.

---

## 9) Data and Consistency Strategy

- Use local ACID transaction for session submit + order write + outbox insert.
- Outbox relays commands/events to bus (exactly-once effect at business level via idempotency).
- Eventual consistency accepted between checkout and downstream invoice/payment-read models.

---

## 10) Sequence (Logical)

```text
Client -> Checkout API: SubmitSession(session_id, idempotency_key, payment_context)
Checkout API -> Catalog: ValidateItemsAndPrices(snapshot)
Catalog --> Checkout API: ValidationResult + snapshot_ref
Checkout API -> Checkout DB: Tx{mark submitted, create order, insert outbox}
Checkout API --> Client: 202 Accepted + order_id

Outbox Relay -> Event Bus: checkout.payment_initiation.requested.v1
Payment Worker -> Payment Adapter Gateway: CreatePayment(request_id, order_id, amount...)
Payment Adapter Gateway --> Payment Worker: accepted | failed(retryable|terminal)
Payment Worker -> Checkout DB: persist attempt + order status update
Payment Worker -> Event Bus: checkout.payment_initiation.accepted|failed.v1
```

---

## 11) QC Guardrails (10/10)

1. **No payment provider logic**
   - Provider specifics stay inside adapter implementations only.

2. **No duplication with invoice service**
   - Checkout emits order/payment-initiation events; invoice materialization remains external.

3. **Retries handled cleanly**
   - End-to-end idempotency keys, transition guards, retry classification, DLQ.

4. **Clear separation of checkout vs payment**
   - Checkout orchestrates commercial intent/order lifecycle.
   - Payment adapter layer executes provider interactions.

5. **Stateless architecture enforced**
   - Runtime nodes are stateless; persistence and event logs are sole source of truth.

---

## 12) Observability and Operations

Key metrics:
- `checkout_submit_requests_total`
- `checkout_submit_idempotent_replay_total`
- `checkout_order_create_latency_ms`
- `payment_initiation_success_total`
- `payment_initiation_retryable_failure_total`
- `payment_initiation_terminal_failure_total`
- `payment_initiation_retry_attempts_histogram`
- `checkout_outbox_lag_seconds`

Operational controls:
- Replay by `order_id` / `request_id`.
- Manual retry endpoint gated by role and state checks.
- Structured audit logs with tenant/order/session correlation IDs.
