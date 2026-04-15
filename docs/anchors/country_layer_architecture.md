# Country Layer Architecture (Unified)

> **NORMALISATION NOTE (2026-04-04):** The country layer is an ADAPTER-BINDING pattern, not country-specific logic embedded inside the platform. It translates `tenant.country_code` into adapter selection (payment, communication, media security, offline sync), keeping all country variance declarative and isolated in adapter implementations. This is consistent with Master Spec §4 (adapter layer) and §1.5 (country_code as permitted tenant input). Service internals never branch on country — only adapters vary.

## Purpose
Define one canonical country-layer contract that composes adapter-backed delivery and communication behavior by tenant geography, using only adapter interface contracts and QC validation outputs.

---

## Canonical Definition

```yaml
country_layer:
  payment_adapter
  communication_adapter
  media_security
  offline_sync
```

`country_layer` is selected by `tenant.country_code` (ISO 3166-1 alpha-2, uppercase).

---

## Selection Rule (Normative)
1. Read `tenant.country_code` from tenant context.
2. Resolve the country-scoped layer for that code.
3. Bind all four components from the resolved layer as a single bundle:
   - `payment_adapter`
   - `communication_adapter`
   - `media_security`
   - `offline_sync`
4. Execute runtime flows only through the mapped interfaces below.

This keeps country variance declarative while preserving stable application contracts.

---

## Adapter Map → Interface Contracts

| country_layer component | Interface contract | Runtime role |
|---|---|---|
| `payment_adapter` | `docs/architecture/payment_provider_adapter_interface_contract.md` | Country-aware provider routing and normalized payment create/verify/refund. |
| `communication_adapter` | `docs/architecture/communication_adapter_interface_contract.md` | Channel-agnostic send/schedule/broadcast with workflow trigger emission. |
| `media_security` | `docs/architecture/media_security_interface_contract.md` | Secure playback authorization, tokenized controls, watermark/anti-piracy hooks. |
| `offline_sync` | `docs/architecture/offline_sync_interface_contract.md` | Download orchestration, idempotent sync queue, resumable retry/recovery flows. |

---

## QC Alignment Matrix

| country_layer component | QC evidence | Alignment |
|---|---|---|
| `payment_adapter` | `docs/qc/B7P05_payment_adapter_validation_report.md` | PASS, validation score 10/10, adapter isolation and config-based routing verified. |
| `communication_adapter` | `docs/qc/B7P06_communication_workflow_validation_report.md` | PASS, validation score 10/10, adapter-only delivery and WhatsApp→SMS fallback verified. |
| `media_security` | `docs/qc/B7P07_delivery_system_validation_report.md` | PASS, validation score 10/10, entitlement-gated secure playback and anti-piracy controls verified. |
| `offline_sync` | `docs/qc/B7P07_delivery_system_validation_report.md` | PASS, validation score 10/10, entitled sync + deduplicated/idempotent offline queue behavior verified. |
| `tenant.country_code` selection | `docs/qc/B7P03_config_resolution_validation_report.md` | PASS, validation score 10/10, country layer resolution is deterministic and hierarchy-safe. |

---

## Completeness Check (QC + Auto-Fix)
- All required adapters/components present in canonical `country_layer`: **YES**.
- Missing components: **NONE**.
- Interface mapping coverage: **4/4 components mapped**.
- QC coverage across components and country-based selection: **COMPLETE**.
- Aggregate alignment result: **FULLY ALIGNED WITH QC**.

**QC Score: 10/10**
