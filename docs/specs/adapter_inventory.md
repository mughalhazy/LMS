# Adapter Inventory

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §4

---

## Purpose

Catalogue all required external adapters per Master Spec §4. All external dependencies must use adapters. Adapters live in `/integrations/`. Core services never depend on provider logic.

---

## Required Adapters (per Master Spec §4)

| Adapter type | Status | Canonical path | Interface contract | Implementations |
|---|---|---|---|---|
| Payment | IMPLEMENTED | `integrations/payments/` (canonical) | `docs/architecture/payment_provider_adapter_interface_contract.md` | `easypaisa_adapter.py`, `jazzcash_adapter.py`, `raast_adapter.py`, `stripe_adapter.py`, `paypal_adapter.py` |
| Communication | IMPLEMENTED | `integrations/communication/` | `docs/architecture/communication_adapter_interface_contract.md` | `email_adapter.py`, `sms_adapter.py`, `whatsapp_adapter.py` |
| Storage | IMPLEMENTED | `integrations/storage/` | `docs/architecture/storage_adapter_interface_contract.md` | `s3_adapter.py` (S3/S3-compatible), `local_adapter.py` (local/dev) |
| Third-party integrations | PARTIAL | `services/integration-service/` | `docs/api/integration_api.md` | HRIS sync, LTI, webhooks |

---

## Payment Adapters (IMPLEMENTED)

**Canonical path:** `integrations/payments/` (DF-04 RESOLVED 2026-04-11 — plural is canonical)
**Deprecated path:** `integrations/payment/` — deprecated with backward-compat exports only; do not add new adapters here
**Interface contract:** `docs/architecture/payment_provider_adapter_interface_contract.md`
**QC validation:** `docs/qc/B7P05_payment_adapter_validation_report.md` — PASS 10/10

| File | Provider | Market | Notes |
|---|---|---|---|
| `base_adapter.py` | — | All | Abstract base — all adapters extend this |
| `easypaisa_adapter.py` | Easypaisa | PK | Market-specific adapter — correct adapter pattern |
| `jazzcash_adapter.py` | JazzCash | PK | Market-specific adapter — correct adapter pattern |
| `raast_adapter.py` | Raast | PK | Market-specific adapter |
| `stripe_adapter.py` | Stripe | International | International adapter |
| `paypal_adapter.py` | PayPal | International | International adapter |
| `router.py` | — | All | Routes to correct adapter by `tenant.country_code` |

---

## Communication Adapters (IMPLEMENTED)

**Canonical path:** `integrations/communication/`
**Interface contract:** `docs/architecture/communication_adapter_interface_contract.md`
**QC validation:** `docs/qc/B7P06_communication_workflow_validation_report.md` — PASS 10/10

| File | Channel | Notes |
|---|---|---|
| `base_adapter.py` | — | Abstract base |
| `email_adapter.py` | Email | Standard SMTP/transactional email |
| `sms_adapter.py` | SMS | Country-agnostic SMS gateway |
| `whatsapp_adapter.py` | WhatsApp | Supports §5.9 Interaction Layer delivery |

---

## Storage Adapter (IMPLEMENTED — MO-022, Phase B, 2026-04-14)

**Status:** Implemented.
**MS§4 violation resolved:** `integrations/storage/` built and registered.
**Canonical path:** `integrations/storage/`
**Interface contract:** `docs/architecture/storage_adapter_interface_contract.md`

| File | Role |
|---|---|
| `base_adapter.py` | `BaseStorageAdapter` Protocol — 6-method contract |
| `s3_adapter.py` | S3StorageAdapter — AWS S3 / MinIO / Wasabi / Cloudflare R2 / DigitalOcean Spaces |
| `local_adapter.py` | LocalStorageAdapter — local filesystem (dev / offline LMS-in-a-box) |
| `router.py` | StorageRouter — content_category → bucket routing; per-tenant adapter selection |
| `__init__.py` | Package exports |

**Canonical buckets (per file_storage_design.md):**

| Content category | Bucket |
|---|---|
| `video` | `lms-video-store` |
| `document` | `lms-document-store` |
| `scorm` | `lms-scorm-store` |
| `image` | `lms-image-store` |

**Primary consumers:**
- `services/file-storage/service.py` — content upload/download lifecycle
- `services/media-pipeline/service.py` — processed asset storage

---

## Third-Party Integration Adapters (PARTIAL)

**Path:** `services/integration-service/`
**Spec:** `docs/specs/integration_service_spec.md`
**Integration API:** `docs/api/integration_api.md`

| Integration | Status | Spec ref |
|---|---|---|
| HRIS sync | IMPLEMENTED | `docs/integrations/hris_sync_spec.md` |
| LTI consumer | IMPLEMENTED | `docs/integrations/lti_consumer_spec.md` |
| LTI provider | IMPLEMENTED | `docs/integrations/lti_provider_spec.md` |
| Webhooks | IMPLEMENTED | `docs/integrations/webhook_system_spec.md` |
| SCORM runtime | IMPLEMENTED | `docs/specs/scorm_runtime_spec.md` |
| xAPI | IMPLEMENTED | `docs/integrations/standards_support.md` |

---

---

## Architectural Contract: MS-ADAPTER-01 — Adapter Isolation (MS§4)

**Contract name:** MS-ADAPTER-01
**Source authority:** Master Spec §4
**Enforcement scope:** Applies to ALL services. No service is exempt.

**Rule — four sub-rules, all mandatory:**

1. **All external dependencies MUST use adapters.** A service may not call an external provider SDK, API, or library directly from its business logic. Every external dependency must be accessed via an adapter that implements a stable, provider-agnostic interface.

2. **All adapters MUST live in `/integrations/`.** Provider-specific code lives in `integrations/<category>/`. No adapter logic may reside inside `services/`, `shared/`, or any other layer.

3. **Core services MUST NEVER contain provider logic.** A core service must be unaware of which provider is selected. Provider selection is the router's concern. Provider-specific payloads, error codes, and retry strategies are the adapter's concern.

4. **Adapters MUST be swappable without core changes.** Adding, replacing, or removing a provider adapter must require zero changes to any service outside `/integrations/`. The adapter interface (contract) is the boundary.

**Canonical adapter paths:**

| Category | Canonical path | Interface contract |
|---|---|---|
| Payment | `integrations/payments/` | `docs/architecture/payment_provider_adapter_interface_contract.md` |
| Communication | `integrations/communication/` | `docs/architecture/communication_adapter_interface_contract.md` |
| Storage | `integrations/storage/` (PLANNED) | `docs/architecture/storage_adapter_interface_contract.md` (to be created) |

**What a violation looks like:**
- A service file containing `import jazzcash_sdk` or a direct HTTP call to a payment provider.
- A payment or communication adapter placed in `services/` or `shared/`.
- A service with an `if provider == "stripe":` conditional in its business logic.
- An adapter change that requires modifying a service's business logic.

**Why this rule exists:** MS§4 requires a complete adapter layer as the isolation boundary between core platform logic and all external dependencies. Without named enforcement, provider logic drifts into services, making providers non-swappable and the platform non-portable.

---

## References

- Master Spec §4
- `docs/anchors/country_layer_architecture.md` — adapter binding by country
- `doc_catalogue.md` Section 15 — Integrations code layer
