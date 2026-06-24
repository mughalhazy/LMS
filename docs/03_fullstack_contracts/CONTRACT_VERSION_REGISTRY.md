# CONTRACT_VERSION_REGISTRY

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Registry of all versioned contracts across the fullstack system. Tracks the current version of each contract, its authoritative document, and whether it is in sync across backend and frontend.

---

## API Version Status

| Contract | Current Version | Backend | Frontend | Status |
|---|---|---|---|---|
| API base path | v1 (`/api/v1/`) | Implemented | Pending verification | UNKNOWN |
| Response header `X-API-Version` | `v1` | All services set this | Pending verification | UNKNOWN |
| Auth service base | v2 (`/api/v2/auth`) | Implemented | Pending verification | UNKNOWN |
| Path compat (v2→v1 rewrite) | — | enrollment-service only | N/A | PARTIAL |

---

## Event Envelope Version

| Contract | Version | Authority Doc | Status |
|---|---|---|---|
| Canonical event envelope | v1 | `docs/anchors/event-envelope.md` | ACTIVE (PROTECTED) |
| Event topic format | `lms.<domain>.<event>.v1` | `infrastructure/event-bus/event_topics.json` | ACTIVE |

All 39 event topics are at version `v1`. No v2 topics exist. Topic versioning is embedded in the topic name (suffix `.v1`).

---

## Service Contract Versions

### Auth Contracts

| Contract | Version | Source | Backend Implemented |
|---|---|---|---|
| Login request/response | v2 | auth-service-spec.md §4.1 | Yes |
| Refresh token | v2 | auth-service-spec.md §4.2 | Yes |
| Session validation | v2 | auth-service-spec.md | Yes |
| JWKS endpoint | RFC 7517 (JWK Set) | `/.well-known/jwks.json` | Yes |
| Password policy | — | auth-service main.py §CAT-006 | Yes |
| SSO (SAML/OIDC) | — | auth-service-spec.md §8 | Yes |
| Admin password reset | — | auth-service-spec.md §2.1 | Yes |

### RBAC Contracts

| Contract | Version | Source | Backend Implemented |
|---|---|---|---|
| Role lifecycle | v1 | rbac-service-spec.md | Yes |
| Permission model | v1 | rbac-service-spec.md | Yes |
| Authorize / Batch authorize | v1 | rbac-service-spec.md | Yes |
| Policy rules | v1 | rbac-service-spec.md | Yes |
| Audit log | v1 | rbac-service-spec.md | Yes |

### Tenant Contracts

| Contract | Version | Source | Backend Implemented |
|---|---|---|---|
| Tenant creation + lifecycle | v1 | tenant-service-spec.md | Yes |
| Configuration management | v1 | tenant-service-spec.md | Yes |
| Feature flag management | v1 | tenant-service-spec.md | Yes |
| Isolation evaluation | v1 | tenant-service-spec.md | Yes |

### Enrollment Contracts

| Contract | Version | Source | Backend Implemented |
|---|---|---|---|
| Enrollment CRUD | v1 | enrollment-service-spec.md | Yes |
| Status transitions | v1 | enrollment-service-spec.md | Yes |
| Bulk assignment | v1 | enrollment-service-spec.md | Yes |
| Audit log | v1 | enrollment-service-spec.md | Yes |

### Progress Contracts

| Contract | Version | Source | Backend Implemented |
|---|---|---|---|
| Lesson progress upsert/complete | v1 | progress-service-spec.md | Yes |
| Learner summary | v1 | progress-service-spec.md | Yes |
| Certificate eligibility | v1 | progress-service-spec.md | Yes |
| Learning path assignment | v1 | progress-service-spec.md | Yes |

### Checkout / Commerce Contracts

| Contract | Version | Source | Backend Implemented |
|---|---|---|---|
| Checkout session lifecycle | v1 | (checkout-service source) | Yes |
| Order management | v1 | (checkout-service source) | Yes |
| Payment initiation | v1 | (checkout-service source) | Yes |
| Payment provider adapter | v1 | `docs/contracts/payment-provider-adapter-contract.md` | Yes (JazzCash, EasyPaisa) |

---

## Interface Contract Documents

Located in `docs/contracts/`:

| Contract File | Version | Status |
|---|---|---|
| `capability-interface-contract.md` | v1 | ACTIVE |
| `config-resolution-interface-contract.md` | v1 | ACTIVE |
| `offline-sync-interface-contract.md` | v1 | ACTIVE |
| `capability-gating-model.md` | v1 | ACTIVE |
| `communication-adapter-contract.md` | v1 | ACTIVE |
| `entitlement-interface-contract.md` | v1 | ACTIVE |
| `media-security-interface-contract.md` | v1 | ACTIVE |
| `payment-provider-adapter-contract.md` | v1 | ACTIVE |
| `storage-adapter-interface-contract.md` | v1 | ACTIVE |
| `usage-metering-interface-contract.md` | v1 | ACTIVE |
| `content-storage-model.md` | v1 | ACTIVE |

---

## Anchor Documents (PROTECTED)

These documents are the highest-authority contracts. They must not be changed without owner approval.

| Anchor | Current Version | Status | Known Issue |
|---|---|---|---|
| `docs/anchors/tenant-contract.md` | v1 (6-field) | ACTIVE | None noted |
| `docs/anchors/event-envelope.md` | v1 (7-field) | ACTIVE | None noted |
| `docs/anchors/capability-resolution.md` | v1 | ACTIVE | May reference outdated config levels (OWN-005) |
| `docs/anchors/doc-precedence.md` | v1 | ACTIVE | May reference obsolete BATCH model (OWN-006) |

---

## Data Schema Docs

Located in `docs/data/` (13 files — not fully inspected):
- TBD: Data schema version tracking pending Data Authority Capture phase

---

## Breaking Change Protocol

Any change that modifies a versioned contract must follow this protocol per governance:

1. Check if the contract is a protected anchor (`docs/anchors/`) → REQUIRES_APPROVAL
2. Check if it is an event topic (`event_topics.json`) → REQUIRES_APPROVAL
3. Check if it changes an API route path or response schema → REQUIRES_APPROVAL
4. Check if it changes `service-manifest.json` → REQUIRES_APPROVAL
5. If the change is backwards-compatible only (new optional field) → AUTONOMOUS documentation update
6. If breaking: create a versioned successor (v2 path, new contract doc, new ADR)

Do NOT change contract versions without an ADR in `docs/06_decisions/`.

---

## Contract Sync Status (Backend vs Frontend)

| Contract Area | Backend | Frontend | Sync Status |
|---|---|---|---|
| Auth headers | Verified | Pending | UNKNOWN |
| Tenant isolation | Verified | Pending | UNKNOWN |
| RBAC authorization | Verified | Pending | UNKNOWN |
| Error handling | Verified | Pending | UNKNOWN |
| Pagination | Verified (stub total) | Pending | UNKNOWN |
| Event envelope | Verified (in-memory) | N/A | N/A |
| Password policy | Verified | Pending | UNKNOWN |

Frontend Authority Capture required to complete sync status verification.

---

## Related Documents

- `docs/anchors/` — canonical protected contracts
- `docs/contracts/` — 11 interface contracts
- `docs/specs/` — per-service engineering specs (73 files)
- `docs/03_fullstack_contracts/VALIDATION_PARITY.md` — validation alignment
- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` — auth versioning
