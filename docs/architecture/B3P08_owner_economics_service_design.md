# B3P08 — Owner Economics Service Design

**Type:** Architecture design (BATCH) | **Date:** 2026-04-04 | **MS§:** §5.14 | **Priority:** Priority 1 (BATCH B3*)

---

## Purpose

Design the owner/instructor economics service — the sub-domain within commerce that manages how platform participants (academy owners, instructors, tutors, content creators) earn from and track their revenue participation.

---

## Scope and Non-Goals

### In scope
- Revenue participation model (how earnings are calculated per participant)
- Earnings ledger (append-only record of all earning events per participant)
- Payout calculation (gross earnings → deductions → net payout)
- Earnings dashboard data (read model for participant earnings visibility)

### Out of scope
- Invoice and billing SoR (owned by `B3P04`)
- Platform-level revenue analytics (owned by `B3P06`)
- Payment execution / bank transfers (owned by payment adapters)
- Tax computation beyond platform fee deduction (external service)

---

## Service Design

### Module 1: `EarningsLedger`
- Append-only record of all revenue-participation events per participant
- Event types: enrollment_revenue_share, session_fee, content_royalty, referral_credit
- Keys: participant_id, period, source_event_id
- Deduplication enforced by source_event_id
- Shared model: `shared/models/owner_economics.py`

### Module 2: `RevenueParticipationEngine`
- Calculates each participant's share of revenue from a given transaction
- Participation rules: percentage split, fixed fee, tiered by volume
- Rules are config-driven — stored in config service by capability key
- No hardcoded revenue split ratios

### Module 3: `PayoutCalculator`
- Aggregates earnings over a payout period
- Applies deductions: platform commission, processing fees, tax withholding
- Produces: gross earnings, deduction breakdown, net payout amount
- Payout schedule: configurable (weekly/monthly/on-demand) via config service

### Module 4: `TeacherEconomicsView`
- Read model for teacher/tutor economics (distinct participant type from owners)
- Shared model: `shared/models/teacher_economics.py`
- Inputs from: session delivery, learning path completion, tutor rating events

---

## Integration

- Consumes: payment_confirmed events from commerce, session_completed events from learning
- Produces: earnings_credited events, payout_calculated events
- Read by: operations-os (participant dashboards), analytics-service (system economics)
- Payout execution: routes to payment adapter (not owned by this service)

---

## Data Model

Key entities (from `shared/models/owner_economics.py`, `shared/models/teacher_economics.py`):
- `EarningsEntry` — single earning event record
- `ParticipantLedger` — aggregated ledger per participant per period
- `PayoutRecord` — calculated payout with deduction breakdown

---

## References

- Master Spec §5.14
- `docs/specs/economic_capabilities_user_spec.md`
- `docs/architecture/B3P06_revenue_service_design.md` (system revenue — complement)
- `services/commerce/owner_economics.py` (implementation)
- `services/commerce/test_owner_economics.py`
- `validation/tests/test_exam_economics_validation.py`
