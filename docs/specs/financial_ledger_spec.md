# Financial Ledger Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.3 | **Service:** `services/system-of-record/`

---

## Capability Domain: §5.3 Financial Capabilities

Covers: student ledger | payment tracking | revenue allocation

---

## Scope

This spec defines the student-facing financial ledger capability. It is distinct from the platform billing/invoice SoR (owned by `services/commerce/`) — that covers tenant-to-platform billing. This spec covers the student-to-academy financial relationship.

---

## Capabilities Defined

### CAP-STUDENT-LEDGER
- Per-student financial record tracking fee obligations, payments, balances, and credit notes
- Inputs: enrollment fee schedules, payment events from commerce adapters
- Outputs: balance state, payment history, clearance status
- Owner: `services/system-of-record/`
- Shared model: `shared/models/ledger.py`

### CAP-PAYMENT-TRACKING
- Real-time payment event capture and reconciliation against fee obligations
- Inputs: payment adapter callbacks, invoice state from commerce
- Outputs: payment confirmation, outstanding balance, overdue flags
- Owner: `services/commerce/` (payment events) + SoR (ledger state)

### CAP-REVENUE-ALLOCATION
- Allocation of received payments to course/instructor/academy revenue buckets
- Inputs: payment events, pricing rules from commerce
- Outputs: revenue allocation records per entity
- Owner: `services/commerce/owner_economics.py`
- Shared model: `shared/models/owner_economics.py`

---

## Boundary Rules

- Student ledger is READ-ONLY from the operations layer (academy-ops reads clearance status)
- Only the SoR service writes authoritative ledger entries
- Payment adapters emit events; they never write to the ledger directly
- Commerce domain owns invoice SoR; SoR service owns student-balance SoR

---

## Data Model

Key entities (from `shared/models/ledger.py`):
- `LedgerEntry` — append-only financial event record
- `StudentBalance` — current balance projection from ledger entries
- `FeeObligation` — expected payment schedule per enrollment

---

## Integration

- Consumes: payment events from `integrations/payment/router.py`
- Produces: `student.ledger.payment_received`, `student.ledger.balance_updated`
- Read by: `services/academy-ops/` (fee tracking), `services/operations-os/` (dashboard)

---

## References

- Master Spec §5.3
- `docs/architecture/SOR_01_system_of_record_design.md`
- `docs/architecture/B3P04_invoice_billing_service_design.md`
- `services/system-of-record/service.py`
