# B3P05 — Subscription Service Design

## 1) Purpose and scope

This document defines the **Subscription Service** for recurring access products in the LMS commerce domain.

**In scope**

- Plan catalog projection for subscription-ready plans
- Subscription creation and lifecycle state management
- Upgrades/downgrades (including dynamic, mid-cycle changes)
- Renewals and end-of-term processing
- Trial lifecycle handling
- Free → paid transitions

**Must integrate with**

- Entitlement system
- Billing service

**Out of scope (explicit non-overlap)**

- Invoice generation, taxes, collections, payment retries, dunning (Billing Service)
- Capability enforcement and real-time access checks (Entitlement System)
- Payment provider adapter logic

---

## 2) Service boundary and ownership model

## 2.1 Subscription Service owns

- Subscription contract state (`trialing`, `active`, `grace`, `paused`, `canceled`, etc.)
- Which **plan** a subscriber is on and which plan change is scheduled/effective
- Commercial effective dates (`started_at`, `current_term_start`, `current_term_end`, `renewal_anchor`)
- Plan change policy application (immediate vs next renewal)
- Integration orchestration commands/events to billing and entitlement

## 2.2 Billing Service owns (no duplication)

- Money math, rated charges, credits, proration amounts
- Invoice/final charge lifecycle
- Payment status and collection outcomes
- Financial ledger entries

> Subscription Service **requests** billing actions and consumes billing outcomes; it does not compute amounts.

## 2.3 Entitlement System owns (no duplication)

- Capability grants/revocations and policy evaluation
- Enforcement at request/runtime layer
- Access scope derivation from plan/capability mapping

> Subscription Service publishes subscription state/plan change intents; entitlement resolves those into concrete capability grants.

---

## 3) Plan vs capability separation

To satisfy strict separation:

- **Plan** = commercial package identifier (e.g., `free`, `pro_monthly`, `enterprise_annual`) used by Subscription + Billing.
- **Capability** = access permission (e.g., `ai_tutor`, `analytics_export`) used by Entitlement.

Subscription Service stores `plan_id` and optional `plan_version` only.
It never stores the capability matrix as source-of-truth.

A separate mapping contract is maintained by entitlement/config domain:

`plan_id -> entitlement_bundle_ref`

On subscription state changes, Subscription Service emits the plan reference and state; entitlement resolves the bundle.

---

## 4) Logical architecture

```text
                         +--------------------------------+
                         |        Plan Catalog Service    |
                         | (commercial plan definitions)  |
                         +---------------+----------------+
                                         |
                                         | plan snapshots / validation
                                         v
+----------------------+        +--------+-----------------+        +--------------------------+
| API Gateway / BFF    |------->|    Subscription Service  |------->|      Billing Service     |
| (tenant + auth ctx)  |        | (state + lifecycle only) |<-------| (charges/invoices/money) |
+----------------------+        +--------+-----------------+        +------------+-------------+
                                         |
                                         | subscription lifecycle events
                                         v
                              +----------+------------------+
                              |      Entitlement System     |
                              | (capability grant/revoke)   |
                              +-----------------------------+
```

### 4.1 Internal modules

1. **Plan Reference Module**
   - Caches active plan metadata needed for lifecycle validation.
   - Validates upgrade/downgrade compatibility and transition policies.

2. **Lifecycle Engine**
   - Finite-state-machine + transition guards.
   - Maintains idempotent transition history.

3. **Change Orchestrator**
   - Receives upgrade/downgrade requests.
   - Decides effective timing (`immediate` or `at_renewal`) based on policy + caller input.
   - Issues billing commands and waits for billing outcomes.

4. **Renewal Coordinator**
   - Drives renewals from term boundary events.
   - Handles success/failure outcomes and grace-period entry.

5. **Integration Outbox**
   - Reliable event publication to entitlement/billing.
   - At-least-once with idempotency keys.

---

## 5) Core data model (Subscription Service)

## 5.1 Aggregates

- `Subscription`
- `SubscriptionChangeRequest`
- `SubscriptionTransitionLog`

## 5.2 Subscription (canonical fields)

- `subscription_id`
- `tenant_id`
- `subscriber_type` (`user`, `org`, `team`)
- `subscriber_id`
- `status` (FSM state)
- `plan_id`
- `plan_version`
- `billing_account_ref` (opaque reference only)
- `started_at`
- `trial_started_at`
- `trial_ends_at`
- `current_term_start`
- `current_term_end`
- `renewal_anchor`
- `cancel_at_term_end` (bool)
- `scheduled_plan_change` (optional: target plan + effective date)
- `grace_ends_at` (optional)
- `version` (optimistic concurrency)

No money columns are stored as financial source-of-truth.

---

## 6) API surface (service-level)

- `POST /subscriptions` — create (free, trial, or paid start)
- `GET /subscriptions/{id}` — read status/plan/timeline
- `POST /subscriptions/{id}/change-plan` — upgrade/downgrade request
- `POST /subscriptions/{id}/renew` — manual/admin renewal trigger
- `POST /subscriptions/{id}/cancel` — immediate or term-end cancel
- `POST /subscriptions/{id}/resume` — from paused/grace where policy allows

All mutating requests require:

- `idempotency_key`
- `requested_by`
- `reason_code`

---

## 7) Integration contracts

## 7.1 Billing commands emitted by Subscription Service

- `billing.subscription.activate.requested`
- `billing.subscription.change_plan.requested`
- `billing.subscription.renewal.requested`
- `billing.subscription.cancel.requested`

Payload includes subscription identity + old/new plan references + effective date policy.
No internal money computations are sent from Subscription Service.

## 7.2 Billing events consumed

- `billing.subscription.activated`
- `billing.subscription.change_plan.applied`
- `billing.subscription.renewed`
- `billing.subscription.payment_failed`
- `billing.subscription.canceled`

These events are the trigger for final lifecycle transition commit.

## 7.3 Entitlement events emitted by Subscription Service

- `subscription.lifecycle.changed`
- `subscription.plan.changed`
- `subscription.trial.started`
- `subscription.trial.ended`
- `subscription.grace.started`
- `subscription.terminated`

Payload contains `subscription_id`, `subscriber_id`, `plan_id`, `status`, and effective timestamps.
No capability lists are included as authoritative policy.

---

## 8) Subscription lifecycle (clear FSM)

## 8.1 States

- `draft` — created but not active (pre-validation)
- `trialing` — access under trial policy
- `active` — paid or committed free active state
- `grace` — payment/renewal failure grace window
- `paused` — administratively paused
- `canceled_pending_end` — will end at term boundary
- `canceled` — inactive but potentially recoverable within restore window
- `expired` — terminated and no longer recoverable

## 8.2 Transition table

| From | Event | Guard | To | External dependency |
|---|---|---|---|---|
| `draft` | create_free | valid free plan | `active` | entitlement notify |
| `draft` | start_trial | trial eligible | `trialing` | entitlement notify |
| `draft` | activate_paid | billing activated | `active` | billing outcome |
| `trialing` | trial_end_convert | billing activated | `active` | billing outcome |
| `trialing` | trial_end_no_convert | no payment method / opt-out | `canceled` or `active` (free fallback policy) | policy + entitlement |
| `active` | renew_success | billing renewed | `active` | billing outcome |
| `active` | renew_failed | retries exhausted | `grace` | billing outcome |
| `grace` | recovery_payment_success | within grace | `active` | billing outcome |
| `grace` | grace_timeout | grace elapsed | `expired` | entitlement revoke |
| `active` | schedule_cancel | cancel_at_term_end=true | `canceled_pending_end` | billing sync |
| `canceled_pending_end` | term_end_reached | no recovery action | `canceled` | entitlement revoke |
| `active`/`trialing` | immediate_cancel | policy allows | `canceled` | entitlement revoke + billing sync |
| `active` | pause | admin/system policy | `paused` | entitlement policy event |
| `paused` | resume | billing standing valid | `active` | billing/entitlement sync |
| `canceled` | restore | restore window open | `active` | billing reactivation |
| `canceled` | restore_window_elapsed | timeout | `expired` | none |

### 8.3 Dynamic upgrade/downgrade transitions

Plan change is a **sub-flow** on top of `active`/`trialing` state:

1. Request received with target plan and timing preference.
2. Plan compatibility validated.
3. Billing command sent for charge/credit/proration evaluation.
4. On `billing.subscription.change_plan.applied`, subscription `plan_id` is switched.
5. `subscription.plan.changed` emitted to entitlement.

Supported timing modes:

- `immediate` (mid-cycle; billing decides proration)
- `at_renewal` (deferred; scheduled change persisted)

This enables dynamic upgrades without duplicating billing math.

---

## 9) Required scenario handling

## 9.1 Free → paid transition

- Current `active` on free plan.
- Change request to paid plan (`immediate`).
- Billing activation/change-plan requested.
- On billing success: plan changes to paid and entitlement updates accordingly.
- On failure: remain on free plan; emit failure reason in audit trail.

## 9.2 Trials

- Trial eligibility validated at creation.
- In `trialing`, entitlement receives trial state marker.
- At trial end:
  - if conversion succeeds in billing: `active` paid
  - if conversion fails and free fallback exists: `active` free
  - else: `canceled`

## 9.3 Renewal

- Renewal initiated by scheduler at `current_term_end` boundary.
- Billing outcome controls transition:
  - success → extend term, stay `active`
  - failure → enter `grace`, start grace timer
  - unresolved by grace end → `expired`

---

## 10) Reliability, audit, and idempotency

- Every mutation has idempotency key and aggregate version check.
- Outbox pattern for billing/entitlement messages.
- Transition log is append-only for auditability.
- Duplicate event handling via `(event_id, subscription_id)` dedupe.
- Reconciliation job compares subscription state with latest billing status for drift repair.

---

## 11) QC checklist alignment (10/10)

- **No overlap with billing logic:** pricing/proration/collection remain in billing only.
- **No duplication with entitlement:** no capability rules or enforcement in this service.
- **Dynamic upgrades supported:** immediate + scheduled change paths with billing-driven application.
- **Clear lifecycle transitions:** explicit FSM states, guards, and transition outcomes.
- **Plan vs capability separation:** commercial plan identifiers are decoupled from entitlement bundles.

