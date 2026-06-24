# Badge Service — Spec

**Service:** `badge-service` | **Gateway:** `/api/v1/badge` | **Port:** varies

## Purpose

Manages badge definitions and badge issuances. Supports the full badge lifecycle from definition authoring through issuance to revocation, with learner badge history.

## Responsibilities

- Badge definition CRUD (create, patch, archive)
- Badge issuance to learners (issue, revoke, reinstate)
- Learner badge history with badge metadata joined

## Out of scope

- Certificate issuance (owned by `certificate-service`)
- Completion rule evaluation — caller is responsible for determining eligibility before issuing

## Data model

| Entity | Fields |
|---|---|
| `BadgeDefinition` | badge_id, tenant_id, code, title, description, criteria{}, image_url, metadata{}, status, created_at, updated_at |
| `BadgeIssuance` | issuance_id, tenant_id, badge_id, learner_id, issued_by, evidence{}, issued_at, status, revoked_at, revoke_reason, created_at, updated_at |

## Status values

- `BadgeDefinition.status`: `active` | `archived`
- `BadgeIssuance.status`: `issued` | `revoked`

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/badge/definitions` | Create badge definition |
| PATCH | `/api/v1/badge/definitions/{badgeId}` | Update definition (code field is immutable) |
| GET | `/api/v1/badge/definitions` | List definitions for tenant |
| POST | `/api/v1/badge/issuances` | Issue badge to learner |
| PATCH | `/api/v1/badge/issuances/{issuanceId}` | Revoke or reinstate issuance |
| GET | `/api/v1/badge/learners/{learnerId}/history` | Learner badge history with badge metadata |

## Behavioral rules

- `code` field is immutable after creation — patch attempts rejected with 400
- Badge code must be unique per tenant (case-insensitive)
- Badge must be `active` to issue — archived badges reject new issuances with 400
- A learner can only have one active issuance per badge — duplicate issue attempt returns 409
- Revocation records revoked_at timestamp and reason
- Learner history sorted by issued_at descending

## Integration

- Consumed by: `certificate-service` (cross-reference), operator dashboards
- Emits: no events currently
