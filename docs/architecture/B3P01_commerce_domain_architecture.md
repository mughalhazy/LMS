# B3P01 — Commerce Domain Architecture

## 1) Purpose and scope

This document defines the **commerce domain architecture** for LMS monetization. It covers:

- Product/catalog
- Pricing
- Checkout
- Invoices
- Subscriptions
- Revenue tracking

It is designed to support:

- One-time payments
- Recurring subscriptions
- Bundles
- Add-on monetization

And must integrate with:

- Entitlement system
- Usage metering
- Payment adapters (future)

---

## 2) Domain boundaries and non-overlap rules

### 2.1 Commerce domain responsibilities (owned here)

The commerce domain owns **commercial intent and financial lifecycle logic**:

- What can be sold (SKUs, plans, bundles, add-ons)
- How items are priced (price books, rules, taxes, discounts)
- How orders are assembled and validated
- How invoiceable obligations are generated
- How subscriptions evolve over time (create/renew/change/cancel)
- How recognized/forecast revenue is tracked at domain level

### 2.2 Explicitly out of scope (owned elsewhere)

To enforce **no overlap with payment adapter layer**:

- Payment network/protocol integrations (card rails, wallets, bank APIs)
- Payment tokenization and authorization workflows
- Fraud tooling specific to payment instruments
- Payment provider failover routing
- PCI-sensitive processor-side logic

Those concerns belong to the payment adapter layer and are consumed through stable contracts.

### 2.3 Billing logic single-source-of-truth rule

To enforce **no duplication of billing logic**:

- All billing state transitions originate in `Subscription Billing Orchestrator` and `Invoice Engine`.
- Checkout performs **pre-billing validation only** (not recurring billing calculations).
- Revenue Tracking performs **read-model derivation only** (no invoice mutation).
- Entitlement system performs access control only; it does not compute charges.

---

## 3) Commerce domain architecture (logical view)

```text
                                +----------------------------+
                                |      Entitlement System    |
                                | (grant/revoke/access eval) |
                                +-------------^--------------+
                                              |
                                              | entitlement events / commands
                                              |
+----------------------+     +----------------+-----------------+     +---------------------------+
|  Product Catalog     |---->|  Commerce Orchestration Layer    |---->|  Usage Metering System    |
|  (sellable entities) |     |  (checkout/subscription/invoice) |<----| (usage records/ratings in)|
+----------+-----------+     +----------------+-----------------+     +-------------+-------------+
           |                                  |                                     |
           v                                  v                                     |
+----------------------+           +----------------------+                           |
|   Pricing Engine     |           |   Invoice Engine     |---------------------------+
| (price books/rules)  |           | (invoice lifecycle)  |
+----------+-----------+           +-----------+----------+
           |                                   |
           v                                   v
+----------------------+           +----------------------+
|   Checkout Service   |---------->| Subscription Billing |
| (order intent/cart)  |           |   Orchestrator       |
+----------+-----------+           +-----------+----------+
           |                                   |
           +-------------------+---------------+
                               v
                    +--------------------------+
                    | Revenue Tracking Module  |
                    | (ledger/read models/KPIs)|
                    +------------+-------------+
                                 |
                                 v
                    +--------------------------+
                    | Payment Adapter Contract |
                    | (future integration seam)|
                    +--------------------------+
```

---

## 4) Sub-module breakdown

## 4.1 Product Catalog Module

**Responsibility**

- Manage sellable entities and commercial composition.

**Core aggregates**

- `Product`
- `Plan` (subscription plan)
- `Bundle` (set of products/plans/add-ons)
- `AddOn`
- `CatalogVersion`

**Key capabilities**

- SKU lifecycle (draft, active, retired)
- Bundle composition rules
- Add-on compatibility matrix
- Tenant/region catalog targeting

**Publishes**

- `catalog.product.published`
- `catalog.bundle.updated`

**Consumes**

- none required for core lifecycle

---

## 4.2 Pricing Module

**Responsibility**

- Produce deterministic, auditable charge outcomes from catalog + context.

**Core aggregates**

- `PriceBook`
- `PriceRule`
- `DiscountPolicy`
- `TaxProfile`
- `RatedLineItem`

**Key capabilities**

- One-time vs recurring rating
- Bundle pricing strategies (fixed bundle, component sum, mixed)
- Add-on rating (flat, tiered, per-seat, per-usage)
- Proration policy generation for plan changes
- Currency and region-aware pricing

**Publishes**

- `pricing.quote.generated`
- `pricing.rule.changed`

**Consumes**

- `catalog.*` events
- usage rating inputs from metering for usage-based add-ons

---

## 4.3 Checkout Module

**Responsibility**

- Convert buyer intent into a committed commercial order.

**Core aggregates**

- `Cart`
- `CheckoutSession`
- `Order`
- `OrderLine`

**Key capabilities**

- Cart assembly for products, subscriptions, bundles, add-ons
- Quote lock and price snapshotting
- Idempotent order submission
- Pre-commit validations (catalog validity, pricing validity, entitlement conflicts)

**Publishes**

- `checkout.order.submitted`
- `checkout.order.confirmed`

**Consumes**

- `pricing.quote.generated`
- entitlement eligibility checks

> Note: checkout does not execute payment processing internals; it issues an abstract payment intent command through the payment contract.

---

## 4.4 Invoice Engine Module

**Responsibility**

- Produce and manage invoice lifecycle for all billable obligations.

**Core aggregates**

- `Invoice`
- `InvoiceLine`
- `CreditMemo`
- `BillingCycle`

**Key capabilities**

- Draft/finalized/void invoice state machine
- Tax and discount materialization at invoice line level
- Consolidation of one-time and recurring charges
- Credit note generation and reversal handling

**Publishes**

- `invoice.issued`
- `invoice.adjusted`
- `invoice.settled`

**Consumes**

- `checkout.order.confirmed`
- subscription cycle events
- usage charge records from metering integration

---

## 4.5 Subscription Billing Orchestrator Module

**Responsibility**

- Own subscription commercial lifecycle and recurring billing decisions.

**Core aggregates**

- `Subscription`
- `SubscriptionItem`
- `Amendment`
- `RenewalSchedule`

**Key capabilities**

- Start/pause/resume/cancel subscriptions
- Mid-cycle upgrades/downgrades with proration
- Add/remove recurring add-ons
- Renewal and retry policy state
- Entitlement grant/revoke triggers based on subscription state

**Publishes**

- `subscription.activated`
- `subscription.changed`
- `subscription.renewed`
- `subscription.canceled`

**Consumes**

- `checkout.order.confirmed`
- `invoice.settled`
- metered usage rating outputs where applicable

---

## 4.6 Revenue Tracking Module

**Responsibility**

- Provide financial read models and metrics without mutating billing truth.

**Core aggregates/read models**

- `RevenueLedgerEntry`
- `MRRSnapshot`
- `ARRSnapshot`
- `DeferredRevenueSchedule`
- `MonetizationAttribution`

**Key capabilities**

- Event-sourced revenue projection from invoices/subscriptions
- Recognized vs deferred revenue snapshots
- Bundle and add-on contribution analysis
- Net revenue retention and expansion tracking

**Publishes**

- `revenue.snapshot.generated`
- `revenue.anomaly.detected`

**Consumes**

- invoice, subscription, checkout, and entitlement events

---

## 4.7 Commerce Integration Facade (cross-module anti-corruption layer)

**Responsibility**

- Keep external integrations decoupled from module internals via canonical contracts.

**Contracts exposed**

- Entitlement contract
- Usage metering contract
- Payment adapter contract

**Rules**

- No external system calls internal module stores directly.
- Integration mappings are versioned and backward-compatible.

---

## 5) Interaction flows

## 5.1 One-time purchase flow

1. Catalog returns sellable SKU + add-ons.
2. Pricing returns deterministic quote.
3. Checkout validates and commits `Order`.
4. Invoice Engine emits invoice for order lines.
5. Payment contract command is emitted (adapter executes externally).
6. On settlement signal, Entitlement is granted.
7. Revenue Tracking records recognized/deferred entries.

## 5.2 Subscription signup flow

1. Buyer selects plan (+ optional add-ons/bundle options).
2. Pricing rates initial charge + recurring schedule.
3. Checkout confirms order and starts subscription intent.
4. Subscription Orchestrator activates subscription.
5. Invoice Engine issues initial invoice and cycle schedule.
6. Payment settlement event confirms activation continuity.
7. Entitlement grants plan/add-on capabilities.
8. Revenue Tracking updates MRR/ARR and deferred schedule.

## 5.3 Usage-based add-on monthly close flow

1. Usage Metering publishes rated usage summary for billing window.
2. Subscription Orchestrator associates usage to active subscription items.
3. Invoice Engine appends metered lines to cycle invoice.
4. Invoice is finalized and sent to payment contract.
5. Settlement and adjustments propagate to Revenue Tracking.

## 5.4 Bundle purchase with mixed one-time + recurring lines

1. Catalog resolves bundle composition into component lines.
2. Pricing computes mixed pricing (one-time + recurring components).
3. Checkout submits atomic order with line types preserved.
4. Invoice Engine splits into immediate and cycle-linked invoice obligations.
5. Subscription Orchestrator manages only recurring component lifecycle.
6. Entitlement grants all bundle capabilities after settlement policy is met.

---

## 6) Canonical interfaces to required integrations

## 6.1 Entitlement integration

**Outbound commands**

- `GrantEntitlement(subject, capability, sourceOrderLine, effectiveWindow)`
- `RevokeEntitlement(subject, capability, reason, effectiveAt)`

**Inbound signals**

- `EntitlementGrantApplied`
- `EntitlementRevokeApplied`

**Boundary guarantee**

- Commerce decides *when/why* entitlement changes happen; entitlement system decides *how* access enforcement is executed.

## 6.2 Usage metering integration

**Inbound data**

- `RatedUsageWindow(subscriptionId, addOnId, quantity, unitPrice, windowStart, windowEnd)`

**Boundary guarantee**

- Metering owns raw usage ingestion/aggregation/rating inputs.
- Commerce owns invoice materialization and subscription impact.

## 6.3 Payment adapter integration (future)

**Outbound commands**

- `CreatePaymentIntent(invoiceId, amount, currency, customerRef, paymentContext)`
- `CapturePayment(paymentIntentId)`
- `RefundPayment(paymentRef, amount, reason)`

**Inbound signals**

- `PaymentAuthorized`
- `PaymentCaptured`
- `PaymentFailed`
- `PaymentRefunded`

**Boundary guarantee**

- Commerce never embeds processor-specific logic.
- Adapter layer never recalculates pricing, invoicing, or subscription rules.

---

## 7) Extensibility model

- **Modular contracts first**: each module exposes API + domain events, hides storage schema.
- **Strategy slots**:
  - Pricing strategies (bundle and add-on schemes)
  - Subscription proration policies
  - Invoice rendering/tax plugins
- **Versioned events** for safe evolution.
- **Feature flags** for staged rollout (e.g., usage-based add-ons by tenant).
- **Tenant isolation compatibility** through tenant-scoped identifiers in all aggregates.

---

## 8) QC conformance checklist (QC FIX RE QC 10/10)

### 8.1 No overlap with payment adapter layer

- Enforced by explicit out-of-scope list and canonical payment contract boundary.

### 8.2 No duplication of billing logic

- Billing state machine centralized in Subscription Billing Orchestrator + Invoice Engine.
- Other modules consume outcomes, do not recompute charges.

### 8.3 Domain-complete

- Includes product/catalog, pricing, checkout, invoices, subscriptions, revenue tracking.
- Includes required monetization modes: one-time, subscriptions, bundles, add-ons.

### 8.4 Clear module boundaries

- Defined per module with responsibilities, aggregates, events, and consumption contracts.

### 8.5 Supports add-on monetization

- Add-ons are first-class in catalog, pricing, checkout, subscription lifecycle, invoicing, and revenue attribution.

---

## 9) Recommended implementation sequencing

1. Catalog + Pricing foundational contracts.
2. Checkout with quote snapshot and order idempotency.
3. Invoice Engine + Subscription Orchestrator shared billing state machine.
4. Entitlement and usage metering integrations.
5. Revenue read models and finance dashboards.
6. Payment adapter integration activation (behind interface already defined).
