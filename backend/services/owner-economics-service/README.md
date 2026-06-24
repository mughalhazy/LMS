# owner-economics-service

Owner and instructor economics — earnings ledger, payout calculation with deductions, teacher/tutor economics view. Design: `docs/designs/owner-economics-service-design.md` (B3P08) and `docs/specs/economic-capabilities-user-spec.md`.

## Shared models

- `backend/shared/models/owner_economics.py` — `OwnerEarningsEntry`, `OwnerLedger`, `PayoutRecord` (B15-008)
- `backend/shared/models/teacher_economics.py` — `TeacherEarningsEntry`, `TeacherLedger` (B15-008)

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/owner-economics/earnings` | Record owner earning |
| GET | `/api/v1/owner-economics/participants/{id}/ledger` | Get earnings ledger for period |
| GET | `/api/v1/owner-economics/participants/{id}/payouts` | List payouts |
| POST | `/api/v1/owner-economics/payouts/calculate` | Calculate payout with config-service deductions |
| POST | `/api/v1/teacher-economics/sessions` | Record tutor session earning (B15-007) |
| GET | `/api/v1/teacher-economics/tutors/{id}/ledger` | Get teacher ledger (B15-007) |
| GET | `/health` | Health check |

## B15 fixes (2026-06-02)

- **B15-007**: `TeacherEconomicsView` added — distinct from owner economics; driven by session delivery + tutor rating events; rating-based multiplier on earnings
- **B15-008**: `shared/models/owner_economics.py` + `shared/models/teacher_economics.py` created at canonical paths
- **B15-009**: Payout deductions (processing fee, tax withholding) now fetched from config-service; falls back to hardcoded defaults if config unavailable

## Gateway

Route: `/api/v1/owner-economics`, `/api/v1/teacher-economics` | Rate limit: `public-api-standard`
