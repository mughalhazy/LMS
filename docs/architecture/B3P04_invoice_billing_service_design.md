# B3P04 — Invoice & Billing Service Design

## 1) Purpose

The **Invoice & Billing Service** is responsible for creating financial obligations (invoices), maintaining billing records, and orchestrating subscription billing cycles.

It explicitly **does not execute payments**. Payment authorization/capture/refund remain in the Payment Execution domain.

---

## 2) Scope

### In scope
- Invoice generation
- Billing records management
- Subscription billing orchestration
- One-time invoice support
- Recurring billing support
- Audit trail for all billing state changes

### Out of scope
- Payment method tokenization
- Payment gateway interactions
- Payment capture/settlement/refund processing
- Usage event production/aggregation logic

---

## 3) Service boundary and integrations

## 3.1 Domain ownership
- **Invoice & Billing Service owns:**
  - Billing account profile (commercial terms snapshot)
  - Invoice aggregate and lifecycle state
  - Billing cycle run state
  - Billing ledger entries (debit/credit adjustments at billing-document level)
  - Billing audit events
- **Usage Metering Service owns:**
  - Usage event ingestion, normalization, aggregation, rating inputs
  - Billable usage summaries delivered to billing (read contract/event)
- **Checkout Service owns:**
  - Purchase intent, cart/offer acceptance, one-time order context
  - Checkout completion signal with commercial payload
- **Payment Execution domain owns:**
  - Collection and settlement of funds

## 3.2 Required integrations
1. **Usage Metering integration**
   - Billing consumes `usage.billing_window.closed.v1` (or equivalent API) containing rated/ratable usage totals for a period.
   - Billing never recomputes raw usage; it only transforms metered totals into invoice lines.

2. **Checkout integration**
   - Billing consumes `checkout.order.completed.v1` for one-time purchases and subscription activations/upgrades.
   - Billing creates draft invoice(s) or scheduled billing obligations from checkout payload.

---

## 4) Functional requirements mapping

- **Recurring billing:** billing cycle scheduler generates period invoices from subscription plans + metered usage summary.
- **One-time invoices:** created from checkout-completed order context.
- **Auditable:** immutable audit log entries on every lifecycle transition and financial adjustment.
- **No overlap with payment execution:** billing emits `invoice.issued` and expects payment outcome events; it does not call gateway PSP APIs.
- **No duplication with usage tracking:** billing only consumes rated/aggregated usage outputs.

---

## 5) Core data model

## 5.1 Aggregates

1. **BillingAccount**
   - `billing_account_id`
   - `tenant_id`, `customer_id`
   - `billing_timezone`, `currency`
   - `invoice_delivery_preferences`
   - `tax_profile_snapshot_ref`
   - `status`

2. **SubscriptionContract** (billing view)
   - `subscription_id`
   - `billing_account_id`
   - `plan_id`, `price_book_version`
   - `billing_period` (monthly/annual/custom)
   - `next_billing_at`
   - `proration_policy`
   - `status`

3. **Invoice**
   - `invoice_id`, `invoice_number`
   - `billing_account_id`, `subscription_id?`, `checkout_order_id?`
   - `invoice_type` (`recurring`, `one_time`, `adjustment`, `credit_note`)
   - `period_start`, `period_end`
   - `currency`
   - `subtotal`, `tax_total`, `discount_total`, `grand_total`
   - `state` (see lifecycle)
   - `due_at`, `issued_at`, `voided_at`
   - `version` (optimistic locking)

4. **InvoiceLine**
   - `invoice_line_id`, `invoice_id`
   - `line_type` (`subscription_fee`, `usage`, `one_time_item`, `tax`, `discount`, `adjustment`)
   - `source_ref` (usage summary id / checkout line id / manual adjustment id)
   - `quantity`, `unit_price`, `amount`
   - `metadata` (plan tier, usage window ref)

5. **BillingRecord**
   - Immutable, append-only financial record for all invoice-affecting actions.
   - `record_type` (`invoice_created`, `invoice_issued`, `credit_applied`, `invoice_voided`, etc.)
   - `recorded_at`, `actor_type`, `actor_id`, `correlation_id`, `payload_hash`

6. **AuditTrailEntry**
   - `audit_id`, `entity_type`, `entity_id`, `action`, `before`, `after`
   - `performed_by`, `performed_at`, `reason`, `request_id`
   - WORM retention policy

---

## 6) Invoice lifecycle (clear state machine)

`draft -> validated -> issued -> (paid | partially_paid | overdue | voided)`

Additional branches:
- `issued -> disputed`
- `disputed -> issued` (resolved)
- `issued/overdue -> written_off`
- `paid -> refunded_partial/refunded_full` (status reflected from payment domain events)

### State ownership notes
- Billing service controls: `draft`, `validated`, `issued`, `voided`, `overdue`, `written_off`.
- Payment outcome states (`paid`, `partially_paid`, `refunded_*`) are **derived from payment events**, not from billing attempting payment execution.

### Transition guards
- `draft -> validated`: all required invoice fields present; totals reconcile.
- `validated -> issued`: idempotency check passed; immutable invoice number assigned.
- `issued -> voided`: only if no successful settlement linked.
- `issued -> overdue`: due date passed and no full settlement event.

---

## 7) Billing flow

## 7.1 Recurring billing flow
1. Scheduler selects due subscriptions (`next_billing_at <= now`).
2. Billing requests/consumes metering window summary for `period_start..period_end`.
3. Billing composes draft invoice (subscription base fee + usage lines + tax/discount policies).
4. Validation and total reconciliation.
5. Invoice issued; event `invoice.issued.v1` published.
6. Payment domain attempts collection (outside billing boundary).
7. Billing consumes payment result events:
   - `payment.settled` => invoice `paid`/`partially_paid`
   - `payment.failed` => invoice remains `issued`; retry policy handled by collections strategy
8. If due date exceeded without full settlement => `overdue`.

## 7.2 One-time billing flow
1. Checkout completes order and emits `checkout.order.completed.v1`.
2. Billing creates one-time draft invoice from order lines.
3. Billing validates and issues invoice.
4. Payment domain processes according to checkout contract.
5. Billing updates invoice state from payment outcome events.

## 7.3 Adjustments and credit notes
1. Authorized actor creates adjustment request.
2. Billing creates linked adjustment invoice or credit note.
3. Audit entry includes reason, actor, ticket/reference id.
4. New billing records appended; original invoice remains immutable except status fields.

---

## 8) API and events (logical contract)

## 8.1 Synchronous APIs
- `POST /billing-accounts`
- `GET /billing-accounts/{id}`
- `POST /invoices:generate` (internal orchestration)
- `GET /invoices/{invoice_id}`
- `POST /invoices/{invoice_id}/issue`
- `POST /invoices/{invoice_id}/void`
- `POST /invoices/{invoice_id}/adjust`
- `GET /billing-records?billing_account_id=...`
- `GET /audit-trail?entity_type=invoice&entity_id=...`

## 8.2 Published events
- `invoice.draft.created.v1`
- `invoice.issued.v1`
- `invoice.overdue.v1`
- `invoice.voided.v1`
- `invoice.adjusted.v1`
- `billing.cycle.completed.v1`

## 8.3 Consumed events
- `usage.billing_window.closed.v1` (from Usage Metering)
- `checkout.order.completed.v1` (from Checkout)
- `payment.settled.v1`, `payment.failed.v1`, `payment.refunded.v1` (from Payment Execution)

---

## 9) Auditability and compliance

- **Append-only billing records** for financial traceability.
- **Entity audit trail** with before/after snapshots for every state transition.
- **Correlation IDs** propagated across checkout, usage metering, billing, and payment domains.
- **Immutable invoice numbering** once issued.
- **No hard delete** for invoice/billing/audit entities; use tombstone/void semantics.
- Retention and legal hold controls for audit datasets.

---

## 10) Idempotency, consistency, and failure handling

- Idempotency keys on invoice generation (`subscription_id + period` or `checkout_order_id`).
- Outbox pattern for reliable event publication.
- Exactly-once effect at aggregate level via dedupe table + optimistic version checks.
- Replay-safe consumers for metering/checkout/payment events.
- Dead-letter queue and operator re-drive for poisoned messages.

---

## 11) Non-functional expectations

- Horizontal scale for cycle runs (partition by tenant + billing account).
- P95 invoice generation latency target defined per tenant size tier.
- Observability:
  - Metrics: invoice generation rate, issue failures, overdue ratio, cycle duration.
  - Traces: end-to-end billing cycle correlation.
  - Logs: structured and audit-friendly.

---

## 12) QC checklist alignment (QC 10/10)

- **No overlap with payment execution:** payment processing is external; billing only reacts to payment outcomes.
- **No duplication with usage tracking:** usage metering remains source of truth for usage aggregation/rating inputs.
- **Audit trail support:** immutable billing records + audit trail entries for all lifecycle/adjustment actions.
- **Clear invoice lifecycle:** explicit state machine and guarded transitions.
- **Separation of billing vs payment:** bounded contexts and event-driven handshake.

