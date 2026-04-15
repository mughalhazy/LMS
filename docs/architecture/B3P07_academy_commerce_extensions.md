# B3P07 — Academy Commerce Extensions

## 1) Purpose

Define an **academy monetization extension layer** that sits on top of the core commerce domain (`B3P01`) and adds academy-specific behavior without duplicating core commerce services.

This extension layer covers:
- Course monetization flows
- Student payment experience and settlement context
- Enrollment-based pricing
- Promotions

It must support:
- Small academies (single brand, lean operations)
- Large coaching networks (multi-campus, franchise, regional operations)

It must integrate with:
- Communication workflows (future), via event contracts and orchestration hooks.

---

## 2) Guardrails (QC FIX RE QC 10/10)

1. **Extension-only model (no core duplication)**
   - Extension layer can orchestrate, enrich, and configure.
   - Extension layer cannot re-implement catalog, pricing engine, checkout core, invoice core, or subscription billing core.

2. **Clear boundary with core commerce**
   - Core commerce remains source of truth for orders, invoices, subscriptions, and price computation.
   - Academy extension contributes academy-specific inputs (cohort, intake, seat policy, scholarship metadata, guardian payer context).

3. **Provider-neutral payments**
   - No hardcoded payment providers or processor-specific workflows.
   - Use abstract `payment_method_type`, `payment_rail_capability`, and adapter capability flags.

4. **Pakistan-specific readiness without regional lock-in**
   - Support PKR pricing, installment plans, bank transfer references, mobile wallet class, and guardian-assisted payments.
   - Implement as configurable regional policies, not Pakistan-only code paths.

5. **Future communication integration**
   - Emit communication-ready events for nudges, reminders, and receipts.
   - No direct coupling to communication channels (SMS/WhatsApp/email) in this layer.

---

## 3) Core vs Extension Responsibility Split

| Area | Core Commerce (existing) | Academy Commerce Extension (new) |
|---|---|---|
| Product/SKU definition | Owns product, plan, bundle, add-on models | Maps academic constructs (course run, batch, campus seat-pack) into sellable compositions |
| Pricing calculation | Owns deterministic quote/rating | Adds enrollment context: seat demand tier, intake window, scholarship tag, installment eligibility |
| Checkout/order | Owns cart/order lifecycle | Adds student + guardian payer journey, deferred enrollment hold states |
| Invoice lifecycle | Owns draft/finalize/adjust/settle | Adds academic term-level installment schedule templates and institution remittance views |
| Promotions engine | Owns discount policy execution | Adds academy campaign semantics (early-bird, merit scholarship, referral cohort campaigns) |
| Payment integration | Consumes payment adapter contract | Chooses allowed payment rails by tenant/region policy, never calls providers directly |

**Boundary rule:** if logic can apply to non-academy commerce universally, keep it in core; if logic depends on academic enrollment semantics, keep it in extension.

---

## 4) Extension Layer Components

## 4.1 Enrollment Offer Composer

Creates academy-specific commercial offers before checkout:
- Converts `course_id + cohort_id + campus_id + intake_window` into commerce quote context.
- Attaches seat policy metadata:
  - `seat_mode`: open, waitlist, reserved
  - `seat_hold_ttl`
  - `max_students_per_offer`
- Adds student profile qualifiers:
  - `grade_band`, `exam_track`, `language_track`

Outputs:
- `academy.offer.composed` event
- Quote-context payload to core pricing

---

## 4.2 Student Payment Orchestration Extension

Manages academy-specific payer flows while delegating transaction execution to payment adapters.

Capabilities:
- Student-self pay, guardian pay, sponsor pay.
- Full pay or installment commitment.
- Payment proof/reference capture for offline-assisted rails (for reconciliation, not processor execution).
- Asynchronous enrollment confirmation when payment status arrives.

Key extension states:
- `payment_intent_pending`
- `payment_reference_submitted`
- `awaiting_settlement_confirmation`
- `enrollment_provisionally_reserved`

---

## 4.3 Enrollment-Based Pricing Context Adapter

Supplies pricing inputs tied to enrollment economics:
- Cohort occupancy tiers (for demand-based tiering)
- Intake calendar windows (early, regular, late)
- Seat type (live seat vs recorded-only)
- Campus/region context (for localized tax/fee overlays)

Important:
- Adapter provides **input attributes only**.
- Final monetary computation stays in core pricing module.

---

## 4.4 Promotion Scenario Registry (Academy)

Defines academy campaign semantics mapped onto core promotions:
- Early-bird admission
- Sibling/household concession
- Merit scholarship percentage/amount
- Referral credit
- Bundle-by-track campaign (e.g., STEM path pack)

Rules:
- Academy extension stores campaign qualification metadata and evidence requirements.
- Core promotion engine applies the discount mechanics.

---

## 4.5 Regional Policy Pack (Pakistan + Global)

Configurable policy pack attached by `country_code` and tenant profile.

Pakistan-oriented defaults (examples, configurable):
- `currency`: PKR
- `installment_policy`: monthly / bi-monthly options
- `settlement_reference_required`: true for bank-transfer-class rails
- `guardian_consent_required_under_age`: true
- `receipt_fields`: includes NTN/STRN where institution requires tax documentation
- `mobile_wallet_class_enabled`: true (provider-neutral class, not vendor-specific)

This pack is overrideable per tenant and reusable for other countries.

---

## 5) Data Contracts (Extension-Owned)

## 5.1 AcademyCheckoutContext

```json
{
  "tenant_id": "uuid",
  "student_id": "uuid",
  "guardian_id": "uuid|null",
  "course_id": "string",
  "cohort_id": "string",
  "campus_id": "string|null",
  "country_code": "PK",
  "currency_code": "PKR",
  "enrollment_window": "early|regular|late",
  "seat_mode": "open|waitlist|reserved",
  "seat_hold_ttl_seconds": 900,
  "pricing_context_tags": ["merit_candidate", "evening_batch"],
  "promotion_context": {
    "campaign_ids": ["early_bird_2026", "referral_q2"],
    "scholarship_profile": "merit_20"
  },
  "payment_preferences": {
    "allowed_method_types": ["card", "bank_transfer", "mobile_wallet_class"],
    "installment_preference": "monthly"
  }
}
```

## 5.2 PaymentRailPolicy (Provider-Neutral)

```json
{
  "tenant_id": "uuid",
  "country_code": "PK",
  "allowed_method_types": ["card", "bank_transfer", "mobile_wallet_class"],
  "capabilities": {
    "supports_async_confirmation": true,
    "supports_reference_submission": true,
    "supports_partial_installment_capture": true
  }
}
```

---

## 6) Flow Examples

## Flow A — Small Academy: Early-Bird Single Course Purchase

1. Admin publishes a new batch with early-bird window and seat cap.
2. Enrollment Offer Composer emits offer context for that batch.
3. Student enters checkout; extension attaches `enrollment_window=early` and `seat_mode=reserved`.
4. Core pricing computes final quote using extension context.
5. Promotion Scenario Registry maps `early_bird_2026` to core promotion eligibility.
6. Student pays through an allowed method type.
7. Core order/invoice finalization completes.
8. Extension emits `academy.enrollment.payment_confirmed` and `academy.enrollment.activated`.

Communication-ready events emitted:
- `academy.payment.reminder.scheduled`
- `academy.receipt.ready`
- `academy.welcome.sequence.requested`

---

## Flow B — Large Coaching Network: Guardian Installments Across Multi-Campus Offering

1. Parent/guardian selects a 3-course exam-prep track spanning two campuses.
2. Extension composes consolidated academy checkout context with campus and cohort tags.
3. Pricing Context Adapter sends tier + intake + track signals to core pricing.
4. Core promotions apply network campaign + merit concession (if qualified).
5. Student Payment Orchestration sets installment plan template (e.g., 4 milestones).
6. Payment adapters process each installment asynchronously.
7. Extension keeps enrollment in `provisionally_reserved` until first settlement confirmation.
8. On each successful settlement event, extension updates installment schedule status and emits communication hooks for reminder/receipt.

Network-scale considerations:
- Supports centralized finance office view per campus and master network tenant.
- Supports different policy packs per region while sharing one core commerce stack.

---

## Flow C — Pakistan-Assisted Bank Transfer with Reference Submission

1. Student selects bank-transfer-class payment rail.
2. Extension checks `settlement_reference_required=true` from policy pack.
3. Student uploads transfer reference ID / slip metadata.
4. Extension emits `academy.payment.reference.submitted` for reconciliation workflow.
5. Core invoice remains in pending settlement state until adapter confirms.
6. On confirmation, extension activates enrollment and triggers receipt/welcome hooks.

No provider name is embedded; all interactions remain capability-based.

---

## 7) Scalability Profiles

## 7.1 Small Academies
- Simple templates: one campus, limited promotion catalog, monthly installment optional.
- Turnkey default policy pack with minimal required fields.
- Low-ops mode: auto-generated reminder schedules.

## 7.2 Large Coaching Networks
- Multi-entity structure: network tenant + campus sub-tenants.
- Rule layering: global campaign + campus override.
- High-volume event processing: async payment confirmations and large enrollment peaks.
- Finance segmentation: campus-level remittance and centralized reconciliation summaries.

---

## 8) Integration with Future Communication Workflows

The extension emits domain events only; communication service consumes and decides channel strategy.

Suggested events:
- `academy.payment.intent_created`
- `academy.payment.reminder_due`
- `academy.installment.overdue`
- `academy.receipt.generated`
- `academy.enrollment.state_changed`
- `academy.promotion.eligibility_confirmed`

Event payload standards:
- Must include `tenant_id`, `student_id`, `enrollment_id`, `locale`, `country_code`.
- Must exclude payment instrument secrets.
- Must include idempotency key for downstream communication dedupe.

---

## 9) Anti-Duplication Checklist

Before implementing any academy monetization feature, verify:

- Does it recompute prices already owned by core pricing? → If yes, reject.
- Does it create invoice state transitions owned by core invoice engine? → If yes, reject.
- Does it embed provider-specific API fields? → If yes, reject.
- Does it rely on hardcoded country logic instead of regional policy packs? → If yes, reject.
- Does it expose communication-channel logic in commerce extension? → If yes, move to communication domain.

---

## 10) Implementation Starter Backlog (Extension Layer Only)

1. Build `academy_checkout_context` contract and validator.
2. Implement `enrollment_offer_composer` with seat/integration metadata.
3. Implement promotion scenario mapping registry.
4. Implement regional policy pack resolver (`country_code + tenant overrides`).
5. Add academy extension events and schemas for communication integration.
6. Add audit trails for scholarship/referral qualification evidence.

This backlog intentionally excludes core commerce service rework and payment provider SDK integration.
