# INTEGRATION_CATALOG

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Documents all external integration adapters and partner integrations as found in the repository. Derived from code inspection of `integrations/`, `backend/integrations/`, and service source.

---

## Protected Integration Areas

The following integration directories are in PROTECTED_AREAS and must not be modified without explicit owner approval:

| Directory | Status | Reason |
|---|---|---|
| `integrations/payments/` | PROTECTED | Production-confirmed (.pyc files present), JazzCash + EasyPaisa live |
| `integrations/communication/` | PROTECTED | Notification delivery infrastructure |

---

## Payment Integrations

### Location: `integrations/payments/`

**Status**: Production-confirmed. `.pyc` files present — this code is actively executed.

| Provider | Description | Country |
|---|---|---|
| JazzCash | Mobile wallet payment provider | Pakistan |
| EasyPaisa | Mobile wallet payment provider | Pakistan |

These are Pakistan-first payment providers. Any change to JazzCash/EasyPaisa adapter logic requires explicit owner approval (REQUIRES_APPROVAL per governance).

### Related Service

`payment-service` (port 8162, `api:app`) — the HTTP service that integrates payment adapters. Uses non-standard `api:app` entrypoint (not `app.main:app`).

### Payment Contract

Interface defined in `docs/contracts/payment-provider-adapter-contract.md`.

Provider-agnostic adapter interface supports:
- `create` — initiate payment intent/authorization/capture
- `verify` — check payment state with provider
- `refund` — execute refund via provider

Commerce payment statuses (normalized across providers):
`pending`, `requires_action`, `authorized`, `captured`, `failed`, `cancelled`

### Payment Type Coverage

| Payment Method | Type |
|---|---|
| Mobile wallet (JazzCash, EasyPaisa) | `wallet` / `local_method` |
| Card | `card` |
| Bank transfer | `bank_transfer` |
| UPI | `upi` |
| Other | `other` |

---

## Communication Integrations

### Location: `integrations/communication/`

**Status**: PROTECTED. Notification delivery adapters for email, SMS, push.

Interface defined in `docs/contracts/communication-adapter-contract.md`.

Services that use communication adapters:
- `notification-service` (8122)
- `email-service` (8112)
- `push-service` (8126)

---

## Backend Integrations

### Location: `backend/integrations/`

**Status**: NEEDS-REVIEW. Relationship to root `integrations/` unconfirmed (OWN-003).

Contents not fully inventoried. This may be active service-to-adapter bridge code or duplicate integration implementations. Owner classification required before use.

---

## LTI Integration

### Service: `lti-service` (port 8120)

LTI 1.3 integration for connecting external learning tools. Spec: `docs/specs/` (integration-service-spec.md references this).

---

## HRIS Integration

### Service: `hris-sync-service` (port 8116)

HRIS data synchronization — syncs HR system data (users, departments, org structure) into the platform. Spec: `docs/specs/features/hris-sync-service-spec.md`.

---

## SCORM Integration

### Service: `scorm-service` (port 8131, Node.js)

SCORM runtime for SCORM content packages. Node.js implementation (`npm run start`). One of two Node.js services.

Spec: `docs/specs/features/scorm-runtime-spec.md`.

---

## Webhook Integration

### Service: `webhook-service` (port 8137)

Outbound webhook delivery for platform events. Allows external systems to subscribe to platform events.

---

## SSO Integration

### Service: `sso-service` (port 8134)

SAML/OIDC Single Sign-On. auth-service handles SSO initiation and callback endpoints:
- `POST /api/v2/auth/sso/initiate` — pre-auth flow
- `POST /api/v2/auth/sso/callback` — assertion exchange

Spec: `docs/specs/sso-spec.md`.

---

## API Key Integration

### Service: `api-key-service` (port 8101)

Programmatic API key management for machine-to-machine integrations. Spec: `docs/specs/api-key-service-spec.md`.

---

## Integration Service (Generic)

### Service: `integration-service` (port 8154)

Generic integration management service. Spec: `docs/specs/integration-service-spec.md`, `docs/specs/adapter-inventory.md`.

---

## Storage Adapter Contract

Interface defined in `docs/contracts/storage-adapter-interface-contract.md`.

Content storage model: `docs/contracts/content-storage-model.md`.

---

## Media Security Integration

### Service: `media-security-service` (port 8157)

Signed URL generation and media access control. Spec: `docs/specs/media-security-spec.md`. Contract: `docs/contracts/media-security-interface-contract.md`.

---

## Offline Sync Integration

### Service: `offline-sync-service` (port 8158)

Enables offline-capable content consumption and synchronization. Spec: `docs/specs/offline-sync-spec.md`. Contract: `docs/contracts/offline-sync-interface-contract.md`.

---

## Duplicate Directory Finding

| Directory | Files | Status |
|---|---|---|
| `integrations/payment/` | 8 files | NEEDS-REVIEW — overlaps with `integrations/payments/` |
| `integrations/payments/` | 26 files | PROTECTED — production-confirmed |

Resolution requires owner decision (OWN-004). Both directories may coexist during migration.

---

## Integration Contracts in `docs/contracts/`

| Contract | Description |
|---|---|
| `capability-interface-contract.md` | Capability evaluation interface |
| `config-resolution-interface-contract.md` | Config resolution protocol |
| `offline-sync-interface-contract.md` | Offline sync adapter |
| `capability-gating-model.md` | Capability gating logic |
| `communication-adapter-contract.md` | Communication adapter interface |
| `entitlement-interface-contract.md` | Entitlement evaluation interface |
| `media-security-interface-contract.md` | Media security interface |
| `payment-provider-adapter-contract.md` | Payment provider adapter |
| `storage-adapter-interface-contract.md` | Storage adapter interface |
| `usage-metering-interface-contract.md` | Usage metering interface |
| `content-storage-model.md` | Content storage model |

---

## Related Documents

- `docs/contracts/payment-provider-adapter-contract.md` — payment adapter contract
- `docs/contracts/communication-adapter-contract.md` — communication adapter contract
- `docs/01_backend/SERVICE_CATALOG.md` — full service list
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — integration risk items
