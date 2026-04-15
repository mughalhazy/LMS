# DOC_NORM_02 — Market Enforcements → Capability Map

**Type:** Normalisation cross-reference | **Date:** 2026-04-04 | **MS§:** §7

---

## Purpose

Map each of the 7 market enforcement requirements from Master Spec §7 to their implementing capability domain, service owner, and spec reference. Confirms these are implemented as capabilities — not as country or segment logic.

---

## Map

### 1. Mobile-first usage

| Attribute | Value |
|---|---|
| Capability domain | §5.12 Offline Capabilities + §5.13 Performance Capabilities |
| Implementation | Progressive offline sync, lightweight API responses, mobile-optimised content delivery |
| Service owner | `services/offline-sync/`, `services/media-security/` |
| Spec ref | `docs/specs/offline_sync_spec.md`, `docs/architecture/offline_sync_interface_contract.md` |
| Not implemented as | Country-specific mobile feature — it is a platform-wide capability |

---

### 2. Low-tech operators

| Attribute | Value |
|---|---|
| Capability domain | §5.17 Onboarding Capabilities + §5.7 Communication Capabilities |
| Implementation | Instant setup with minimal config, SMS/WhatsApp delivery for low-bandwidth operators |
| Service owner | `services/onboarding/`, `services/notification-service/` |
| Spec ref | `docs/specs/onboarding_spec.md`, `docs/specs/notification_service_spec.md` |
| Not implemented as | Segment-specific simplification — it is a configurable capability |

---

### 3. Asynchronous interaction

| Attribute | Value |
|---|---|
| Capability domain | §5.9 Interaction Layer + §5.7 Communication Capabilities |
| Implementation | Action-based replies, WhatsApp adapter, async notification orchestration |
| Service owner | `services/notification-service/`, `integrations/communication/whatsapp_adapter.py` |
| Spec ref | `docs/specs/interaction_layer_spec.md` (BUILT — DF-03 resolved 2026-04-11), `docs/specs/notification_service_spec.md` |
| Status | BUILT — interaction service implemented (CGAP-025, T3-D); WhatsApp adapter implemented |

---

### 4. Unreliable connectivity

| Attribute | Value |
|---|---|
| Capability domain | §5.12 Offline Capabilities |
| Implementation | Offline content access, local storage, idempotent sync engine, conflict resolution |
| Service owner | `services/offline-sync/` |
| Spec ref | `docs/specs/offline_sync_spec.md`, `docs/architecture/offline_sync_interface_contract.md` |
| Not implemented as | Country-specific fallback — it is a platform capability enabled per tenant |

---

### 5. Instant payment activation

| Attribute | Value |
|---|---|
| Capability domain | §5.4 Commerce Capabilities + §5.5 Monetization Capabilities |
| Implementation | Checkout → entitlement activation pipeline; payment adapters for local providers |
| Service owner | `services/commerce/`, `integrations/payment/` |
| Spec ref | `docs/architecture/B3P03_checkout_service_design.md`, `docs/architecture/payment_provider_adapter_interface_contract.md` |
| Not implemented as | Country-hardcoded — adapters (easypaisa, jazzcash) implement local providers without embedding logic in core |

---

### 6. Content protection

| Attribute | Value |
|---|---|
| Capability domain | §5.11 Content Protection Capabilities |
| Implementation | Tokenised playback, watermarking, session controls, anti-piracy enforcement |
| Service owner | `services/media-security/` |
| Spec ref | `docs/specs/media_security_spec.md`, `docs/architecture/media_security_interface_contract.md` |
| Not implemented as | Country-specific DRM — it is a platform-wide entitlement-gated capability |

---

### 7. Operational automation

| Attribute | Value |
|---|---|
| Capability domain | §5.8 Workflow Capabilities + §5.10 Admin Operations Capabilities |
| Implementation | Event-driven automation, rule engine, multi-step workflows, operational dashboards |
| Service owner | `services/workflow-engine/`, `services/operations-os/` |
| Spec ref | `docs/specs/workflow_engine_spec.md`, `docs/specs/operations_os_spec.md` |
| Not implemented as | Manual-process replacement — it is a general automation capability |

---

---

## Architectural Contract: MS-MARKET-01 — Market Enforcements as Capabilities (MS§7)

**Contract name:** MS-MARKET-01
**Source authority:** Master Spec §7
**Scope:** The 7 market enforcement requirements mapped in this document.

**Rule:** The 7 market requirements listed in this document are non-negotiable platform obligations. Each MUST be fully satisfiable via capability activation alone.

**Three sub-rules, all mandatory:**

1. **No country-specific fork permitted.** None of the 7 market requirements may be delivered through a country-specific code branch, country-specific service deployment, or country-specific data schema. A requirement delivered only for one country is a platform defect.

2. **Capability activation is the only delivery mechanism.** Each requirement must be satisfiable by enabling the corresponding capability for a tenant — no additional configuration, code, or deployment beyond capability activation should be required.

3. **Geography must not gate capability availability.** No capability implementing a market requirement may be restricted by `country_code` or `segment_type` at the entitlement layer. The entitlement system may use these as config discriminators (per MS-CONFIG-01), but not as denial conditions for market-enforcement capabilities.

**Market requirement → capability status:**

| MS§7 requirement | Implementing capability | Delivery mechanism | Country-fork? |
|---|---|---|---|
| Mobile-first usage | §5.12 Offline + §5.13 Performance | Capability activation | ✗ NEVER |
| Low-tech operators | §5.17 Onboarding + §5.7 Communication | Capability activation | ✗ NEVER |
| Async interaction | §5.9 Interaction Layer + §5.7 Communication | Capability activation | ✗ NEVER |
| Unreliable connectivity | §5.12 Offline Capabilities | Capability activation | ✗ NEVER |
| Instant payment activation | §5.4 Commerce + §5.5 Monetization | Adapter substitution + capability activation | ✗ NEVER |
| Content protection | §5.11 Content Protection | Capability activation | ✗ NEVER |
| Operational automation | §5.8 Workflow + §5.10 Admin Ops | Capability activation | ✗ NEVER |

**Why this rule exists:** MS§7 lists these requirements as market realities that must be part of the platform — not optional country builds. Without a named contract, individual requirements can drift toward country-specific implementations, which breaks global portability and forces code changes to enter a new market.

---

## References

- Master Spec §7
- `docs/anchors/capability_resolution.md`
- `doc_catalogue.md` (quick domain lookup)
